
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
    ColorMap = 1


class Header:
    DEFAULT_VERSION = 1
    MAGIC_PREFIX = 'GC'
    FORMAT = '=4BHH'
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(self, resource_count: int, flags: Iterable[ContainerFlags] = None, version: int = None):
        self.resource_count = resource_count
        self.version = version if version is not None else self.DEFAULT_VERSION
        self.flags = set(flags or ())

    def serialize(self) -> bytes:
        magic = '{}{:02d}'.format(self.MAGIC_PREFIX, self.version).encode('ascii')
        flags = 0

        for x in self.flags:
            flags |= x.value

        return struct.pack(self.FORMAT, *magic, self.resource_count, flags)

    @classmethod
    def from_bytes(cls, raw: bytes):
        *magic, resource_count, raw_flags = struct.unpack(cls.FORMAT, raw)

        magic = ''.join(map(chr, magic))

        if magic != 'GC01':
            raise ValueError(f'Invalid magic "{magic}".')

        version = int(magic[2:])
        flags = (x for x in ContainerFlags if x.value & raw_flags)

        return cls(resource_count, flags, version)

    @classmethod
    def from_file(cls, f):
        raw_header = f.read(cls.FORMAT_SIZE)
        return cls.from_bytes(raw_header)


class ResourceDescriptor:
    FORMAT = '=3I4H2BHQ'
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
        self.resource_type = resource_type
        self.format = format
        self.size = size
        self.width = width
        self.height = height
        self.depth = depth
        self.layer_count = layer_count
        self.mip_level_count = mip_level_count
        self.supercompression_scheme = supercompression_scheme
        self.flags = flags
        self.type_data = type_data
        self.header = header

    def serialize(self):
        return struct.pack(
            self.FORMAT,
            self.resource_type, self.format, self.size, self.supercompression_scheme,
            self.width, self.height, self.depth,
            self.layer_count, self.mip_level_count,
            self.flags, self.type_data
        )

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        fields = struct.unpack(cls.FORMAT, raw)
        resource_type = ResourceType(fields[0])
        format = VkFormat(fields[1])
        size = fields[2]
        supercompression_scheme = SupercompressionScheme(fields[3])
        width, height, depth = fields[4:7]
        layer_count = fields[7]
        mip_level_count = fields[8]
        flags = fields[9]
        type_data = fields[10]

        return cls(
            resource_type, format, size,
            width=width, height=height, depth=depth,
            layer_count=layer_count,
            mip_level_count=mip_level_count,
            supercompression_scheme=supercompression_scheme,
            flags=flags,
            type_data=type_data,
            header=header
        )

    @classmethod
    def from_file(cls, f, header: Header):
        raw_descriptor = f.read(cls.FORMAT_SIZE)

        return cls.from_bytes(raw_descriptor, header)


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
