import io
import struct

from gcf import Header, ResourceType, SupercompressionScheme
from gcf.blob import BlobResourceDescriptor
from gcf.resource_format import Format

from .test_header import RES_HEADER

# A deflate-compressed blob resource 128 bytes long uncompressed, 8 bytes long compressed
RES_BLOB_RESOURCE_DESCRIPTOR = struct.pack(
    "=3I2H2Q",
    ResourceType.BLOB.value,
    Format.UNDEFINED.value,
    8,
    SupercompressionScheme.DEFLATE.value,
    0,
    128,
    0,
)


def verify_descriptor_assertions(d: BlobResourceDescriptor, h: Header):
    assert d.resource_type is ResourceType.BLOB
    assert d.format is Format.UNDEFINED
    assert d.size == 8
    assert d.supercompression_scheme is SupercompressionScheme.DEFLATE
    assert (
        d.extended_descriptor
        == RES_BLOB_RESOURCE_DESCRIPTOR[
            BlobResourceDescriptor.EXTENDED_DESCRIPTOR_OFFSET : BlobResourceDescriptor.EXTENDED_DESCRIPTOR_OFFSET
            + BlobResourceDescriptor.EXTENDED_DESCRIPTOR_SIZE
        ]
    )
    assert d.header is h
    assert d.uncompressed_size == 128


def test_init():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = BlobResourceDescriptor(
        8,
        header=h,
        uncompressed_size=128,
        supercompression_scheme=SupercompressionScheme.DEFLATE,
    )

    verify_descriptor_assertions(d, h)


def test_serialize():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = BlobResourceDescriptor(
        8,
        header=h,
        uncompressed_size=128,
        supercompression_scheme=SupercompressionScheme.DEFLATE,
    )

    assert d.serialize() == RES_BLOB_RESOURCE_DESCRIPTOR


def test_from_bytes():
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = BlobResourceDescriptor.from_bytes(RES_BLOB_RESOURCE_DESCRIPTOR, h)

    verify_descriptor_assertions(d, h)


def test_from_file():
    f = io.BytesIO(RES_BLOB_RESOURCE_DESCRIPTOR)
    h = Header.from_bytes(RES_HEADER, valid_version=99)
    d = BlobResourceDescriptor.from_file(f, h)

    verify_descriptor_assertions(d, h)
