import struct
from functools import reduce

from gcf import (
    Format,
    MipLevelDescriptor,
    ResourceType,
    SupercompressionScheme,
    TextureFlags,
    deserialize_mip_level_data,
    deserialize_mip_level_descriptor,
    deserialize_texture_resource_descriptor,
    make_texture_resource_descriptor,
    serialize_mip_level_data,
    serialize_mip_level_descriptor,
    serialize_texture_resource_descriptor,
    texture,
)

from .fixtures import TEXTURE_RESOURCE_DESCRIPTOR


def test_serialize_deserialize_texture_descriptor():
    expected_descriptor = TEXTURE_RESOURCE_DESCRIPTOR
    raw = serialize_texture_resource_descriptor(expected_descriptor)
    actual_descriptor = deserialize_texture_resource_descriptor(raw)

    assert actual_descriptor == expected_descriptor


def test_serialize_texture_descriptor():
    """Test against spec."""

    descriptor = TEXTURE_RESOURCE_DESCRIPTOR
    raw = serialize_texture_resource_descriptor(descriptor)

    (
        actual_type,
        actual_format,
        actual_content_size,
        actual_extension_size,
        actual_supercompression_scheme,
        actual_base_width,
        actual_base_height,
        actual_base_depth,
        actual_layer_count,
        actual_mip_level_count,
        actual_flags,
        actual_texture_group,
        actual_rsvd,
    ) = struct.unpack("=3I2H3H2B2HI", raw)

    assert actual_type == descriptor["type"]
    assert actual_format == descriptor["format"]
    assert actual_content_size == descriptor["content_size"]
    assert actual_extension_size == descriptor["extension_size"]
    assert actual_supercompression_scheme == descriptor["supercompression_scheme"]
    assert actual_base_width == descriptor["base_width"]
    assert actual_base_height == descriptor["base_height"]
    assert actual_base_depth == descriptor["base_depth"]
    assert actual_layer_count == descriptor["layer_count"]
    assert actual_mip_level_count == descriptor["mip_level_count"]
    assert actual_flags == descriptor["flags"]
    assert actual_texture_group == descriptor["texture_group"]
    assert actual_rsvd == 0


def test_make_texture_resource_descriptor():
    descriptor = make_texture_resource_descriptor(
        format_=Format.R8G8B8_SINT,
        compressed_content_size=123,
        supercompression_scheme=SupercompressionScheme.ZLIB.value,
        base_width=1,
        base_height=2,
        base_depth=3,
        layer_count=4,
        mip_level_count=5,
        texture_group=66,
        flags=TextureFlags.TEXTURE_3D,
    )

    assert descriptor["type"] == ResourceType.TEXTURE.value
    assert descriptor["format"] == Format.R8G8B8_SINT
    assert descriptor["content_size"] == 123
    assert descriptor["extension_size"] == texture.EXTENDED_DESCRIPTOR_SIZE
    assert descriptor["supercompression_scheme"] == SupercompressionScheme.ZLIB.value
    assert descriptor["base_width"] == 1
    assert descriptor["base_height"] == 2
    assert descriptor["base_depth"] == 3
    assert descriptor["layer_count"] == 4
    assert descriptor["mip_level_count"] == 5
    assert descriptor["texture_group"] == 66
    assert descriptor["flags"] == TextureFlags.TEXTURE_3D


def test_serialize_deserialize_mip_level_descriptor():
    expected_descriptor: MipLevelDescriptor = {
        "compressed_size": 123,
        "uncompressed_size": 345,
        "layer_stride": 5,
        "row_stride": 6,
        "slice_stride": 7,
    }
    raw = serialize_mip_level_descriptor(expected_descriptor)
    actual_descriptor = deserialize_mip_level_descriptor(raw)

    assert actual_descriptor == expected_descriptor


def test_serialize_mip_level_descriptor():
    """Test against spec."""

    descriptor: MipLevelDescriptor = {
        "compressed_size": 123,
        "uncompressed_size": 345,
        "layer_stride": 5,
        "row_stride": 6,
        "slice_stride": 7,
    }
    raw = serialize_mip_level_descriptor(descriptor)

    (
        actual_compressed_size,
        actual_uncompressed_size,
        actual_row_stride,
        actual_slice_stride,
        actual_layer_stride,
        rsvd,
    ) = struct.unpack("=6I", raw)

    assert actual_compressed_size == descriptor["compressed_size"]
    assert actual_uncompressed_size == descriptor["uncompressed_size"]
    assert actual_row_stride == descriptor["row_stride"]
    assert actual_slice_stride == descriptor["slice_stride"]
    assert actual_layer_stride == descriptor["layer_stride"]
    assert rsvd == 0


def test_serialize_deserialize_mip_level_data():
    expected_layers = [b"abcd", b"cdef"]

    descriptor = make_texture_resource_descriptor(
        format_=Format.R8_UINT,
        compressed_content_size=123,
        supercompression_scheme=SupercompressionScheme.DEFLATE.value,
        base_width=4,
        base_height=1,
        base_depth=1,
        layer_count=2,
        mip_level_count=5,
        texture_group=66,
        flags=TextureFlags.TEXTURE_1D,
    )

    raw = serialize_mip_level_data(expected_layers, descriptor)
    actual_layers = deserialize_mip_level_data(raw, descriptor)

    assert actual_layers == expected_layers


def test_serialize_mip_level_data():
    """Test against spec."""

    layers = [b"abcd", b"cdef"]

    descriptor = make_texture_resource_descriptor(
        format_=Format.R8_UINT,
        compressed_content_size=123,
        supercompression_scheme=SupercompressionScheme.NO_COMPRESSION.value,
        base_width=4,
        base_height=1,
        base_depth=1,
        layer_count=2,
        mip_level_count=5,
        texture_group=66,
        flags=TextureFlags.TEXTURE_1D,
    )

    raw = serialize_mip_level_data(layers, descriptor)

    assert len(raw) == reduce(lambda x, layer: x + len(layer), layers, 0)
    assert raw[0] == layers[0][0]
    assert raw[-1] == layers[-1][-1]
