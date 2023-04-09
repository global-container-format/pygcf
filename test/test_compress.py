import pytest

from gcf.compress import *


@pytest.mark.parametrize("compression_algorithm", tuple(COMPRESSOR_TABLE.keys()))
def test_compress_cycle(compression_algorithm):
    compressor, decompressor = COMPRESSOR_TABLE[compression_algorithm]
    original_data = bytes(range(128))
    compressed_data = compressor(original_data)
    decompressed_data = decompressor(compressed_data)

    assert decompressed_data == original_data
