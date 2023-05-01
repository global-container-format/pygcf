"""
File-based GCF handling utilities.

Functions in this module require the supplied file objects being seekable.
"""

import io
from functools import reduce
from typing import BinaryIO, List, Tuple, Union, cast

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
    MIP_LEVEL_SIZE,
    MipLevelDescriptor,
    TextureResourceDescriptor,
    deserialize_mip_level_data,
    deserialize_mip_level_descriptor,
    deserialize_texture_resource_descriptor,
    serialize_mip_level_data,
    serialize_mip_level_descriptor,
    serialize_texture_resource_descriptor,
)
from .util import align_size

CompositeResourceDescriptor = Union[BlobResourceDescriptor, TextureResourceDescriptor, bytes]


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


def read_composite_descriptor(fileobj: BinaryIO) -> CompositeResourceDescriptor:
    """Read a composite resource descriptor from a file object.

    The returned composite descriptor will be deserialized if it's a standard one
    or returned as a bytes object if it's custom.

    :param fileobj: The file object.

    :returns: The read composite descriptor.
    """
    raw_common_descriptor = fileobj.read(COMMON_DESCRIPTOR_SIZE)
    common_descriptor = deserialize_common_resource_descriptor(raw_common_descriptor)
    extended_descriptor_size = common_descriptor["extension_size"]
    resource_type = common_descriptor["type"]
    raw_extended_descriptor = fileobj.read(extended_descriptor_size)
    full_descriptor = raw_common_descriptor + raw_extended_descriptor

    deserializers = {
        ResourceType.BLOB.value: deserialize_blob_descriptor,
        ResourceType.TEXTURE.value: deserialize_texture_resource_descriptor,
    }

    def nop_deserializer(raw: bytes, _common_descriptor: CommonResourceDescriptor) -> bytes:
        return raw

    return cast(
        CompositeResourceDescriptor,
        deserializers.get(resource_type, nop_deserializer)(full_descriptor, common_descriptor),
    )


def write_composite_resource_descriptor(fileobj: BinaryIO, descriptor: CompositeResourceDescriptor):
    """Write an composite resource descriptor to a file object.

    The provided descriptor can either be a known descriptor object or a bytes object.
    This is especially useful when writing custom descriptors.

    :param fileobj: The file object.
    :param descriptor: The descriptor object.
    """

    if isinstance(descriptor, bytes):

        def serialize(data: bytes) -> bytes:
            return data

    else:
        serializer_map = {
            ResourceType.TEXTURE.value: serialize_texture_resource_descriptor,
            ResourceType.BLOB.value: serialize_blob_descriptor,
        }

        try:
            serialize = serializer_map[descriptor["type"]]  # type: ignore
        except KeyError as exc:
            raise ValueError("Unknown descriptor object", descriptor) from exc

    raw_descriptor = serialize(descriptor)  # type: ignore

    fileobj.write(raw_descriptor)


def skip_padding(fileobj: BinaryIO, header: Header):
    """Skip padding between two resources from a GCF file.

    :param fileobj: The file object.
    :param header: The GCF file header.
    """

    is_alignment_required = not ContainerFlags(header["flags"]) & ContainerFlags.UNPADDED

    if is_alignment_required:
        current_offset = fileobj.tell()
        aligned_offset = align_size(current_offset, 8)

        fileobj.seek(aligned_offset)


def write_padding(fileobj: BinaryIO, header: Header):
    """Write padding between two resources.

    :param fileobj: The file object.
    :param header: The GCF file header.
    """

    if header["flags"] & ContainerFlags.UNPADDED:
        return

    origin = fileobj.tell()
    aligned = align_size(origin, 8)
    padding_size = aligned - origin
    padding = b"\0" * padding_size

    fileobj.write(padding)


def write_mip_level_descriptor(fileobj: BinaryIO, descriptor: MipLevelDescriptor):
    """Write a mip level descriptor to a file object.

    :param fileobj: The file object.
    :param descriptor: The descriptor object.
    """

    fileobj.write(serialize_mip_level_descriptor(descriptor))


def read_mip_level_descriptor(fileobj: BinaryIO) -> MipLevelDescriptor:
    """Read a mip level descriptor from a file object.

    :param fileobj: The file object.
    :returns:  The descriptor object.
    """
    raw = fileobj.read(MIP_LEVEL_SIZE)

    return deserialize_mip_level_descriptor(raw)


def read_mip_level(
    fileobj: BinaryIO, texture_descriptor: TextureResourceDescriptor
) -> Tuple[MipLevelDescriptor, List[bytes]]:
    """Read a mip level and return its data.

    :param fileobj: The file object.
    :param texture_descriptor: The texture resource descriptor object.

    :returns: A tuple containing the mip level descriptor and the list of uncompressed layers.
    """

    level_descriptor = read_mip_level_descriptor(fileobj)
    raw_layers = fileobj.read(level_descriptor["compressed_size"])

    return level_descriptor, deserialize_mip_level_data(raw_layers, texture_descriptor)


def write_mip_level(
    fileobj: BinaryIO, supercompression_scheme: int, mip_level_descriptor: MipLevelDescriptor, layers: List[bytes]
):
    """Write a mip level to file.

    This function ignores the `compressed_size` and `uncompressed_size` mip level descriptor fields and replaces
    their value when writing to file. `mip_level_descriptor` is not updated by this function.

    :param fileobj: The file object.
    :param supercompression_scheme: The supercompression scheme to compress the data.
    :param mip_level_descriptor: The mip level descriptor object.
    :param layers: The list of uncompressed layer data, one entry per layer.
    """

    mip_level_descriptor = mip_level_descriptor.copy()
    raw_layers = serialize_mip_level_data(layers, supercompression_scheme)

    # Override descriptor's data.
    mip_level_descriptor["compressed_size"] = len(raw_layers)
    mip_level_descriptor["uncompressed_size"] = reduce(lambda total, layer: total + len(layer), layers, 0)

    write_mip_level_descriptor(fileobj, mip_level_descriptor)

    fileobj.write(raw_layers)
