import os
import struct
from enum import IntFlag
from functools import reduce
from typing import Iterable, Union

from . import Header, Resource, ResourceDescriptor, ResourceType, SupercompressionScheme
from .compress import COMPRESSOR_TABLE
from .util import compute_mip_level_size
from .vulkan import FORMAT_SIZE_TABLE, Format


class ImageFlags(IntFlag):
    Image1D = 0x0001
    Image2D = 0x0003
    Image3D = 0x0007


class MipLevelDescriptor:
    FORMAT = "=6IQ"
    FORMAT_SIZE = struct.calcsize(FORMAT)

    def __init__(
        self,
        compressed_size: int,
        uncompressed_size: int,
        row_stride: int,
        depth_stride: int,
        layer_stride: int,
    ):
        self.compressed_size = compressed_size
        self.uncompressed_size = uncompressed_size
        self.row_stride = row_stride
        self.depth_stride = depth_stride
        self.layer_stride = layer_stride

    def __eq__(self, o: object) -> bool:
        return (
            self.compressed_size == o.compressed_size
            and self.uncompressed_size == o.uncompressed_size
            and self.row_stride == o.row_stride
            and self.depth_stride == o.depth_stride
            and self.layer_stride == o.layer_stride
        )

    def serialize(self) -> bytes:
        return struct.pack(
            self.FORMAT,
            self.compressed_size,
            self.uncompressed_size,
            self.row_stride,
            self.depth_stride,
            self.layer_stride,
            0,
            0,
        )

    @classmethod
    def from_bytes(cls, raw: bytes):
        fields = struct.unpack(cls.FORMAT, raw[: cls.FORMAT_SIZE])
        compressed_size = fields[0]
        uncompressed_size = fields[1]
        row_stride = fields[2]
        depth_stride = fields[3]
        layer_stride = fields[4]

        return cls(compressed_size, uncompressed_size, row_stride, depth_stride, layer_stride)

    @classmethod
    def from_file(cls, f):
        raw_data = f.read(cls.FORMAT_SIZE)

        return cls.from_bytes(raw_data)


class MipLevel:
    def __init__(self, descriptor: MipLevelDescriptor, level_data: bytes):
        """Create a new mip level from compressed raw data.

        ARGUMENTS:
            descriptor - The mip level descriptor
            level_data - The compressed data, as described in the descriptor
        """
        self.descriptor = descriptor
        self.data = level_data

    def __eq__(self, o: object) -> bool:
        return self.descriptor == o.descriptor and self.data == o.data

    def serialize(self) -> bytes:
        return self.descriptor.serialize() + self.data

    def get_size(self) -> int:
        return self.descriptor.FORMAT_SIZE + len(self.data)

    @classmethod
    def from_bytes(cls, data: bytes):
        """Create a new mip level from a bytes object."""
        descriptor = MipLevelDescriptor.from_bytes(data[: MipLevelDescriptor.FORMAT_SIZE])
        level_data = data[MipLevelDescriptor.FORMAT_SIZE :]

        return cls(descriptor, level_data)

    @classmethod
    def from_file(cls, fileobj):
        """Create a new mip level from file."""
        descriptor = MipLevelDescriptor.from_file(fileobj)
        level_data = fileobj.read(descriptor.compressed_size)

        return cls(descriptor, level_data)

    @classmethod
    def from_image_data(
        cls,
        descriptor: "ImageResourceDescriptor",
        data,
        level: int,
        row_stride: Union[int, None] = None,
        depth_stride: Union[int, None] = None,
        layer_stride: Union[int, None] = None,
    ) -> "MipLevel":  # pylint: disable=too-many-locals, too-many-arguments
        """Create a new mip level from uncompressed image data.

        ARGUMENTS:
            descriptor - The image resource descriptor.
            data -  The uncompressed image data as a numpy array with shape [layers, depth, height, width, format_width].
            level - The mip level expressed by `data`.
            row_stride - The row stride or None to default to the size of a row.
            depth_stride - The depth stride or None to default to the size of one image plane.
            layer_stride - The layer stride or None to default to the size of one image layer.

        RETURN VALUE:
            A new `ImageResource` object.
        """
        compressor = COMPRESSOR_TABLE[descriptor.supercompression_scheme][0]
        flattened_data = data.flatten().tobytes()
        compressed_data = compressor(flattened_data)
        compressed_data_length = len(compressed_data)
        uncompressed_data_length = len(flattened_data)

        try:
            pixel_size = FORMAT_SIZE_TABLE[descriptor.format]
        except KeyError as exc:
            raise ValueError(f"Unsupported format {descriptor.format.name}.") from exc

        mip_level_width, mip_level_height, mip_level_depth = compute_mip_level_size(
            level, descriptor.width, descriptor.height, descriptor.depth
        )

        real_row_stride = row_stride or (pixel_size * mip_level_width)
        real_depth_stride = depth_stride or (real_row_stride * mip_level_height)
        real_layer_stride = layer_stride or (real_depth_stride * mip_level_depth)
        expected_level_size = real_layer_stride * descriptor.layer_count

        if expected_level_size != uncompressed_data_length:
            raise ValueError(
                f"Expected mip level size is {expected_level_size} but data is {uncompressed_data_length} bytes long."
            )

        mip_level_descriptor = MipLevelDescriptor(
            compressed_data_length,
            uncompressed_data_length,
            real_row_stride,
            real_depth_stride,
            real_layer_stride,
        )

        return cls(mip_level_descriptor, compressed_data)


