"""
GCF resource compression and decompression.
"""
import zlib

from . import SupercompressionScheme


def compress_deflate(data, level=6):
    """Deflate compression function."""
    compressor = zlib.compressobj(level, wbits=-15)
    compressed_data = compressor.compress(data)
    compressed_data += compressor.flush()

    return compressed_data


def decompress_deflate(data):
    """Deflate decompression function."""
    return zlib.decompress(data, wbits=-15)


def compress_zlib(data, level=6):
    """ZLib compression function."""
    compressor = zlib.compressobj(level, wbits=15)

    data = compressor.compress(data)
    data += compressor.flush()

    return data


def decompress_zlib(data):
    """ZLib decompression function."""
    return zlib.decompress(data, wbits=15)


def compress_identity(data, level=None): # pylint: disable=unused-argument
    """Identity compression function.

    Will return the input data. Any other argument is ignored.
    """
    return data


def decompress_identity(data):
    """Identity decompression function.

    Will return the input data.
    """
    return data


COMPRESSOR_TABLE = {
    SupercompressionScheme.NO_COMPRESSION: (compress_identity, decompress_identity),
    SupercompressionScheme.ZLIB: (compress_zlib, decompress_zlib),
    SupercompressionScheme.DEFLATE: (compress_deflate, decompress_deflate),
    # Deflate chosen to minimize test data size. Doesn't make any difference
    # as "test" is not a valid supercompression scheme
    SupercompressionScheme.TEST: (compress_deflate, decompress_deflate),
}
