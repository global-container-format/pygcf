import struct
from enum import IntFlag
from typing import List, Optional, TypedDict

from .compression import compress, decompress
from .resource import (
    COMMON_DESCRIPTOR_SIZE,
    CommonResourceDescriptor,
    deserialize_common_resource_descriptor,
    serialize_common_resource_descriptor,
)

EXTENDED_DESCRIPTOR_FORMAT = "=3H2BHIH"
EXTENDED_DESCRIPTOR_SIZE = struct.calcsize(EXTENDED_DESCRIPTOR_FORMAT)
TOTAL_DESCRIPTOR_SIZE = COMMON_DESCRIPTOR_SIZE + EXTENDED_DESCRIPTOR_SIZE

MIP_LEVEL_FORMAT = "=6IQ"
MIP_LEVEL_SIZE = struct.calcsize(MIP_LEVEL_FORMAT)


class TextureFlags(IntFlag):
    """Texture flags."""

    TEXTURE_1D = 0x0001
    TEXTURE_2D = 0x0003  # pylint: disable=implicit-flag-alias
    TEXTURE_3D = 0x0007  # pylint: disable=implicit-flag-alias


class TextureResourceDescriptor(CommonResourceDescriptor):
    base_width: int
    base_height: int
    base_depth: int
    layer_count: int
    mip_level_count: int
    flags: TextureFlags
    texture_group: int


class MipLevelDescriptor(TypedDict):
    compressed_size: int
    uncompressed_size: int
    row_stride: int
    slice_stride: int
    layer_stride: int


def serialize_mip_level_descriptor(descriptor: MipLevelDescriptor) -> bytes:
    return struct.pack(
        MIP_LEVEL_FORMAT,
        descriptor["compressed_size"],
        descriptor["uncompressed_size"],
        descriptor["row_stride"],
        descriptor["slice_stride"],
        descriptor["layer_stride"],
        0,
    )


def deserialize_mip_level_descriptor(raw: bytes) -> MipLevelDescriptor:
    if len(raw) < MIP_LEVEL_SIZE:
        raise ValueError("Invalid mip level data size", len(raw))

    fields = struct.unpack(MIP_LEVEL_FORMAT, raw)

    return {
        "compressed_size": fields[0],
        "uncompressed_size": fields[1],
        "row_stride": fields[2],
        "slice_stride": fields[3],
        "layer_stride": fields[4],
    }


def serialize_texture_resource_descriptor(descriptor: TextureResourceDescriptor) -> bytes:
    common_data = serialize_common_resource_descriptor(descriptor)

    extended_data = struct.pack(
        EXTENDED_DESCRIPTOR_FORMAT,
        descriptor["base_width"],
        descriptor["base_height"],
        descriptor["base_depth"],
        descriptor["layer_count"],
        descriptor["mip_level_count"],
        descriptor["flags"].value,
        descriptor["texture_group"],
        0,
    )

    return common_data + extended_data


def deserialize_texture_resource_descriptor(
    raw: bytes, common_descriptor: Optional[CommonResourceDescriptor] = None
) -> TextureResourceDescriptor:
    if len(raw) < TOTAL_DESCRIPTOR_SIZE:
        raise ValueError("Invalid texture descriptor data size", len(raw))

    common_descriptor = common_descriptor or deserialize_common_resource_descriptor(raw)
    extended_fields = struct.unpack(EXTENDED_DESCRIPTOR_FORMAT, raw[COMMON_DESCRIPTOR_SIZE:TOTAL_DESCRIPTOR_SIZE])

    return {
        **common_descriptor,  # type: ignore
        "base_width": extended_fields[0],
        "base_height": extended_fields[1],
        "base_depth": extended_fields[2],
        "layer_count": extended_fields[3],
        "mip_level_count": extended_fields[4],
        "flags": extended_fields[5],
        "texture_group": extended_fields[6],
    }


def deserialize_mip_level_data(raw: bytes, descriptor: TextureResourceDescriptor) -> List[bytes]:
    supercompression_scheme = descriptor["supercompression_scheme"]
    layer_count = descriptor["layer_count"]
    decompressed_level = decompress(raw, supercompression_scheme)
    total_decompressed_size = len(decompressed_level)
    layer_size = total_decompressed_size // layer_count

    layers = []

    for layer_index in range(layer_count):
        layer_data_begin = layer_size * layer_index
        layer_data_end = layer_data_begin + layer_size

        layers.append(decompressed_level[layer_data_begin:layer_data_end])

    return layers


def serialize_mip_level_data(layers: List[bytes], descriptor: TextureResourceDescriptor) -> bytes:
    supercompression_scheme = descriptor["supercompression_scheme"]
    layer_count = descriptor["layer_count"]

    if not layer_count == len(layers):
        raise ValueError("Layer count doesn't match descriptor metadata.")

    layer_seq = b"".join(layers)

    return compress(layer_seq, supercompression_scheme)
