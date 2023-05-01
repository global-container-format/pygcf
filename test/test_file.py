import io
from typing import BinaryIO

import pytest

from gcf import (
    CommonResourceDescriptor,
    ContainerFlags,
    Format,
    Header,
    MipLevelDescriptor,
    ResourceType,
    SupercompressionScheme,
    TextureFlags,
    TextureResourceDescriptor,
    file,
    make_magic_number,
    make_texture_resource_descriptor,
    serialize_mip_level_data,
)
from gcf.file import CompositeResourceDescriptor
from gcf.texture import MIP_LEVEL_SIZE

from .fixtures import (
    BLOB_RESOURCE_DESCRIPTOR,
    CUSTOM_RESOURCE_DESCRIPTOR,
    TEXTURE_RESOURCE_DESCRIPTOR,
    two_resource_gcf_file,
)


def test_read_write_file():
    magic = make_magic_number()
    expected_header: Header = {"flags": ContainerFlags(0), "magic": magic, "resource_count": 123}
    test_file = io.BytesIO()

    file.write_header(test_file, expected_header)
    test_file.seek(0)

    actual_header = file.read_header(test_file)

    assert actual_header == expected_header


def test_read_write_common_resource_descriptor():
    expected_descriptor: CommonResourceDescriptor = {
        "content_size": 1,
        "extension_size": 2,
        "format": Format.R8G8B8_SRGB,
        "supercompression_scheme": SupercompressionScheme.TEST.value,
        "type": ResourceType.TEST.value,
    }
    test_file = io.BytesIO()

    file.write_common_resource_descriptor(test_file, expected_descriptor)
    test_file.seek(0)

    actual_descriptor = file.read_common_resource_descriptor(test_file)

    assert actual_descriptor == expected_descriptor


@pytest.mark.parametrize(
    "expected_descriptor", [BLOB_RESOURCE_DESCRIPTOR, TEXTURE_RESOURCE_DESCRIPTOR, CUSTOM_RESOURCE_DESCRIPTOR]
)
def test_read_write_composite_resource_descriptor(expected_descriptor: CompositeResourceDescriptor):
    test_file = io.BytesIO()

    file.write_composite_resource_descriptor(test_file, expected_descriptor)
    test_file.seek(0)

    actual_descriptor = file.read_composite_descriptor(test_file)

    assert actual_descriptor == expected_descriptor


@pytest.mark.parametrize("padding_enabled", [True, False])
def test_skip_resource(padding_enabled):
    gcf: BinaryIO = two_resource_gcf_file(padding_enabled)
    header = file.read_header(gcf)
    first_common_resource_descriptor = file.read_common_resource_descriptor(gcf)

    file.skip_resource(gcf, first_common_resource_descriptor, header)
    second_common_resource_descriptor = file.read_common_resource_descriptor(gcf)

    assert second_common_resource_descriptor["type"] == ResourceType.TEST.value


def test_read_write_mip_level_descriptor():
    test_file = io.BytesIO()
    expected_descriptor: MipLevelDescriptor = {
        "compressed_size": 123,
        "uncompressed_size": 500,
        "layer_stride": 5,
        "row_stride": 6,
        "slice_stride": 1,
    }

    file.write_mip_level_descriptor(test_file, expected_descriptor)
    test_file.seek(0)

    actual_descriptor = file.read_mip_level_descriptor(test_file)

    assert expected_descriptor == actual_descriptor


def test_read_write_mip_level():
    test_file = io.BytesIO()
    expected_layers = [b"abcd", b"cdef"]
    serialized_layers = serialize_mip_level_data(expected_layers, SupercompressionScheme.DEFLATE.value)

    tex_descriptor = make_texture_resource_descriptor(
        format_=Format.R8_UINT,
        content_size=len(serialized_layers) + MIP_LEVEL_SIZE,
        supercompression_scheme=SupercompressionScheme.DEFLATE.value,
        base_width=4,
        base_height=1,
        base_depth=1,
        layer_count=2,
        mip_level_count=1,
        texture_group=66,
        flags=TextureFlags.TEXTURE_1D,
    )

    level_descriptor: MipLevelDescriptor = {
        "compressed_size": len(serialized_layers),
        "uncompressed_size": 8,
        "layer_stride": 5,
        "row_stride": 6,
        "slice_stride": 7,
    }

    file.write_mip_level(test_file, SupercompressionScheme.DEFLATE.value, level_descriptor, expected_layers)
    test_file.seek(0)
    actual_descriptor, actual_layers = file.read_mip_level(test_file, tex_descriptor)

    assert actual_layers == expected_layers
    assert actual_descriptor == level_descriptor
