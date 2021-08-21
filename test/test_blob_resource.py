from gcf import Header
from gcf.compress import compress_zlib
from gcf.blob import BlobResource, BlobResourceDescriptor, SupercompressionScheme
from .test_blob_resource_descriptor import RES_BLOB_RESOURCE_DESCRIPTOR


RES_BLOB_RESOURCE_DATA = b'\0' * 8
RES_BLOB_RESOURCE = RES_BLOB_RESOURCE_DESCRIPTOR + RES_BLOB_RESOURCE_DATA


def test_init():
    h = Header(1)
    d = BlobResourceDescriptor(8, header=h, uncompressed_size=128, supercompression_scheme=SupercompressionScheme.Deflate)
    r = BlobResource(d, RES_BLOB_RESOURCE_DATA)

    assert r.descriptor == d
    assert r.data == RES_BLOB_RESOURCE_DATA
    assert r.content_data == r.data


def test_from_uncompressed_data():
    compressed_data = compress_zlib(RES_BLOB_RESOURCE_DATA)
    h = Header(1)
    r = BlobResource.from_uncompressed_data(RES_BLOB_RESOURCE_DATA, header=h, supercompression_scheme=SupercompressionScheme.ZLib)

    assert isinstance(r.descriptor, BlobResourceDescriptor)
    assert r.descriptor.size == len(compressed_data)
    assert r.descriptor.uncompressed_size == len(RES_BLOB_RESOURCE_DATA)
    assert r.descriptor.header == h
    assert r.descriptor.supercompression_scheme == SupercompressionScheme.ZLib
    assert r.data == compressed_data
