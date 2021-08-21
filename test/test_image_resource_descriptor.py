import struct
import io
from .test_header import RES_HEADER
from gcf import Header, ResourceType, SupercompressionScheme
from gcf.image import ImageResourceDescriptor, ImageFlags
from gcf.vulkan import Format


# A an 2D image resource descriptor with format R8G8B8A8_UINT, width 2x1x1 with 1 layer and 1 mip level
# super-compressed in ZLib format
RES_IMAGE_RESOURCE_DESCRIPTOR = struct.pack(
    '=3I4H2BHQ',
    ResourceType.Image.value,
    Format.R8G8B8A8_UINT.value,
    8,
    SupercompressionScheme.ZLib.value,
    2,
    1,
    1,
    1,
    1,
    ImageFlags.Image2D.value,
    0
)


def verify_descriptor_assertions(d: ImageResourceDescriptor, h: Header):
    assert d.resource_type is ResourceType.Image
    assert d.format is Format.R8G8B8A8_UINT
    assert d.size == 8
    assert d.supercompression_scheme is SupercompressionScheme.ZLib
    assert d.type_data == RES_IMAGE_RESOURCE_DESCRIPTOR[
        ImageResourceDescriptor.TYPE_DATA_OFFSET
        :ImageResourceDescriptor.TYPE_DATA_OFFSET + ImageResourceDescriptor.TYPE_DATA_SIZE
    ]
    assert d.header is h
    assert d.width == 2
    assert d.height == 1
    assert d.depth == 1
    assert d.layer_count == 1
    assert d.mip_level_count == 1
    assert len(d.flags) == 1
    assert ImageFlags.Image2D in d.flags


def test_init():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ImageResourceDescriptor(
        Format.R8G8B8A8_UINT,
        8,
        header=h,
        width=2,
        height=1,
        supercompression_scheme=SupercompressionScheme.ZLib,
        flags=[ImageFlags.Image2D]
    )

    verify_descriptor_assertions(d, h)


def test_serialize():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ImageResourceDescriptor(
        Format.R8G8B8A8_UINT,
        8,
        header=h,
        width=2,
        height=1,
        supercompression_scheme=SupercompressionScheme.ZLib,
        flags=[ImageFlags.Image2D]
    )

    assert d.serialize() == RES_IMAGE_RESOURCE_DESCRIPTOR


def test_from_bytes():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ImageResourceDescriptor.from_bytes(RES_IMAGE_RESOURCE_DESCRIPTOR, h)

    verify_descriptor_assertions(d, h)


def test_from_file():
    f = io.BytesIO(RES_IMAGE_RESOURCE_DESCRIPTOR)
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = ImageResourceDescriptor.from_file(f, h)

    verify_descriptor_assertions(d, h)
