import io
import struct

from gcf import Header, ResourceDescriptor, ResourceType, SupercompressionScheme
from gcf.resource_format import Format

from .test_header import RES_HEADER

# A resource descriptor of type Test, length 128 bytes, compressed with zlib and type-specific data a byte
# array from 0 to 17 (inclusive)
RES_RESOURCE_DESCRIPTOR = struct.pack(
    "=3I2H16B", ResourceType.TEST.value, Format.UNDEFINED.value, 128, SupercompressionScheme.ZLIB.value, 0, *range(16)
)


def test_init():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor(
        ResourceType.TEST,
        Format.UNDEFINED,
        128,
        header=h,
        supercompression_scheme=SupercompressionScheme.ZLIB,
        type_data=struct.pack("=16B", *range(16)),
    )

    assert d.resource_type is ResourceType.TEST
    assert d.format is Format.UNDEFINED
    assert d.size == 128
    assert d.supercompression_scheme is SupercompressionScheme.ZLIB
    assert d.type_data == struct.pack("=16B", *range(16))
    assert d.header is h


def test_serialize():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor(
        ResourceType.TEST,
        Format.UNDEFINED,
        128,
        header=h,
        supercompression_scheme=SupercompressionScheme.ZLIB,
        type_data=struct.pack("=16B", *range(16)),
    )

    assert d.serialize() == RES_RESOURCE_DESCRIPTOR


def test_from_bytes():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor.from_bytes(RES_RESOURCE_DESCRIPTOR, h)

    assert d.resource_type is ResourceType.TEST
    assert d.format is Format.UNDEFINED
    assert d.size == 128
    assert d.supercompression_scheme is SupercompressionScheme.ZLIB
    assert d.type_data == struct.pack("=16B", *range(16))
    assert d.header is h


def test_from_file():
    f = io.BytesIO(RES_RESOURCE_DESCRIPTOR)
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor.from_file(f, h)

    assert d.resource_type is ResourceType.TEST
    assert d.format is Format.UNDEFINED
    assert d.size == 128
    assert d.supercompression_scheme is SupercompressionScheme.ZLIB
    assert d.type_data == struct.pack("=16B", *range(16))
    assert d.header is h
