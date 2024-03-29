"""
Common resource descriptor serialization.
"""

import struct
from enum import IntEnum, unique
from typing import TypedDict

COMMON_DESCRIPTOR_FORMAT = "=3I2H"
COMMON_DESCRIPTOR_SIZE = struct.calcsize(COMMON_DESCRIPTOR_FORMAT)


@unique
class ResourceType(IntEnum):
    """Supported standard resource types."""

    BLOB = 0
    TEXTURE = 1
    TEST = 0xFFFFFFFF


class CommonResourceDescriptor(TypedDict):
    """The common portion of a GCF resource descriptor."""

    type: int
    format: int
    content_size: int
    extension_size: int
    supercompression_scheme: int


def serialize_common_resource_descriptor(descriptor: CommonResourceDescriptor) -> bytes:
    """Serialize a common resource descriptor.

    :param descriptor: The descriptor object.

    :returns: A bytes object containing the serialized descriptor.
    """

    return struct.pack(
        COMMON_DESCRIPTOR_FORMAT,
        descriptor["type"],
        descriptor["format"],
        descriptor["content_size"],
        descriptor["extension_size"],
        descriptor["supercompression_scheme"],
    )


def deserialize_common_resource_descriptor(raw: bytes) -> CommonResourceDescriptor:
    """Deserialize a common resource descriptor.

    :param raw: A bytes object containing the serialized descriptor.

    :returns: The descriptor object.
    """

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
