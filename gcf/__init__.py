"""
Python library to read and write `GCF <https://github.com/global-container-format/gcf-spec>`_ files.
"""

from .blob import (
    BlobResourceDescriptor,
    deserialize_blob_descriptor,
    make_blob_resource_descriptor,
    serialize_blob_descriptor,
)
from .header import ContainerFlags, Header, deserialize_header, make_magic_number, serialize_header
from .resource import (
    CommonResourceDescriptor,
    ResourceType,
    deserialize_common_resource_descriptor,
    serialize_common_resource_descriptor,
)
from .texture import (
    MipLevelDescriptor,
    TextureFlags,
    TextureResourceDescriptor,
    deserialize_mip_level_descriptor,
    deserialize_texture_resource_descriptor,
    serialize_mip_level_descriptor,
    serialize_texture_resource_descriptor,
    make_texture_resource_descriptor,
    serialize_mip_level_data,
    deserialize_mip_level_data
)
from .compression import SupercompressionScheme
from .resource_format import Format
