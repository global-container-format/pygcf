import struct
from . import ResourceDescriptor, Resource, SupercompressionScheme, Header, ResourceType
from .compress import COMPRESSOR_TABLE
from .vulkan import Format


class BlobResourceDescriptor(ResourceDescriptor):
    TYPE_DATA_FORMAT = '=2QH'
    TYPE_DATA_FORMAT_SIZE = struct.calcsize(TYPE_DATA_FORMAT)

    def __init__(
        self,
        size: int,
        /,
        header: Header,
        uncompressed_size: int,
        supercompression_scheme: SupercompressionScheme = SupercompressionScheme.NoCompression
    ):
        super().__init__(
            ResourceType.Blob,
            Format.UNDEFINED,
            size,
            header=header,
            supercompression_scheme=supercompression_scheme,
            type_data=self.TYPE_DATA_CUSTOM
        )

        self.uncompressed_size = uncompressed_size

    @property
    def type_data(self):
        return struct.pack(self.TYPE_DATA_FORMAT, self.uncompressed_size, 0, 0)

    @classmethod
    def from_resource_descriptor(cls, descriptor: ResourceDescriptor):
        fields = struct.unpack(cls.TYPE_DATA_FORMAT, descriptor.type_data)
        uncompressed_size = fields[0]

        return cls(
            descriptor.size,
            uncompressed_size=uncompressed_size,
            supercompression_scheme=descriptor.supercompression_scheme,
            header=descriptor.header
        )

    @classmethod
    def from_bytes(cls, raw: bytes, header: Header):
        base_descriptor = ResourceDescriptor.from_bytes(raw, header)

        return cls.from_resource_descriptor(base_descriptor)

    @classmethod
    def from_file(cls, f, header: Header):
        base_descriptor = ResourceDescriptor.from_file(f, header)

        return cls.from_resource_descriptor(base_descriptor)


class BlobResource(Resource):
    def __init__(self, descriptor: BlobResourceDescriptor, data: bytes):
        '''Create a new blob resource from compressed data.

        ARGUMENTS:
            descriptor - The blob resource descriptor.
            data - The compressed data.
        '''
        super().__init__(descriptor)

        self.data = data

    @property
    def content_data(self) -> bytes:
        return self.data

    @classmethod
    def from_uncompressed_data(cls, descriptor: BlobResourceDescriptor, data: bytes):
        '''Create a new blob resource from uncompressed data.

        ARGUMENTS:
            descriptor - The blob resource descriptor.
            data - The uncompressed data.

        RETURN VALUE:
            A new blob resource object.
        '''
        compressor = COMPRESSOR_TABLE[descriptor.supercompression_scheme][0]
        flattened_data = data.flatten().tobytes()
        compressed_data = compressor(flattened_data)

        return cls(descriptor, compressed_data)
