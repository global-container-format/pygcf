import struct

from gcf import CommonResourceDescriptor, serialize_common_resource_descriptor, deserialize_common_resource_descriptor, ResourceType, Format, SupercompressionScheme


def test_serialize_deserialize_common_resource_descriptor():
    expected_descriptor: CommonResourceDescriptor = {
        "type": ResourceType.TEST.value,
        "format": Format.TEST,
        "content_size": 123,
        "extension_size": 0,
        "supercompression_scheme": SupercompressionScheme.TEST.value
    }
    raw = serialize_common_resource_descriptor(expected_descriptor)
    actual_descriptor = deserialize_common_resource_descriptor(raw)

    assert expected_descriptor == actual_descriptor


def test_serialize_common_resource_descriptor():
    """Test against spec."""

    descriptor: CommonResourceDescriptor = {
        "type": ResourceType.TEST.value,
        "format": Format.TEST,
        "content_size": 123,
        "extension_size": 0,
        "supercompression_scheme": SupercompressionScheme.TEST.value
    }
    raw = serialize_common_resource_descriptor(descriptor)

    (actual_type, actual_format, actual_content_size, actual_extension_size, actual_supercompression_scheme) = struct.unpack("=3I2H", raw)

    assert actual_type == ResourceType.TEST.value
    assert actual_format == Format.TEST.value
    assert actual_content_size == 123
    assert actual_extension_size == 0
    assert actual_supercompression_scheme == SupercompressionScheme.TEST.value
