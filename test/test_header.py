import io
import struct

import pytest

from gcf import ContainerFlags, Header

# Example header with version 99, 5 resources and `Unpadded` flag
RES_HEADER = b'GC99' + struct.pack('=2H', 5, ContainerFlags.Unpadded.value)
RES_HEADER_NOFLAGS = b'GC99' + struct.pack('=2H', 5, 0)


def test_init():
    h = Header(5, [ContainerFlags.Unpadded], version=99)

    assert h.resource_count == 5
    assert h.version == 99
    assert len(h.flags) == 1
    assert ContainerFlags.Unpadded in h.flags


def test_init_default():
    h = Header(6)

    assert h.resource_count == 6
    assert h.version == Header.DEFAULT_VERSION
    assert h.flags is not None and not h.flags


def test_serialize():
    h = Header(5, [ContainerFlags.Unpadded], version=99)
    s = h.serialize()

    assert s == RES_HEADER


def test_serialize_noflags():
    h = Header(5, version=99)
    s = h.serialize()

    assert s == RES_HEADER_NOFLAGS


def test_from_bytes():
    h = Header.from_bytes(RES_HEADER, valid_version=99)

    assert h.resource_count == 5
    assert h.version == 99
    assert len(h.flags) == 1
    assert ContainerFlags.Unpadded in h.flags


def test_from_bytes_noflags():
    h = Header.from_bytes(RES_HEADER_NOFLAGS, valid_version=99)

    assert h.resource_count == 5
    assert h.version == 99
    assert h.flags is not None and not h.flags


def test_from_bytes_wrong_version():
    with pytest.raises(ValueError):
        h = Header.from_bytes(RES_HEADER, valid_version=88)


def test_from_file():
    f = io.BytesIO(RES_HEADER)
    h = Header.from_file(f, valid_version=99)

    assert h.resource_count == 5
    assert h.version == 99
    assert len(h.flags) == 1
    assert ContainerFlags.Unpadded in h.flags
