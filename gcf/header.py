"""
Header serialization.
"""

import struct
from enum import Flag, auto
from typing import TypedDict

DEFAULT_VERSION = 3
MAGIC_PREFIX = b"GC"
HEADER_FORMAT = "=I2H"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class ContainerFlags(Flag):
    """Container flags."""

    UNPADDED = auto()


class Header(TypedDict):
    """GCF file header."""

    magic: int
    resource_count: int
    flags: ContainerFlags


def make_magic_number(version: int = DEFAULT_VERSION) -> bytes:
    """Return the magic number for a given GCF version."""

    if version > 99:
        raise ValueError("Version must be < 100", version)

    version_bytes = str(version).zfill(2).encode("utf-8")
    magic_bytes = MAGIC_PREFIX + version_bytes

    return struct.unpack("<I", magic_bytes)[0]


def serialize_header(header: Header) -> bytes:
    """Serialize a GCF file header.

    :param header: The header object.

    :returns: A bytes object containing the serialized representation of the header.
    """

    return struct.pack(HEADER_FORMAT, header["magic"], header["resource_count"], header["flags"].value)


def deserialize_header(raw: bytes) -> Header:
    """Serialize a GCF file header.

    :param raw: A bytes object containing the serialized representation of the header.

    :returns: A header object.
    """

    if not len(raw) == HEADER_SIZE:
        raise ValueError("Invalid header data size", len(raw))

    fields = struct.unpack(HEADER_FORMAT, raw)

    return {"magic": fields[0], "resource_count": fields[1], "flags": ContainerFlags(fields[2])}
