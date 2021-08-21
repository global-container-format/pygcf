import struct
import io
from .test_header import RES_HEADER
from gcf import Header, ResourceType, ResourceDescriptor, SupercompressionScheme
from gcf.vulkan import Format


# A resource descriptor of type Test, length 128 bytes, compressed with zlib and type-specific data a byte
# array from 0 to 17 (inclusive)
RES_RESOURCE_DESCRIPTOR = struct.pack(
    '=3IH18B',
    ResourceType.Test.value,
    Format.UNDEFINED.value,
    128,
    SupercompressionScheme.ZLib.value,
    *range(18)
)


def test_init():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor(
        ResourceType.Test,
        Format.UNDEFINED,
        128,
        header=h,
        supercompression_scheme=SupercompressionScheme.ZLib,
        type_data=struct.pack('=18B', *range(18))
    )

    assert d.resource_type is ResourceType.Test
    assert d.format is Format.UNDEFINED
    assert d.size == 128
    assert d.supercompression_scheme is SupercompressionScheme.ZLib
    assert d.type_data == struct.pack('=18B', *range(18))
    assert d.header is h


def test_serialize():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor(
        ResourceType.Test,
        Format.UNDEFINED,
        128,
        header=h,
        supercompression_scheme=SupercompressionScheme.ZLib,
        type_data=struct.pack('=18B', *range(18))
    )

    assert d.serialize() == RES_RESOURCE_DESCRIPTOR


def test_from_bytes():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor.from_bytes(RES_RESOURCE_DESCRIPTOR, h)

    assert d.resource_type is ResourceType.Test
    assert d.format is Format.UNDEFINED
    assert d.size == 128
    assert d.supercompression_scheme is SupercompressionScheme.ZLib
    assert d.type_data == struct.pack('=18B', *range(18))
    assert d.header is h


def test_from_file():
    f = io.BytesIO(RES_RESOURCE_DESCRIPTOR)
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ResourceDescriptor.from_file(f, h)

    assert d.resource_type is ResourceType.Test
    assert d.format is Format.UNDEFINED
    assert d.size == 128
    assert d.supercompression_scheme is SupercompressionScheme.ZLib
    assert d.type_data == struct.pack('=18B', *range(18))
    assert d.header is h
