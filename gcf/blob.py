"""
Blob resource.

Spec: https://github.com/global-container-format/gcf-spec/blob/master/resources/blob.md
"""
import struct

from typing import BinaryIO
from . import Header, Resource, ResourceDescriptor, ResourceType, SupercompressionScheme, COMMON_DESCRIPTOR_SIZE
from .compress import COMPRESSOR_TABLE
from .resource_format import Format

EXTENDED_DESCRIPTOR_FORMAT = "=2Q"
EXTENDED_DESCRIPTOR_SIZE = struct.calcsize(EXTENDED_DESCRIPTOR_FORMAT)


class BlobResourceDescriptor(ResourceDescriptor):
    """A blob resource descriptor."""

    def __init__(
        self,
        size: int,
        /,
        header: Header,
        uncompressed_size: int,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NO_COMPRESSION,
    ):
        """Create a new blob resource descriptor."""

        super().__init__(
            ResourceType.BLOB,
            Format.UNDEFINED,
            size,
            header=header,
            supercompression_scheme=supercompression_scheme,
            extended_descriptor=struct.pack(EXTENDED_DESCRIPTOR_FORMAT, 0, 0)
        )

        self.uncompressed_size = uncompressed_size

    @property
    def extended_descriptor(self):
        """Return the blob descriptor's type info."""

        return struct.pack(EXTENDED_DESCRIPTOR_FORMAT, self.uncompressed_size, 0)

    @classmethod
    def from_resource_descriptor(cls, descriptor: ResourceDescriptor, raw_extended_descriptor: bytes):
        """Create a blob descriptor from a resource descriptor."""

        fields = struct.unpack(EXTENDED_DESCRIPTOR_FORMAT, raw_extended_descriptor)
        uncompressed_size = fields[0]

        return cls(
            descriptor.size,
            uncompressed_size=uncompressed_size,
            supercompression_scheme=descriptor.supercompression_scheme,
            header=descriptor.header,
        )

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        common_descriptor = ResourceDescriptor.from_bytes(raw, header)
        total_descriptor_size = COMMON_DESCRIPTOR_SIZE + EXTENDED_DESCRIPTOR_SIZE
        raw_extended_descriptor = raw[COMMON_DESCRIPTOR_SIZE : total_descriptor_size]

        return cls.from_resource_descriptor(common_descriptor, raw_extended_descriptor)

    @classmethod
    def from_file(cls, fileobj: BinaryIO, header: Header):
        common_descriptor = ResourceDescriptor.from_file(fileobj, header)
        raw_extended_descriptor = fileobj.read(EXTENDED_DESCRIPTOR_SIZE)

        return cls.from_resource_descriptor(common_descriptor, raw_extended_descriptor)


class BlobResource(Resource):
    """A blob resource."""

    def __init__(self, descriptor: BlobResourceDescriptor, data: bytes):
        """Create a new blob resource from compressed data.

        ARGUMENTS:
            descriptor - The blob resource descriptor.
            data - The compressed data.
        """
        super().__init__(descriptor)

        self._data = data

    @property
    def content_data(self) -> bytes:
        return self._data

    @classmethod
    def from_uncompressed_data(
        cls,
        data: bytes,
        /,
        header: Header,
        supercompression_scheme: SupercompressionScheme,
    ):
        """Create a new blob resource from uncompressed data.

        ARGUMENTS:
            data - The uncompressed data.
            header - The header.
            supercompression_scheme - The supercompression scheme.

        RETURN VALUE:
            A new blob resource object.
        """
        compressor = COMPRESSOR_TABLE[supercompression_scheme][0]
        compressed_data = compressor(data)

        descriptor = BlobResourceDescriptor(
            len(compressed_data),
            header=header,
            uncompressed_size=len(data),
            supercompression_scheme=supercompression_scheme,
        )

        return cls(descriptor, compressed_data)
