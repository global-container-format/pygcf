"""
Texture resource serialization.
"""

import struct
from enum import IntFlag
from typing import List, Optional, TypedDict

from .compression import compress, decompress
from .resource import (
    COMMON_DESCRIPTOR_SIZE,
    CommonResourceDescriptor,
    ResourceType,
    deserialize_common_resource_descriptor,
    serialize_common_resource_descriptor,
)

EXTENDED_DESCRIPTOR_FORMAT = "=3H2BHIH"
EXTENDED_DESCRIPTOR_SIZE = struct.calcsize(EXTENDED_DESCRIPTOR_FORMAT)
TOTAL_DESCRIPTOR_SIZE = COMMON_DESCRIPTOR_SIZE + EXTENDED_DESCRIPTOR_SIZE

MIP_LEVEL_FORMAT = "=6I"
MIP_LEVEL_SIZE = struct.calcsize(MIP_LEVEL_FORMAT)


class TextureFlags(IntFlag):
    """Texture flags."""

    TEXTURE_1D = 0x0001
    TEXTURE_2D = 0x0003  # pylint: disable=implicit-flag-alias
    TEXTURE_3D = 0x0007  # pylint: disable=implicit-flag-alias


class TextureResourceDescriptor(CommonResourceDescriptor):
    """A texture extended descriptor object."""

    base_width: int
    base_height: int
    base_depth: int
    layer_count: int
    mip_level_count: int
    flags: TextureFlags
    texture_group: int


class MipLevelDescriptor(TypedDict):
    """A texture mip level descriptor."""

    compressed_size: int
    uncompressed_size: int
    row_stride: int
    slice_stride: int
    layer_stride: int


def make_texture_resource_descriptor(
    *,
    format_: int,
    content_size: int,
    supercompression_scheme: int,
    base_width: int,
    base_height: int = 1,
    base_depth: int = 1,
    layer_count: int = 1,
    mip_level_count: int = 1,
    texture_group: int = 0,
    flags: TextureFlags
) -> TextureResourceDescriptor:
    """Make a texture resource descriptor."""

    return {
        "type": ResourceType.TEXTURE.value,
        "format": format_,
        "content_size": content_size,
        "extension_size": EXTENDED_DESCRIPTOR_SIZE,
        "supercompression_scheme": supercompression_scheme,
        "base_width": base_width,
        "base_height": base_height,
        "base_depth": base_depth,
        "layer_count": layer_count,
        "mip_level_count": mip_level_count,
        "flags": flags,
        "texture_group": texture_group,
    }


def serialize_mip_level_descriptor(descriptor: MipLevelDescriptor) -> bytes:
    """Serialize a mip level descriptor.

    :param descriptor: The descriptor object.

    :returns: A bytes object containing the serialized descriptor.
    """

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
    """Deserialize a mip level descriptor.

    :param raw: A bytes object containing the serialized descriptor.

    :returns: The descriptor object.
    """

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
    """Serialize a texture extended resource descriptor.

    :param descriptor: The descriptor object.

    :returns: A bytes object containing the serialized descriptor.
    """

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
    """Deserialize a texture extended resource descriptor.

    :param raw: A bytes object containing the serialized descriptor.

    :returns: The descriptor object.
    """

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
        "flags": TextureFlags(extended_fields[5]),
        "texture_group": extended_fields[6],
    }


def deserialize_mip_level_data(raw: bytes, descriptor: TextureResourceDescriptor) -> List[bytes]:
    """Deserialize a texture mip level data.

    :param raw: A bytes object containing the serialized data.
    :param descriptor: The texture resource descriptor.

    :returns: A list of bytes objects, each representing the data of a given texture layer.
    """

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


def serialize_mip_level_data(layers: List[bytes], supercompression_scheme: int) -> bytes:
    """Serialize a texture mip level data.

    :param layers: A list of bytes objects, each representing the data of a given texture layer.
    :param supercompression_scheme: The supercompression scheme to use.

    :returns: A bytes object containing the serialized data.
    """
    layer_seq = b"".join(layers)

    return compress(layer_seq, supercompression_scheme)
