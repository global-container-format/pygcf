"""
Global Container Format reader and writer implementation.
"""

import struct
from enum import Flag, IntEnum, auto, unique
from functools import reduce
from typing import Iterable, Optional

from .resource_format import Format as VkFormat


def _align_size(orig_size: int, alignment: int) -> int:
    assert not alignment & (alignment - 1)  # must be power of 2
    mask = alignment - 1

    return (orig_size + mask) & ~mask


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
    IMAGE = (1,)
    TEST = 0xFFFFFFFF


class Header:
    """A GCF file header."""

    DEFAULT_VERSION = 2
    MAGIC_PREFIX = "GC"
    FORMAT = "=4BHH"
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(
        self,
        resource_count: int,
        flags: Optional[Iterable[ContainerFlags]] = None,
        version: Optional[int] = None,
    ):
        """Create a new header."""
        self.resource_count = resource_count
        self.version = version or self.DEFAULT_VERSION
        self.flags = set(flags or ())

    @classmethod
    def _make_valid_version(cls, version_number: int):
        """Create a new version string from its version number."""
        return f"{cls.MAGIC_PREFIX}{version_number:02d}"

    def serialize(self) -> bytes:
        """Serialize the header."""
        magic = self._make_valid_version(self.version).encode("ascii")
        flags = reduce(lambda result, flag: result | flag.value, self.flags, 0)

        return struct.pack(self.FORMAT, *magic, self.resource_count, flags)

    @classmethod
    def from_bytes(cls, raw: bytes, /, valid_version=DEFAULT_VERSION):
        """Create a new header from a bytes object.

        This function will raise a value error if the the version does not match the
        provided valid version value.
        """
        *raw_magic, resource_count, raw_flags = struct.unpack(cls.FORMAT, raw)

        magic = "".join(map(chr, raw_magic))
        valid_magic = cls._make_valid_version(valid_version)

        if magic != valid_magic:
            raise ValueError(f'Invalid magic "{magic}", should be "{valid_magic}".')

        version = int(magic[2:])
        flags = (x for x in ContainerFlags if x.value & raw_flags)

        return cls(resource_count, flags, version)

    @classmethod
    def from_file(cls, f, /, valid_version=DEFAULT_VERSION):
        """Create a new header from file.

        This function will raise a value error if the the version does not match the
        provided valid version value.
        """
        raw_header = f.read(cls.FORMAT_SIZE)
        return cls.from_bytes(raw_header, valid_version=valid_version)


class ResourceDescriptor:
    """A resource descriptor."""

    TOTAL_RESOURCE_DESCRIPTOR_SIZE = 32  # Includes the basic resource descriptor + type info
    FORMAT = "=3I2H"
    FORMAT_SIZE = struct.calcsize(FORMAT)
    TYPE_INFO_OFFSET = FORMAT_SIZE
    TYPE_INFO_SIZE = TOTAL_RESOURCE_DESCRIPTOR_SIZE - FORMAT_SIZE

    __type_info: bytes

    @property
    def type_info(self) -> bytes:
        """Return the resource type information."""
        return self.__type_info

    def __init__(
        self,
        resource_type: ResourceType,
        resource_format: VkFormat,
        size: int,
        /,
        header: Header,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NO_COMPRESSION,
        type_info: Optional[bytes] = None,
    ):
        """Create a new descriptor."""
        self.resource_type = resource_type
        self.format = resource_format
        self.size = size
        self.supercompression_scheme = supercompression_scheme
        self.header = header
        self.__type_info = type_info or b"\x00" * self.TYPE_INFO_SIZE

    def serialize(self):
        """Serialize the descriptor."""
        return (
            struct.pack(
                self.FORMAT,
                self.resource_type,
                self.format,
                self.size,
                self.supercompression_scheme,
                0,
            )
            + self.type_info
        )

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        """Create a new descriptor from a bytes object."""
        fields = struct.unpack(cls.FORMAT, raw[: cls.TYPE_INFO_OFFSET])
        resource_type = ResourceType(fields[0])
        resource_format = VkFormat(fields[1])
        size = fields[2]
        supercompression_scheme = SupercompressionScheme(fields[3])
        type_info = raw[cls.TYPE_INFO_OFFSET :]

        return cls(
            resource_type,
            resource_format,
            size,
            supercompression_scheme=supercompression_scheme,
            type_info=type_info,
            header=header,
        )

    @classmethod
    def from_file(cls, fileobj, header: Header):
        """Create a new descriptor from file."""

        raw_descriptor = fileobj.read(cls.FORMAT_SIZE + cls.TYPE_INFO_SIZE)

        return cls.from_bytes(raw_descriptor, header)


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

    def serialize(self):
        """Serialize the resource."""
        raw_content = self.content_data
        self.descriptor.size = len(raw_content)
        raw_data = self.descriptor.serialize() + raw_content

        if not ContainerFlags.UNPADDED in self.descriptor.header.flags:
            raw_data_size = len(raw_data)
            raw_data_size_aligned = _align_size(raw_data_size, 8)
            padding_size = raw_data_size_aligned - raw_data_size
        else:
            padding_size = 0

        padding = b"\x00" * padding_size

        return raw_data + padding
