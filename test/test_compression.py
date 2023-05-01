import pytest

from gcf.compression import COMPRESSOR_TABLE, compress, decompress


@pytest.mark.parametrize("supercompression_scheme", tuple(COMPRESSOR_TABLE.keys()))
def test_compress_cycle(supercompression_scheme):
    original_data = bytes(range(128))
    compressed_data = compress(original_data, supercompression_scheme)
    decompressed_data = decompress(compressed_data, supercompression_scheme)

    assert decompressed_data == original_data
