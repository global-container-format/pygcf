from gcf.util import *


def test_compute_mip_level_size():
    assert compute_mip_level_size(0, 256, 256, 1) == (256, 256, 1)
    assert compute_mip_level_size(1, 256, 256, 1) == (128, 128, 1)
    assert compute_mip_level_size(2, 256, 128, 1) == (64, 32, 1)


def test_compute_mip_level_resize_factor():
    assert compute_mip_level_resize_factor(0) == 1
    assert compute_mip_level_resize_factor(1) == 1 / 2
    assert compute_mip_level_resize_factor(2) == 1 / 4


def test_align_size():
    assert align_size(15, 16) == 16
    assert align_size(257, 256) == 512
    assert align_size(0, 2) == 0
    assert align_size(2, 2) == 2
