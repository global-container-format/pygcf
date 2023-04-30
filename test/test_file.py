import io
import pytest

from typing import BinaryIO
from gcf import ResourceType, Format, SupercompressionScheme, Header, CommonResourceDescriptor, make_magic_number, file, ContainerFlags
from gcf.file import CompositeResourceDescriptor
from .fixtures import BLOB_RESOURCE_DESCRIPTOR, TEXTURE_RESOURCE_DESCRIPTOR, CUSTOM_RESOURCE_DESCRIPTOR, two_resource_gcf_file


def test_read_write_file():
    magic = make_magic_number()
    expected_header: Header = {
        "flags": ContainerFlags(0),
        "magic": magic,
        "resource_count": 123
    }
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
        "type": ResourceType.TEST.value
    }
    test_file = io.BytesIO()

    file.write_common_resource_descriptor(test_file, expected_descriptor)
    test_file.seek(0)

    actual_descriptor = file.read_common_resource_descriptor(test_file)

    assert actual_descriptor == expected_descriptor


@pytest.mark.parametrize("expected_descriptor", [
    BLOB_RESOURCE_DESCRIPTOR,
    TEXTURE_RESOURCE_DESCRIPTOR,
    CUSTOM_RESOURCE_DESCRIPTOR
])
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
