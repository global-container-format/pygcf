import struct

from gcf import blob, ResourceType, SupercompressionScheme
from gcf.resource_format import Format


def test_make_blob_resource_descriptor():
    result = blob.make_blob_resource_descriptor(100, 200, SupercompressionScheme.TEST.value)

    assert result['content_size'] == 100
    assert result['extension_size'] == blob.EXTENDED_DESCRIPTOR_SIZE
    assert result['format'] == Format.UNDEFINED
    assert result['supercompression_scheme'] == SupercompressionScheme.TEST.value
    assert result['type'] == ResourceType.BLOB.value
    assert result['uncompressed_size'] == 200


def test_serialize_deserialize_blob_descriptor():
    expected_descriptor = blob.make_blob_resource_descriptor(100, 200, SupercompressionScheme.TEST.value)
    raw = blob.serialize_blob_descriptor(expected_descriptor)
    actual_descriptor = blob.deserialize_blob_descriptor(raw)

    assert actual_descriptor == expected_descriptor


def test_serialize_blob_descriptor():
    """Test against spec."""

    descriptor = blob.make_blob_resource_descriptor(100, 200, SupercompressionScheme.TEST.value)
    raw = blob.serialize_blob_descriptor(descriptor)

    (
        decoded_type,
        decoded_format,
        decoded_content_size,
        decoded_extension_size,
        decoded_supercompression_scheme,
        decoded_uncompressed_size
    ) = struct.unpack("=3I2HQ", raw)

    assert decoded_content_size == 100
    assert decoded_extension_size == blob.EXTENDED_DESCRIPTOR_SIZE
    assert decoded_format == Format.UNDEFINED
    assert decoded_supercompression_scheme == SupercompressionScheme.TEST.value
    assert decoded_type == ResourceType.BLOB.value
    assert decoded_uncompressed_size == 200
