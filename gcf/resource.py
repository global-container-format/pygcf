import struct
from enum import IntEnum, unique
from typing import TypedDict

COMMON_DESCRIPTOR_FORMAT = "=3I2H"
COMMON_DESCRIPTOR_SIZE = struct.calcsize(COMMON_DESCRIPTOR_FORMAT)


@unique
class SupercompressionScheme(IntEnum):
    """Supported standard supercompression schemes."""

    NO_COMPRESSION = 0
    ZLIB = 1
    DEFLATE = 2
    TEST = 0xFFFF


@unique
class ResourceType(IntEnum):
    """Supported standard resource types."""

    BLOB = 0
    TEXTURE = 1
    TEST = 0xFFFFFFFF


class CommonResourceDescriptor(TypedDict):
    type: int
    format: int
    content_size: int
    extension_size: int
    supercompression_scheme: int


def serialize_common_resource_descriptor(descriptor: CommonResourceDescriptor) -> bytes:
    return struct.pack(
        COMMON_DESCRIPTOR_FORMAT,
        descriptor["type"],
        descriptor["format"],
        descriptor["content_size"],
        descriptor["extension_size"],
        descriptor["supercompression_scheme"],
    )


def deserialize_common_resource_descriptor(raw: bytes) -> CommonResourceDescriptor:
    if len(raw) < COMMON_DESCRIPTOR_SIZE:
        raise ValueError("Invalid common resource descriptor data size", len(raw))

    fields = struct.unpack(COMMON_DESCRIPTOR_FORMAT, raw[:COMMON_DESCRIPTOR_SIZE])

    return {
        "type": fields[0],
        "format": fields[1],
        "content_size": fields[2],
        "extension_size": fields[3],
        "supercompression_scheme": fields[4],
    }
