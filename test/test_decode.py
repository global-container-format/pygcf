import struct

from gcf import Header, ResourceDescriptor, ResourceType
from gcf.blob import BlobResourceDescriptor
from gcf.decode import decode_resource_descriptor
from gcf.image import ImageFlags, ImageResourceDescriptor
from gcf.resource_format import Format


def test_decode_resource_descriptor():
    h = Header(2)
    d_image = ResourceDescriptor(
        ResourceType.IMAGE,
        Format.R8G8B8A8_UINT,
        8,
        header=h,
        type_data=struct.pack("=3H2BHIH", 2, 1, 1, 1, 1, ImageFlags.IMAGE_2D.value, 0, 0),
    )
    d_blob = ResourceDescriptor(
        ResourceType.BLOB,
        Format.UNDEFINED,
        8,
        header=h,
        type_data=struct.pack("=2Q", 2, 0),
    )
    d_res = ResourceDescriptor(
        ResourceType.TEST,
        Format.UNDEFINED,
        8,
        header=h,
        type_data=struct.pack("=2Q", 2, 0),
    )

    assert isinstance(decode_resource_descriptor(d_image), ImageResourceDescriptor)
    assert isinstance(decode_resource_descriptor(d_blob), BlobResourceDescriptor)
    assert type(decode_resource_descriptor(d_res)).__name__ == ResourceDescriptor.__name__
