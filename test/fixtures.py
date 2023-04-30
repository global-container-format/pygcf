import io

from typing import BinaryIO

from gcf import SupercompressionScheme, Format, serialize_common_resource_descriptor, ResourceType, make_magic_number, file, Header, ContainerFlags
from gcf.blob import make_blob_resource_descriptor
from gcf.texture import make_texture_resource_descriptor, TextureFlags

BLOB_RESOURCE_DESCRIPTOR = make_blob_resource_descriptor(100, 200, SupercompressionScheme.TEST.value)

TEXTURE_RESOURCE_DESCRIPTOR = make_texture_resource_descriptor(
    format=Format.R8G8B8_SRGB,
    compressed_content_size=123,
    supercompression_scheme=SupercompressionScheme.TEST.value,
    base_width=100,
    base_height=100,
    layer_count=5,
    mip_level_count=2,
    texture_group=99,
    flags=TextureFlags.TEXTURE_2D
)

CUSTOM_RESOURCE_DESCRIPTOR = serialize_common_resource_descriptor({
    "type": ResourceType.TEST.value,
    "content_size": 123,
    "extension_size": 3,
    "format": Format.UNDEFINED,
    "supercompression_scheme": SupercompressionScheme.NO_COMPRESSION.value
}) + b"123"


def two_resource_gcf_file(padding_enabled: bool) -> BinaryIO:
    magic = make_magic_number()
    header: Header = {
        "magic": magic,
        "flags": ContainerFlags.UNPADDED if not padding_enabled else ContainerFlags(0),
        "resource_count": 2
    }
    fileobj = io.BytesIO()

    file.write_header(fileobj, header)
    file.write_composite_resource_descriptor(fileobj, BLOB_RESOURCE_DESCRIPTOR)
    fileobj.write(b'\xfe' * 100)
    file.write_padding(fileobj, header)
    file.write_composite_resource_descriptor(fileobj, CUSTOM_RESOURCE_DESCRIPTOR)
    fileobj.write(b'\xfb' * 123)
    fileobj.seek(0)

    return fileobj
