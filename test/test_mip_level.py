import io
from gcf.image import MipLevelDescriptor, MipLevel
from .test_mip_level_descriptor import RES_MIP_LEVEL_DESCRIPTOR


RES_MIP_LEVEL_DATA = b'\0' * (16 * 8 * 8)
RES_MIP_LEVEL = RES_MIP_LEVEL_DESCRIPTOR + RES_MIP_LEVEL_DATA


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
