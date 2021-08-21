from numpy.lib.index_tricks import r_
from gcf import Header
import io
import numpy as np
from gcf.image import ImageResourceDescriptor, MipLevelDescriptor, MipLevel
from gcf.vulkan import Format
from .test_mip_level_descriptor import RES_MIP_LEVEL_DESCRIPTOR


RES_MIP_LEVEL_DATA = b'\0' * (16 * 8 * 8)
RES_MIP_LEVEL = RES_MIP_LEVEL_DESCRIPTOR + RES_MIP_LEVEL_DATA

# A mip level image as a numpy array with 1 layer, size 16x1x1, RGB UINT format with 8 bits per channel.
RES_MIP_LEVEL_IMAGE = np.zeros((1, 1, 16, 16, 3), dtype=np.uint8)


def verify_mip_level_assertions(d, l):
    assert l.data == RES_MIP_LEVEL_DATA
    assert l.descriptor == d


def test_init():
    d = MipLevelDescriptor(1024, 256, 16, 8, 8)
    l = MipLevel(d, RES_MIP_LEVEL_DATA)

    verify_mip_level_assertions(d, l)


def test_serialize():
    d = MipLevelDescriptor(1024, 256, 16, 8, 8)
    l = MipLevel(d, RES_MIP_LEVEL_DATA)
    l_raw = l.serialize()

    assert l_raw == RES_MIP_LEVEL


def test_from_bytes():
    d = MipLevelDescriptor(1024, 256, 16, 8, 8)
    l = MipLevel.from_bytes(RES_MIP_LEVEL)

    verify_mip_level_assertions(d, l)


def test_from_file():
    f = io.BytesIO(RES_MIP_LEVEL)
    d = MipLevelDescriptor(1024, 256, 16, 8, 8)
    l = MipLevel.from_file(f)

    verify_mip_level_assertions(d, l)


def test_from_image_data():
    h = Header(1)
    d = ImageResourceDescriptor(Format.R8G8B8_UINT, RES_MIP_LEVEL_IMAGE.nbytes, header=h, width=16, height=16)
    l = MipLevel.from_image_data(d, RES_MIP_LEVEL_IMAGE)
    r_bytes = RES_MIP_LEVEL_IMAGE.flatten().tobytes()

    assert l.data == r_bytes
    assert l.descriptor.compressed_size == len(r_bytes)
    assert l.descriptor.uncompressed_size == l.descriptor.compressed_size
    assert l.descriptor.row_stride == 16 * 3
    assert l.descriptor.depth_stride == l.descriptor.row_stride * 16
    assert l.descriptor.layer_stride == l.descriptor.depth_stride