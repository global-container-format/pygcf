import struct

from gcf import ContainerFlags, Header, deserialize_header, make_magic_number, serialize_header


def test_serialize_deserialize_header():
    magic = make_magic_number()
    expected_header: Header = {"magic": magic, "flags": ContainerFlags.UNPADDED, "resource_count": 666}

    raw = serialize_header(expected_header)
    actual_header = deserialize_header(raw)

    assert actual_header == expected_header


def test_serialize_header():
    """Test against spec."""

    magic = make_magic_number()
    expected_header: Header = {"magic": magic, "flags": ContainerFlags.UNPADDED, "resource_count": 666}

    raw = serialize_header(expected_header)

    (actual_magic, actual_resource_count, actual_flags) = struct.unpack("=I2H", raw)

    assert actual_magic == magic
    assert actual_resource_count == 666
    assert actual_flags == ContainerFlags.UNPADDED.value


def test_make_magic_number():
    actual = make_magic_number(99)
    (expected,) = struct.unpack("<I", b"GC99")

    assert actual == expected
