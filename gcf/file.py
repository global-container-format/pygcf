"""
File-based GCF handling utilities.

Functions in this module require the supplied file objects being seekable.
"""

import io
from typing import BinaryIO, Union, cast

from .blob import BlobResourceDescriptor, deserialize_blob_descriptor, serialize_blob_descriptor
from .header import (
    DEFAULT_VERSION,
    HEADER_SIZE,
    ContainerFlags,
    Header,
    deserialize_header,
    make_magic_number,
    serialize_header,
)
from .resource import (
    COMMON_DESCRIPTOR_SIZE,
    CommonResourceDescriptor,
    ResourceType,
    deserialize_common_resource_descriptor,
    serialize_common_resource_descriptor,
)
from .texture import (
    TextureResourceDescriptor,
    deserialize_texture_resource_descriptor,
    serialize_texture_resource_descriptor,
)
from .util import align_size

ExtendedResourceDescriptor = Union[BlobResourceDescriptor, TextureResourceDescriptor, bytes]


def read_header(fileobj: BinaryIO, expected_version=DEFAULT_VERSION) -> Header:
    """Read a GCF header from a file object.

        :param fileobj: The file object.
        :param expected_version: The expected GCF version. If the version mismatches, a value error is raised.

        :returns: The read header.
    """

    raw_header = fileobj.read(HEADER_SIZE)
    expected_magic_number = make_magic_number(expected_version)
    header = deserialize_header(raw_header)

    if header["magic"] != expected_magic_number:
        raise ValueError("Invalid header magic number", header["magic"])

    return header


def write_header(fileobj: BinaryIO, header: Header):
    """Write a GCF header to a file object.

        :param fileobj: The file object.
        :param header: The header object.
    """

    fileobj.write(serialize_header(header))


def read_common_resource_descriptor(fileobj: BinaryIO) -> CommonResourceDescriptor:
    """Read a common resource descriptor from a file object.

        :param fileobj: The file object.

        :returns: The read descriptor.
    """

    raw_descriptor = fileobj.read(COMMON_DESCRIPTOR_SIZE)
    descriptor = deserialize_common_resource_descriptor(raw_descriptor)

    return descriptor


def write_common_resource_descriptor(fileobj: BinaryIO, descriptor: CommonResourceDescriptor):
    """Write a common resource descriptor to a file object.

        :param fileobj: The file object.
        :param descriptor: The descriptor object.
    """

    fileobj.write(serialize_common_resource_descriptor(descriptor))


def skip_resource(fileobj: BinaryIO, common_descriptor: CommonResourceDescriptor, header: Header):
    """Skip a resource from a GCF file.

        :param fileobj: The file object.
        :param common_descriptor: The common descriptor object of the resource to skip.
        :param header: The GCF file header.
    """

    extended_descriptor_size = common_descriptor["extension_size"]
    content_data_size = common_descriptor["content_size"]
    total_skip_size = extended_descriptor_size + content_data_size

    fileobj.seek(total_skip_size, io.SEEK_CUR)

    skip_padding(fileobj, header)


def read_extended_resource_descriptor(
    fileobj: BinaryIO, common_descriptor: CommonResourceDescriptor
) -> ExtendedResourceDescriptor:
    """Read an extended resource descriptor from a file object.

        The returned extended descriptor will be deserialized if it's a standard one
        or returned as a bytes object if it's custom.

        :param fileobj: The file object.
        :param common_descriptor: The common descriptor associated with the extended descriptor to read.

        :returns: The read descriptor.
    """

    extended_descriptor_size = common_descriptor["extension_size"]
    resource_type = common_descriptor["type"]
    raw_extended_descriptor = fileobj.read(extended_descriptor_size)

    deserializers = {
        ResourceType.BLOB.value: deserialize_blob_descriptor,
        ResourceType.TEXTURE.value: deserialize_texture_resource_descriptor,
    }

    def nop_deserializer(raw: bytes, _common_descriptor: CommonResourceDescriptor) -> bytes:
        return raw

    return cast(
        ExtendedResourceDescriptor,
        deserializers.get(resource_type, nop_deserializer)(raw_extended_descriptor, common_descriptor),
    )


def write_extended_resource_descriptor(fileobj: BinaryIO, descriptor: ExtendedResourceDescriptor):
    """Write an extended resource descriptor to a file object.

        The provided descriptor can either be a known descriptor object or a bytes object.
        This is especially useful when writing custom descriptors.

        :param fileobj: The file object.
        :param descriptor: The descriptor object.
    """

    serializers = {
        TextureResourceDescriptor: serialize_texture_resource_descriptor,
        BlobResourceDescriptor: serialize_blob_descriptor,
        bytes: lambda x: x,
    }

    try:
        serialize = serializers[type(descriptor)]
    except KeyError as exc:
        raise ValueError("Unknown descriptor object", descriptor) from exc

    raw_descriptor = serialize(descriptor)

    fileobj.write(raw_descriptor)


def skip_padding(fileobj: BinaryIO, header: Header):
    """Skip padding between two resources from a GCF file.

        :param fileobj: The file object.
        :param header: The GCF file header.
    """

    is_alignment_required = not header["flags"] & ContainerFlags.UNPADDED

    if is_alignment_required:
        current_offset = fileobj.tell()
        aligned_offset = align_size(current_offset, 8)

        fileobj.seek(aligned_offset, io.SEEK_CUR)
