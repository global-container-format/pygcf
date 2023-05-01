"""
GCF resource compression and decompression.
"""
import zlib
from enum import IntEnum, unique


@unique
class SupercompressionScheme(IntEnum):
    """Supported standard supercompression schemes."""

    NO_COMPRESSION = 0
    ZLIB = 1
    DEFLATE = 2
    TEST = 0xFFFF


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


def compress_identity(data, level=None):  # pylint: disable=unused-argument
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
    SupercompressionScheme.NO_COMPRESSION.value: (compress_identity, decompress_identity),
    SupercompressionScheme.ZLIB.value: (compress_zlib, decompress_zlib),
    SupercompressionScheme.DEFLATE.value: (compress_deflate, decompress_deflate),
    # Arbitrarily chosen for testing this library
    SupercompressionScheme.TEST.value: (compress_deflate, decompress_deflate),
}


def compress(data: bytes, supercompression_scheme: int) -> bytes:
    """Compress data by using one of the registered supercompression schemes.

    :param data: The uncompressed data.
    :param supercompression_scheme: The supercompression scheme ID.

    :returns: The compressed data.
    """

    try:
        compressor, _ = COMPRESSOR_TABLE[supercompression_scheme]
    except KeyError as exc:
        raise ValueError("Unknown supercompression scheme", supercompression_scheme) from exc

    return compressor(data)


def decompress(data: bytes, supercompression_scheme: int) -> bytes:
    """Decompress data by using one of the registered supercompression schemes.

    :param data: The compressed data.
    :param supercompression_scheme: The supercompression scheme ID.

    :returns: The decompressed data.
    """

    try:
        _, decompressor = COMPRESSOR_TABLE[supercompression_scheme]
    except KeyError as exc:
        raise ValueError("Unknown supercompression scheme", supercompression_scheme) from exc

    return decompressor(data)
