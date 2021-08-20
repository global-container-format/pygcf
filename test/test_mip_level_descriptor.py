import io
import struct
from gcf.image import MipLevelDescriptor


# A mip level descriptor of compressed size 1024, uncompressed size 256
# and stride 16x8x8
RES_MIP_LEVEL_DESCRIPTOR = struct.pack(MipLevelDescriptor.FORMAT, 1024, 256, 16, 8, 8, 0, 0)


def verify_descriptor_assertions(d):
    assert d.compressed_size == 1024
    assert d.uncompressed_size == 256
    assert d.row_stride == 16
    assert d.depth_stride == 8
    assert d.layer_stride == 8


def test_init():
    d = MipLevelDescriptor(1024, 256, 16, 8, 8)

    verify_descriptor_assertions(d)


def test_serialize():
    d = MipLevelDescriptor(1024, 256, 16, 8, 8)

    assert d.serialize() == RES_MIP_LEVEL_DESCRIPTOR


def test_from_bytes():
    d = MipLevelDescriptor.from_bytes(RES_MIP_LEVEL_DESCRIPTOR)

    verify_descriptor_assertions(d)


def test_from_file():
    f = io.BytesIO(RES_MIP_LEVEL_DESCRIPTOR)
    d = MipLevelDescriptor.from_file(f)

    verify_descriptor_assertions(d)
