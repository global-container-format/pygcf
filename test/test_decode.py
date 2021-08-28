import struct
from gcf import Header, ResourceDescriptor, ResourceType
from gcf.blob import BlobResourceDescriptor
from gcf.image import ImageFlags, ImageResourceDescriptor
from gcf.decode import decode_resource_descriptor
from gcf.vulkan import Format


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
    d_res = ResourceDescriptor(
        ResourceType.Test,
        Format.UNDEFINED,
        8,
        header=h,
        type_data=struct.pack('=2QH', 2, 0, 0)
    )

    assert isinstance(decode_resource_descriptor(d_image), ImageResourceDescriptor)
    assert isinstance(decode_resource_descriptor(d_blob), BlobResourceDescriptor)
    assert type(decode_resource_descriptor(d_res)).__name__ == ResourceDescriptor.__name__