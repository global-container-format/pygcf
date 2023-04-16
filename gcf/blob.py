"""
Blob resource.

Spec: https://github.com/global-container-format/gcf-spec/blob/master/resources/blob.md
"""
import struct

from . import Header, Resource, ResourceDescriptor, ResourceType, SupercompressionScheme
from .compress import COMPRESSOR_TABLE
from .resource_format import Format


class BlobResourceDescriptor(ResourceDescriptor):
    """A blob resource descriptor."""

    TYPE_INFO_FORMAT = "=2Q"
    TYPE_INFO_FORMAT_SIZE = struct.calcsize(TYPE_INFO_FORMAT)

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
        )

        self.uncompressed_size = uncompressed_size

    @property
    def type_info(self):
        """Return the blob descriptor's type info."""
        return struct.pack(self.TYPE_INFO_FORMAT, self.uncompressed_size, 0)

    @classmethod
    def from_resource_descriptor(cls, descriptor: ResourceDescriptor):
        """Create a blob descriptor from a resource descriptor."""
        if not isinstance(descriptor.type_info, bytes):
            raise TypeError("Expected blob type info.")

        fields = struct.unpack(cls.TYPE_INFO_FORMAT, descriptor.type_info)
        uncompressed_size = fields[0]

        return cls(
            descriptor.size,
            uncompressed_size=uncompressed_size,
            supercompression_scheme=descriptor.supercompression_scheme,
            header=descriptor.header,
        )

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        base_descriptor = ResourceDescriptor.from_bytes(raw, header)

        return cls.from_resource_descriptor(base_descriptor)

    @classmethod
    def from_file(cls, fileobj, header: Header):
        base_descriptor = ResourceDescriptor.from_file(fileobj, header)

        return cls.from_resource_descriptor(base_descriptor)


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
