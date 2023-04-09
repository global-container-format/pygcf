import zlib

from . import SupercompressionScheme


def compress_deflate(data, level=6):
    compressor = zlib.compressobj(level, wbits=-15)
    compressed_data = compressor.compress(data)
    compressed_data += compressor.flush()

    return compressed_data


def decompress_deflate(data):
    return zlib.decompress(data, wbits=-15)


def compress_zlib(data, level=6):
    compressor = zlib.compressobj(level, wbits=15)

    data = compressor.compress(data)
    data += compressor.flush()

    return data


def decompress_zlib(data):
    return zlib.decompress(data, wbits=15)


def compress_identity(data, level=None):
    return data


def decompress_identity(data):
    return data


COMPRESSOR_TABLE = {
    SupercompressionScheme.NoCompression: (compress_identity, decompress_identity),
    SupercompressionScheme.ZLib: (compress_zlib, decompress_zlib),
    SupercompressionScheme.Deflate: (compress_deflate, decompress_deflate),
    # Deflate chosen to minimize test data size. Doesn't make any difference as "test" is not a valid supercompression scheme
    SupercompressionScheme.Test: (compress_deflate, decompress_deflate)
}
