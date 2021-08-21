import io
import struct
from gcf import Header, ResourceDescriptor, SupercompressionScheme
from gcf.blob import BlobResource, BlobResourceDescriptor
from gcf.image import ImageFlags, ImageResourceDescriptor, MipLevel, MipLevelDescriptor
from gcf.vulkan import Format
from gcf.util import *


def test_align_size():
    assert align_size(15, 16) == 16
    assert align_size(257, 256) == 512
    assert align_size(0, 2) == 0
    assert align_size(2, 2) == 2


def test_compute_mip_level_size():
    assert compute_mip_level_size(1, 256, 256, 1) == (256, 256, 1)
    assert compute_mip_level_size(2, 256, 256, 1) == (128, 128, 1)
    assert compute_mip_level_size(3, 256, 128, 1) == (64, 32, 1)


def test_compute_mip_level_resize_factor():
    assert compute_mip_level_resize_factor(1) == 1
    assert compute_mip_level_resize_factor(2) == 1/2
    assert compute_mip_level_resize_factor(3) == 1/4


def test_skip_resource():
    h = Header(2)
    d1 = BlobResourceDescriptor(128, header=h, uncompressed_size=128)
    r1 = BlobResource(d1, b'\0' * 128)
    d2 = BlobResourceDescriptor(128, header=h, uncompressed_size=128)
    r2 = BlobResource(d2, b'\0' * 128)
    raw_r1 = r1.serialize()
    raw_resources = raw_r1 + r2.serialize()
    f = io.BytesIO(raw_resources)

    skip_resources(f, 1, h)

    assert f.tell() == len(raw_r1)


def test_decode_resource_descriptor():
    h = Header(2)
    d_image = ResourceDescriptor(
        ResourceType.Image,
        Format.R8G8B8A8_UINT,
        8,
        header=h,
        type_data=struct.pack('=3H2BHQ', 2, 1, 1, 1, 1, ImageFlags.Image2D.value, 0)
    )
    d_blob = ResourceDescriptor(
        ResourceType.Blob,
        Format.UNDEFINED,
        8,
        header=h,
        type_data=struct.pack('=2QH', 2, 0, 0)
    )

    assert isinstance(decode_resource_descriptor(d_image), ImageResourceDescriptor)
    assert isinstance(decode_resource_descriptor(d_blob), BlobResourceDescriptor)


def test_skip_mip_level():
    ld = MipLevelDescriptor(100, 100, 10, 10, 1)
    l = MipLevel(ld, bytes(range(100)))
    l_raw = l.serialize()
    f = io.BytesIO(l_raw * 3)

    skip_mip_levels(f, 2)

    assert f.tell() == len(l_raw) * 2
