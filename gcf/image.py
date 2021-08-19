import struct
from functools import reduce
from enum import IntFlag
from typing import Iterable
from . import ResourceDescriptor, Resource, SupercompressionScheme, Header, ResourceType
from .compress import COMPRESSOR_TABLE
from .vulkan import Format, FORMAT_SIZE_TABLE


class ImageFlags(IntFlag):
    Image1D = 0x0001
    Image2D = 0x0003
    Image3D = 0x0007


class MipLevelDescriptor:
    FORMAT = '=6IQ'
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(
        self,
        compressed_size: int,
        uncompressed_size: int,
        row_stride: int,
        depth_stride: int,
        layer_stride: int
    ):
        self.compressed_size = compressed_size
        self.uncompressed_size = uncompressed_size
        self.row_stride = row_stride
        self.depth_stride = depth_stride
        self.layer_stride = layer_stride

    def serialize(self) -> bytes:
        return struct.pack(
            self.FORMAT,
            self.compressed_size,
            self.uncompressed_size,
            self.row_stride,
            self.depth_stride,
            self.layer_stride,
            0, 0
        )

    @classmethod
    def from_bytes(cls, raw: bytes):
        fields = struct.unpack(cls.FORMAT, raw)
        compressed_size = fields[0]
        uncompressed_size = fields[1]
        row_stride = fields[2]
        depth_stride = fields[3]
        layer_stride = fields[4]

        return cls(
            compressed_size,
            uncompressed_size,
            row_stride,
            depth_stride,
            layer_stride
        )

    @classmethod
    def from_file(cls, f):
        raw_data = f.read(cls.FORMAT_SIZE)

        return cls.from_bytes(raw_data)


class MipLevel:
    def __init__(self, descriptor: MipLevelDescriptor, level_data: bytes):
        '''Create a new mip level from compressed raw data.

        ARGUMENTS:
            descriptor - The mip level descriptor
            level_data - The compressed data, as described in the descriptor
        '''
        self.descriptor = descriptor
        self.data = level_data

    def serialize(self) -> bytes:
        return self.descriptor.serialize() + self.data

    def get_size(self) -> int:
        return self.descriptor.FORMAT_SIZE + len(self.data)

    @classmethod
    def from_image_data(cls, descriptor: 'ImageResourceDescriptor', data):
        '''Create a new mip level from uncompressed image data.

        ARGUMENTS:
            data -  The uncompressed image data as a numpy array with shape [layers, depth, height, width, format_width]
            descriptor -  The image resource descriptor

        RETURN VALUE:
            A new `ImageResource` object.
        '''
        compressor = COMPRESSOR_TABLE[descriptor.supercompression_scheme][0]
        flattened_data = data.flatten().tobytes()
        compressed_data = compressor(flattened_data)
        compressed_data_length = len(compressed_data)
        uncompressed_data_length = len(flattened_data)

        try:
            pixel_size = FORMAT_SIZE_TABLE[format]
        except KeyError as exc:
            raise ValueError(f'Unsupported format {format.name}.') from exc

        row_stride = pixel_size * descriptor.width
        depth_stride = row_stride * descriptor.height
        layer_stride = depth_stride * descriptor.depth

        descriptor = MipLevelDescriptor(
            compressed_data_length,
            uncompressed_data_length,
            row_stride, depth_stride, layer_stride
        )

        return cls(descriptor, compressed_data)


class ImageResourceDescriptor(ResourceDescriptor):
    TYPE_DATA_FORMAT = '=3H2BHQ'
    TYPE_DATA_FORMAT_SIZE = struct.calcsize(TYPE_DATA_FORMAT)

    def __init__(
        self,
        format: Format,
        size: int,
        /,
        header: Header,
        width: int, height: int, depth: int = 1,
        layer_count: int = 1, mip_level_count: int = 1,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NoCompression,
        flags: Iterable[ImageFlags] = 0
    ):
        super().__init__(
            ResourceType.Image,
            format,
            size,
            header=header,
            supercompression_scheme=supercompression_scheme,
            type_data=self.TYPE_DATA_CUSTOM
        )

        self.width = width
        self.height = height
        self.depth = depth
        self.layer_count = layer_count
        self.mip_level_count = mip_level_count
        self.flags = set(flags)

    @property
    def type_data(self) -> bytes:
        raw_flags = reduce(lambda x, y: x | y, self.flags)

        return struct.pack(
            self.TYPE_DATA_FORMAT,
            self.width, self.height, self.depth,
            self.layer_count, self.mip_level_count,
            raw_flags,
            0
        )

    @staticmethod
    def _decode_flags(raw_flags):
        flags = set()

        # The Image[1,2,3]D flags share the same bits; only one should be
        # allowed.
        for f in (ImageFlags.Image3D, ImageFlags.Image2D, ImageFlags.Image1D):
            if raw_flags & f.value == f.value:
                flags.add(f)
                break

        return flags

    @classmethod
    def from_resource_descriptor(cls, descriptor: ResourceDescriptor):
        fields = struct.unpack(cls.TYPE_DATA_FORMAT, descriptor.type_data)
        width, height, depth = fields[0:3]
        layer_count = fields[3]
        mip_level_count = fields[4]
        raw_flags = fields[5]
        flags = cls._decode_flags(raw_flags)

        return cls(
            descriptor.format, descriptor.size,
            width=width, height=height, depth=depth,
            layer_count=layer_count,
            mip_level_count=mip_level_count,
            supercompression_scheme=descriptor.supercompression_scheme,
            flags=flags,
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


class ImageResource(Resource):
    def __init__(self, descriptor: ResourceDescriptor, mip_levels: Iterable[MipLevel]):
        super().__init__(descriptor)

        self.mip_levels = list(mip_levels)

        if not self.mip_levels:
            raise ValueError('Should at least have one mip level.')

    @property
    def content_data(self) -> bytes:
        data = b''

        for mip_level in self.mip_levels:
            data += mip_level.serialize()

        return data
