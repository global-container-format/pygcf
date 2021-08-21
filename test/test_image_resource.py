from gcf import Header
from gcf.image import ImageResource, ImageResourceDescriptor, MipLevel, MipLevelDescriptor
from gcf.vulkan import Format
from .test_mip_level import RES_MIP_LEVEL_DATA


def test_init():
    h = Header(1)
    d = ImageResourceDescriptor(Format.R8_UINT, 16 * 8 * 8, header=h, width=16, height=8, depth=8)
    ld = MipLevelDescriptor(1024, 256, 16, 8, 8)
    l = MipLevel(ld, RES_MIP_LEVEL_DATA)
    r = ImageResource(d, [l])

    assert r.descriptor == d
    assert len(r.mip_levels) == 1 and r.mip_levels[0] == l
    assert r.content_data == l.serialize()