class ImageResourceDescriptor(ResourceDescriptor):
    """Image resource descriptor."""
    TYPE_DATA_FORMAT = "=3H2BHIH"
    TYPE_DATA_FORMAT_SIZE = struct.calcsize(TYPE_DATA_FORMAT)

    def __init__(
        self,
        resource_format: Format,
        size: int,
        /,
        header: Header,
        width: int,
        height: int = 1,
        depth: int = 1,
        layer_count: int = 1,
        mip_level_count: int = 1,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NO_COMPRESSION,
        flags: Iterable[ImageFlags] = (ImageFlags.Image2D,),
    ): # pylint: disable=too-many-arguments
        super().__init__(
            ResourceType.IMAGE,
            resource_format,
            size,
            header=header,
            supercompression_scheme=supercompression_scheme,
            type_data=self.TYPE_DATA_CUSTOM,
        )

        self.flags = set(flags)

        if len(set((ImageFlags.Image1D, ImageFlags.Image2D, ImageFlags.Image3D)) & self.flags) != 1:
            raise ValueError("Image flags must specify exactly once if the image is 1, 2 or 3D.")

        self.width = width
        self.height = height if ImageFlags.Image1D not in self.flags else 1
        self.depth = depth if ImageFlags.Image3D in self.flags else 1
        self.layer_count = layer_count
        self.mip_level_count = mip_level_count

    def __eq__(self, obj: object) -> bool:
        return (
            super().__eq__(obj)
            and self.width == obj.width
            and self.height == obj.height
            and self.depth == obj.depth
            and self.layer_count == obj.layer_count
            and self.mip_level_count == obj.mip_level_count
            and self.flags == obj.flags
        )

    @property
    def type_data(self) -> bytes:
        """Return the resource type information."""
        raw_flags = reduce(lambda x, y: x | y, self.flags)

        return struct.pack(
            self.TYPE_DATA_FORMAT,
            self.width,
            self.height,
            self.depth,
            self.layer_count,
            self.mip_level_count,
            raw_flags,
            0,
            0,
        )

    @staticmethod
    def _decode_flags(raw_flags):
        flags = set()

        # The Image[1,2,3]D flags share the same bits; only one should be
        # allowed.
        for curflag in (ImageFlags.Image3D, ImageFlags.Image2D, ImageFlags.Image1D):
            if raw_flags & curflag.value == curflag.value:
                flags.add(curflag)
                break

        return flags

    @classmethod
    def from_resource_descriptor(cls, descriptor: ResourceDescriptor):
        """Create an image resource from a resource descriptor."""
        fields = struct.unpack(cls.TYPE_DATA_FORMAT, descriptor.type_data)
        width, height, depth = fields[0:3]
        layer_count = fields[3]
        mip_level_count = fields[4]
        raw_flags = fields[5]
        flags = cls._decode_flags(raw_flags)

        return cls(
            descriptor.format,
            descriptor.size,
            width=width,
            height=height,
            depth=depth,
            layer_count=layer_count,
            mip_level_count=mip_level_count,
            supercompression_scheme=descriptor.supercompression_scheme,
            flags=flags,
            header=descriptor.header,
        )

    @classmethod
    def from_file(cls, fileobj, header: Header):
        base_descriptor = ResourceDescriptor.from_file(fileobj, header)

        return cls.from_resource_descriptor(base_descriptor)

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        base_descriptor = ResourceDescriptor.from_bytes(raw, header)

        return cls.from_resource_descriptor(base_descriptor)


class ImageResource(Resource):
    """Image resource."""

    def __init__(self, descriptor: ResourceDescriptor, mip_levels: Iterable[MipLevel]):
        super().__init__(descriptor)

        self.mip_levels = list(mip_levels)

        if not self.mip_levels:
            raise ValueError("Should at least have one mip level.")

    def __eq__(self, obj: object) -> bool:
        return super().__eq__(obj) and self.mip_levels == obj.mip_levels

    @property
    def content_data(self) -> bytes:
        data = b""

        for mip_level in self.mip_levels:
            data += mip_level.serialize()

        return data


def skip_mip_levels(fileobj, num_lines: int):
    """Skip the given number of mip levels from file."""
    for _ in range(num_lines):
        descriptor = MipLevelDescriptor.from_file(fileobj)
        fileobj.seek(descriptor.compressed_size, os.SEEK_CUR)
