"""
Blob resource type serialization.
"""

import struct
from typing import Optional

from .resource import (
    COMMON_DESCRIPTOR_SIZE,
    CommonResourceDescriptor,
    ResourceType,
    deserialize_common_resource_descriptor,
    serialize_common_resource_descriptor,
)
from .resource_format import Format

EXTENDED_DESCRIPTOR_FORMAT = "=Q"
EXTENDED_DESCRIPTOR_SIZE = struct.calcsize(EXTENDED_DESCRIPTOR_FORMAT)
TOTAL_DESCRIPTOR_SIZE = COMMON_DESCRIPTOR_SIZE + EXTENDED_DESCRIPTOR_SIZE


class BlobResourceDescriptor(CommonResourceDescriptor):
    """The resource descriptor for blob resources."""

    uncompressed_size: int


def make_blob_resource_descriptor(
    compressed_data_size: int, uncompressed_data_size: int, supercompression_scheme: int
) -> BlobResourceDescriptor:
    """Create a new blob resource descriptor.

    :param compressed_data_size: The compressed blob data size.
    :param uncompressed_data_size: The size of the data before compression.
    :param supercompression_scheme: The supercompression scheme as passed to gcf.compression.compress().

    :returns: The blob resource descriptor.
    """

    return {
        "content_size": compressed_data_size,
        "extension_size": EXTENDED_DESCRIPTOR_SIZE,
        "format": Format.UNDEFINED.value,
        "supercompression_scheme": supercompression_scheme,
        "type": ResourceType.BLOB.value,
        "uncompressed_size": uncompressed_data_size,
    }


def serialize_blob_descriptor(descriptor: BlobResourceDescriptor) -> bytes:
    """Serialize a blob resource descriptor.

    :param descriptor: The descriptor object.

    :returns: The serialized descriptor.
    """
    common_descriptor_data = serialize_common_resource_descriptor(descriptor)
    extended_descriptor_data = struct.pack(EXTENDED_DESCRIPTOR_FORMAT, descriptor["uncompressed_size"])

    return common_descriptor_data + extended_descriptor_data


def deserialize_blob_descriptor(
    raw: bytes, common_descriptor: Optional[CommonResourceDescriptor] = None
) -> BlobResourceDescriptor:
    """Deserialize a blob resource descriptor.

    This function will not attempt to deserialize the common descriptor a second time
    if this is provided via argument.

    :param raw: The composite descriptor bytes.
    :param common_descriptor: The common_descriptor if already deserialized or None.

    :returns: The blob descriptor.
    """
    if len(raw) < TOTAL_DESCRIPTOR_SIZE:
        raise ValueError("Invalid blob descriptor data length", len(raw))

    common_descriptor = common_descriptor or deserialize_common_resource_descriptor(raw)
    extended_fields = struct.unpack(EXTENDED_DESCRIPTOR_FORMAT, raw[COMMON_DESCRIPTOR_SIZE:TOTAL_DESCRIPTOR_SIZE])

    return {
        **common_descriptor,  # type: ignore
        "uncompressed_size": extended_fields[0],
    }
