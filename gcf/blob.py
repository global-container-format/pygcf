"""
Blob resource type serialization.
"""

import struct
from typing import Optional

from .compression import compress, decompress
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
    uncompressed_size: int


def make_blob_resource_descriptor(
    compressed_data: bytes, uncompressed_data_size: int, supercompression_scheme: int
) -> BlobResourceDescriptor:
    return {
        "content_size": len(compressed_data),
        "extension_size": EXTENDED_DESCRIPTOR_SIZE,
        "format": Format.UNDEFINED.value,
        "supercompression_scheme": supercompression_scheme,
        "type": ResourceType.BLOB.value,
        "uncompressed_size": uncompressed_data_size,
    }


def serialize_blob_descriptor(descriptor: BlobResourceDescriptor) -> bytes:
    common_descriptor_data = serialize_common_resource_descriptor(descriptor)
    extended_descriptor_data = struct.pack(EXTENDED_DESCRIPTOR_FORMAT, descriptor["uncompressed_size"])

    return common_descriptor_data + extended_descriptor_data


def deserialize_blob_descriptor(
    raw: bytes, common_descriptor: Optional[CommonResourceDescriptor] = None
) -> BlobResourceDescriptor:
    if len(raw) < TOTAL_DESCRIPTOR_SIZE:
        raise ValueError("Invalid blob descriptor data length", len(raw))

    common_descriptor = common_descriptor or deserialize_common_resource_descriptor(raw)
    extended_fields = struct.unpack(EXTENDED_DESCRIPTOR_FORMAT, raw[COMMON_DESCRIPTOR_SIZE:TOTAL_DESCRIPTOR_SIZE])

    return {
        **common_descriptor,  # type: ignore
        "uncompressed_size": extended_fields[0],
    }


def deserialize_blob_data(raw: bytes, descriptor: BlobResourceDescriptor) -> bytes:
    supercompression_scheme = descriptor["supercompression_scheme"]

    return decompress(raw, supercompression_scheme)


def serialize_blob_data(data: bytes, descriptor: BlobResourceDescriptor) -> bytes:
    supercompression_scheme = descriptor["supercompression_scheme"]

    return compress(data, supercompression_scheme)
