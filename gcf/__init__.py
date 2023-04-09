import struct
from enum import Flag, IntEnum, auto, unique
from typing import Iterable

from .vulkan import Format as VkFormat


class ContainerFlags(Flag):
    Unpadded = auto()


@unique
class SupercompressionScheme(IntEnum):
    NoCompression = (0,)
    ZLib = (1,)
    Deflate = (2,)
    Test = 0xFFFF


@unique
class ResourceType(IntEnum):
    Blob = (0,)
    Image = (1,)
    Test = 0xFFFFFFFF


class Header:
    DEFAULT_VERSION = 2
    MAGIC_PREFIX = "GC"
    FORMAT = "=4BHH"
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(
        self,
        resource_count: int,
        flags: Iterable[ContainerFlags] = None,
        version: int = None,
    ):
        self.resource_count = resource_count
        self.version = version or self.DEFAULT_VERSION
        self.flags = set(flags or ())

    @classmethod
    def _make_valid_version(cls, version_number):
        return "{}{:02d}".format(cls.MAGIC_PREFIX, version_number)

    def serialize(self) -> bytes:
        magic = self._make_valid_version(self.version).encode("ascii")
        flags = 0

        for x in self.flags:
            flags |= x.value

        return struct.pack(self.FORMAT, *magic, self.resource_count, flags)

    @classmethod
    def from_bytes(cls, raw: bytes, /, valid_version=DEFAULT_VERSION):
        *magic, resource_count, raw_flags = struct.unpack(cls.FORMAT, raw)

        magic = "".join(map(chr, magic))
        valid_magic = cls._make_valid_version(valid_version)

        if magic != valid_magic:
            raise ValueError(f'Invalid magic "{magic}", should be "{valid_magic}".')

        version = int(magic[2:])
        flags = (x for x in ContainerFlags if x.value & raw_flags)

        return cls(resource_count, flags, version)

    @classmethod
    def from_file(cls, f, /, valid_version=DEFAULT_VERSION):
        raw_header = f.read(cls.FORMAT_SIZE)
        return cls.from_bytes(raw_header, valid_version=valid_version)


class ResourceDescriptor:
    TOTAL_RESOURCE_DESCRIPTOR_SIZE = 32  # Includes the basic resource descriptor + type data
    FORMAT = "=3I2H"
    FORMAT_SIZE = struct.calcsize(FORMAT)
    TYPE_DATA_OFFSET = FORMAT_SIZE
    TYPE_DATA_SIZE = TOTAL_RESOURCE_DESCRIPTOR_SIZE - FORMAT_SIZE
    TYPE_DATA_CUSTOM = object()  # Used to indicate type data is handled by a subclass

    def __init__(
        self,
        resource_type: ResourceType,
        format: VkFormat,
        size: int,
        /,
        header: Header,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NoCompression,
        type_data: bytes = b"\x00" * TYPE_DATA_SIZE,
    ):
        self.resource_type = resource_type
        self.format = format
        self.size = size
        self.supercompression_scheme = supercompression_scheme
        self.header = header

        if type_data is not self.TYPE_DATA_CUSTOM:
            self.type_data = type_data

    def serialize(self):
        return (
            struct.pack(
                self.FORMAT,
                self.resource_type,
                self.format,
                self.size,
                self.supercompression_scheme,
                0,
            )
            + self.type_data
        )

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        fields = struct.unpack(cls.FORMAT, raw[: cls.TYPE_DATA_OFFSET])
        resource_type = ResourceType(fields[0])
        format = VkFormat(fields[1])
        size = fields[2]
        supercompression_scheme = SupercompressionScheme(fields[3])
        type_data = raw[cls.TYPE_DATA_OFFSET :]

        return cls(
            resource_type,
            format,
            size,
            supercompression_scheme=supercompression_scheme,
            type_data=type_data,
            header=header,
        )

    @classmethod
    def from_file(cls, f, header: Header):
        raw_descriptor = f.read(cls.FORMAT_SIZE + cls.TYPE_DATA_SIZE)

        return cls.from_bytes(raw_descriptor, header)


class Resource:
    def __init__(self, descriptor: ResourceDescriptor):
        self.descriptor = descriptor

    @property
    def content_data(self) -> bytes:
        raise RuntimeError("get_content_data() must be overridden.")

    def serialize(self):
        from .util import align_size

        raw_content = self.content_data
        self.descriptor.size = len(raw_content)
        raw_data = self.descriptor.serialize() + raw_content

        if not ContainerFlags.Unpadded in self.descriptor.header.flags:
            raw_data_size = len(raw_data)
            raw_data_size_aligned = align_size(raw_data_size, 8)
            padding_size = raw_data_size_aligned - raw_data_size
        else:
            padding_size = 0

        padding = b"\x00" * padding_size

        return raw_data + padding
