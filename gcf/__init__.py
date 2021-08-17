import os
import struct
from typing import Iterable
from enum import IntEnum, Flag, auto, unique
from .vulkan import Format as VkFormat
from .util import align_size


class ContainerFlags(Flag):
    Unpadded = auto()


@unique
class SupercompressionScheme(IntEnum):
    NoCompression = 0,
    ZLib = 1,
    Deflate = 2,
    Test = 0xffff


@unique
class ResourceType(IntEnum):
    Blob = 0,
    Image = 1,
    Test = 0xffffffff


class Header:
    DEFAULT_VERSION = 2
    MAGIC_PREFIX = 'GC'
    FORMAT = '=4BHH'
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(self, resource_count: int, flags: Iterable[ContainerFlags] = None, version: int = None):
        self.resource_count = resource_count
        self.version = version or self.DEFAULT_VERSION
        self.flags = set(flags or ())

    @classmethod
    def _make_valid_version(cls, version_number):
        return '{}{:02d}'.format(cls.MAGIC_PREFIX, version_number)

    def serialize(self) -> bytes:
        magic = self._make_valid_version(self.version).encode('ascii')
        flags = 0

        for x in self.flags:
            flags |= x.value

        return struct.pack(self.FORMAT, *magic, self.resource_count, flags)

    @classmethod
    def from_bytes(cls, raw: bytes, /, valid_version=DEFAULT_VERSION):
        *magic, resource_count, raw_flags = struct.unpack(cls.FORMAT, raw)

        magic = ''.join(map(chr, magic))
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
    FORMAT = '=3IH'
    FORMAT_SIZE = struct.calcsize(FORMAT)
    TYPE_DATA_OFFSET = 14
    TYPE_DATA_SIZE = 18

    def __init__(
        self,
        resource_type: ResourceType,
        format: VkFormat,
        size: int,
        /,
        header: Header,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NoCompression,
        type_data: bytes = b'\x00' * TYPE_DATA_SIZE
    ):
        self.resource_type = resource_type
        self.format = format
        self.size = size
        self.supercompression_scheme = supercompression_scheme
        self.type_data = type_data
        self.header = header

    def serialize(self):
        return struct.pack(
            self.FORMAT,
            self.resource_type,
            self.format,
            self.size,
            self.supercompression_scheme
        ) + self.type_data

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        fields = struct.unpack(cls.FORMAT, raw[:cls.TYPE_DATA_OFFSET])
        resource_type = ResourceType(fields[0])
        format = VkFormat(fields[1])
        size = fields[2]
        supercompression_scheme = SupercompressionScheme(fields[3])
        type_data = raw[cls.TYPE_DATA_OFFSET:]

        return cls(
            resource_type, format, size,
            supercompression_scheme=supercompression_scheme,
            type_data=type_data,
            header=header
        )

    @classmethod
    def from_file(cls, f, header: Header):
        raw_descriptor = f.read(cls.FORMAT_SIZE + cls.TYPE_DATA_SIZE)

        return cls.from_bytes(raw_descriptor, header)


class ImageResourceDescriptor(ResourceDescriptor):
    FORMAT = '=3H2BHQ'
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(
        self,
        resource_type: ResourceType,
        format: VkFormat,
        size: int,
        /,
        header: Header,
        width: int, height: int, depth: int = 1,
        layer_count: int = 1, mip_level_count: int = 1,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NoCompression,
        flags: int = 0,
        type_data: int = 0
    ):
        super().__init__(
            resource_type,
            format,
            size,
            header=header,
            supercompression_scheme=supercompression_scheme,
            type_data=type_data
        )

        self.width = width
        self.height = height
        self.depth = depth
        self.layer_count = layer_count
        self.mip_level_count = mip_level_count
        self.flags = flags

    def serialize(self):
        resource = super().serialize()
        type_data = struct.pack(
            self.FORMAT,
            self.width, self.height, self.depth,
            self.layer_count, self.mip_level_count,
            self.flags
        )

        resource[self.TYPE_DATA_OFFSET:self.TYPE_DATA_OFFSET + self.TYPE_DATA_SIZE] = type_data

        return resource

    @classmethod
    def from_resource_descriptor(cls, descriptor: ResourceDescriptor):
        fields = struct.unpack(cls.FORMAT, descriptor.type_data)
        width, height, depth = fields[0:3]
        layer_count = fields[3]
        mip_level_count = fields[4]
        flags = fields[5]

        return cls(
            descriptor.resource_type, descriptor.format, descriptor.size,
            width=width, height=height, depth=depth,
            layer_count=layer_count,
            mip_level_count=mip_level_count,
            supercompression_scheme=descriptor.supercompression_scheme,
            flags=flags,
            type_data=descriptor.type_data,
            header=descriptor.header
        )

    @classmethod
    def from_file(cls, f, header: Header):
        base_descriptor = ResourceDescriptor.from_file(f, header)

        return cls.from_resource_descriptor(base_descriptor)

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        base_descriptor = ResourceDescriptor.from_bytes(raw, header)

        return cls.from_resource_descriptor(base_descriptor)


class Resource:
    def __init__(self, descriptor: ResourceDescriptor):
        self.descriptor = descriptor

    def get_content_data(self) -> bytes:
        raise RuntimeError('get_content_data() must be overridden.')

    def serialize(self):
        raw_content = self.get_content_data()
        self.descriptor.size = len(raw_content)
        raw_data = self.descriptor.serialize() + raw_content

        if not ContainerFlags.Unpadded in self.descriptor.header.flags:
            raw_data_size = len(raw_data)
            raw_data_size_aligned = align_size(raw_data_size, 64)
            padding_size = raw_data_size_aligned - raw_data_size
        else:
            padding_size = 0

        padding = b'\x00' * padding_size

        return raw_data + padding


def skip_resources(f, n: int, header: Header):
    """Skip the given number of resources from file."""
    for _ in range(n):
        descriptor = ResourceDescriptor.from_file(f, header)
        f.seek(descriptor.size, os.SEEK_CUR)


def decode_resource_descriptor(descriptor: ResourceDescriptor):
    """Convert a generic resource descriptor into a more specific one depending on the resource type."""
    if descriptor.resource_type == ResourceType.Image:
        return ImageResourceDescriptor.from_resource_descriptor(descriptor)

    return descriptor
