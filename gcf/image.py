import os
import struct
from enum import IntFlag
from typing import Iterable
from . import ResourceDescriptor, Resource, SupercompressionScheme
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
        self.descriptor = descriptor
        self.data = level_data

    def serialize(self) -> bytes:
        return self.descriptor.serialize() + self.data

    def get_size(self) -> int:
        return self.descriptor.FORMAT_SIZE + len(self.data)

    @classmethod
    def from_image_data(
        cls,
        data, supercompression: SupercompressionScheme, format: Format,
        width: int, height: int, depth: int
    ):
        compressor = COMPRESSOR_TABLE[supercompression][0]
        flattened_data = data.flatten().tobytes()
        compressed_data = compressor(flattened_data)
        compressed_data_length = len(compressed_data)
        uncompressed_data_length = len(flattened_data)

        try:
            pixel_size = FORMAT_SIZE_TABLE[format]
        except KeyError as exc:
            raise ValueError(f'Unsupported format {format.name}.') from exc

        row_stride = pixel_size * width
        depth_stride = row_stride * height
        layer_stride = depth_stride * depth

        descriptor = MipLevelDescriptor(
            compressed_data_length,
            uncompressed_data_length,
            row_stride, depth_stride, layer_stride
        )

        return cls(descriptor, compressed_data)


class ImageResource(Resource):
    def __init__(self, descriptor: ResourceDescriptor, mip_levels: Iterable[MipLevel]):
        super().__init__(descriptor)

        self.mip_levels = list(mip_levels)

        if not self.mip_levels:
            raise ValueError('Should at least have one mip level.')

    def get_content_data(self) -> bytes:
        data = b''

        for mip_level in self.mip_levels:
            data += mip_level.serialize()

        return data


def skip_mip_levels(f, n: int):
    """Skip the given number of mip levels from file."""
    for _ in range(n):
        descriptor = MipLevelDescriptor.from_file(f)
        f.seek(descriptor.compressed_size, os.SEEK_CUR)
