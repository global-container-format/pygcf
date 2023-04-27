"""
Global Container Format reader and writer implementation.
"""

import struct
from enum import Flag, IntEnum, auto, unique
from functools import reduce
from typing import Iterable, Optional, Union, cast, BinaryIO

from .resource_format import Format

_GCF_DEFAULT_VERSION = 3
_GCF_MAGIC_PREFIX = "GC"
_HEADER_FORMAT = "=4BHH"
_HEADER_FORMAT_SIZE = struct.calcsize(_HEADER_FORMAT)

_DESCRIPTOR_FORMAT = "=3I2H"
_COMMON_DESCRIPTOR_SIZE = struct.calcsize(_DESCRIPTOR_FORMAT)


def _align_size(orig_size: int, alignment: int) -> int:
    """Align a size to a boundary."""

    assert not alignment & (alignment - 1)  # must be power of 2
    mask = alignment - 1

    return (orig_size + mask) & ~mask


def _make_valid_version(version_number: int) -> str:
    """Create a new version string from its version number."""

    return f"{_GCF_MAGIC_PREFIX}{version_number:02d}"


def _deserialize_common_descriptor(raw: bytes):
    """Create a new descriptor from a bytes object.

        :param raw: The raw common descriptor data.
        :param header: The GCF header.

        :returns: A new resource descriptor object.
    """
    fields = struct.unpack(_DESCRIPTOR_FORMAT, raw)

    return {
        "resource_type": ResourceType(fields[0]),
        "resource_format": fields[1],
        "content_size": fields[2],
        "extended_descriptor_size": fields[3],
        "supercompression_scheme": SupercompressionScheme(fields[4]),
    }


class ContainerFlags(Flag):
    """Container flags."""

    UNPADDED = auto()


@unique
class SupercompressionScheme(IntEnum):
    """Supported standard supercompression schemes."""

    NO_COMPRESSION = (0,)
    ZLIB = (1,)
    DEFLATE = (2,)
    TEST = 0xFFFF


@unique
class ResourceType(IntEnum):
    """Supported standard resource types."""

    BLOB = (0,)
    TEXTURE = (1,)
    TEST = 0xFFFFFFFF


class Header:
    """A GCF file header."""

    @property
    def is_gcf_file_unpadded(self) -> bool:
        """True if there is no padding between resources."""

        return ContainerFlags.UNPADDED in self.flags

    def __init__(
        self,
        resource_count: int,
        flags: Optional[Iterable[ContainerFlags]] = None,
        version: Optional[int] = None,
    ):
        """Create a new header."""

        self.resource_count = resource_count
        self.version = version or _GCF_DEFAULT_VERSION
        self.flags = set(flags or ())


    def serialize(self) -> bytes:
        """Serialize the header."""

        magic = self._make_valid_version(self.version).encode("ascii")
        flags = reduce(lambda result, flag: result | flag.value, self.flags, 0)

        return struct.pack(_HEADER_FORMAT, *magic, self.resource_count, flags)

    @classmethod
    def from_bytes(cls, raw: bytes, /, valid_version=_GCF_DEFAULT_VERSION):
        """Create a new header from a bytes object.

        This function will raise a value error if the the version does not match the
        provided valid version value.
        """

        *raw_magic, resource_count, raw_flags = struct.unpack(_HEADER_FORMAT, raw)

        magic = "".join(map(chr, raw_magic))
        valid_magic = _make_valid_version(valid_version)

        if magic != valid_magic:
            raise ValueError(f'Invalid magic "{magic}", should be "{valid_magic}".')

        version = int(magic[2:])
        flags = (x for x in ContainerFlags if x.value & raw_flags)

        return cls(resource_count, flags, version)

    @classmethod
    def from_file(cls, f, /, valid_version=_GCF_DEFAULT_VERSION):
        """Create a new header from file.

        This function will raise a value error if the the version does not match the
        provided valid version value.
        """

        raw_header = f.read(_HEADER_FORMAT_SIZE)
        return cls.from_bytes(raw_header, valid_version=valid_version)


class ResourceDescriptor:
    """A resource descriptor."""

    __extended_descriptor: bytes
    format: int
    resource_type: ResourceType
    size: int
    supercompression_scheme: SupercompressionScheme

    @property
    def extended_descriptor(self) -> bytes:
        """Return the resource type information."""

        return self.__extended_descriptor

    @property
    def extended_descriptor_size(self) -> int:
        """Return the size of the extended descriptor, in bytes."""

        return len(self.__extended_descriptor)

    def __init__(
        self,
        resource_type: ResourceType,
        resource_format: Union[Format, int],
        size: int,
        /,
        header: Header,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NO_COMPRESSION,
        extended_descriptor: Optional[bytes] = None,
    ):
        """Create a new descriptor."""

        real_format = resource_format if isinstance(resource_format, int) else cast(Format, resource_format).value

        self.resource_type = resource_type
        self.format = real_format
        self.size = size
        self.supercompression_scheme = supercompression_scheme
        self.header = header
        self.__extended_descriptor = extended_descriptor or b""

    def serialize(self) -> bytes:
        """Serialize the descriptor."""

        return (
            struct.pack(
                _DESCRIPTOR_FORMAT,
                self.resource_type,
                self.format,
                self.size,
                self.extended_descriptor_size,
                self.supercompression_scheme,
            )
            + self.extended_descriptor
        )

    @classmethod
    def from_bytes(cls, raw: bytes, raw_extended: bytes, header: Header) -> "ResourceDescriptor":
        """Create a new descriptor from a bytes object.

            :param raw: The raw common descriptor data.
            :param raw_extended: The raw extended descriptor data.
            :param header: The GCF header.

            :returns: A new resource descriptor object.
        """

        fields = _deserialize_common_descriptor(raw)
        extended_descriptor_size = fields["extended_descriptor_size"]

        if not len(raw_extended) == extended_descriptor_size:
            raise ValueError("Invalid extended descriptor size.", extended_descriptor_size, len(raw_extended))

        return cls(
            **fields,
            extended_descriptor=raw_extended,
            header=header,
        )

    @classmethod
    def from_file(cls, fileobj: BinaryIO, header: Header) -> "ResourceDescriptor":
        """Create a new descriptor from file."""

        raw_descriptor = fileobj.read(_COMMON_DESCRIPTOR_SIZE)
        fields = _deserialize_common_descriptor(raw_descriptor)
        extended_descriptor_size = fields["extended_descriptor_size"]
        extended_descriptor = fileobj.read(extended_descriptor_size)

        return cls(
            **fields,
            extended_descriptor=extended_descriptor,
            header=header,
        )


class Resource:
    """Resource base class."""

    def __init__(self, descriptor: ResourceDescriptor):
        """Create a new resource."""

        self.descriptor = descriptor

    @property
    def content_data(self) -> bytes:
        """Return the resource data.

        This method is meant to be overridden.
        The default implementation raises a not implemented error.
        """

        raise NotImplementedError("content_data() must be overridden.")

    def serialize(self) -> bytes:
        """Serialize the resource."""

        raw_content = self.content_data
        self.descriptor.size = len(raw_content)
        raw_data = self.descriptor.serialize() + raw_content

        if not self.descriptor.header.is_gcf_file_unpadded:
            raw_data_size = len(raw_data)
            raw_data_size_aligned = _align_size(raw_data_size, 8)
            padding_size = raw_data_size_aligned - raw_data_size
        else:
            padding_size = 0

        padding = b"\x00" * padding_size

        return raw_data + padding
