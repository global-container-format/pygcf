def align_size(orig_size: int, alignment: int) -> int:
    assert not (alignment & (alignment - 1)) # must be power of 2

    mask = alignment - 1

    return (orig_size + mask) & ~mask


def compute_mip_level_size(mip_level: int, base_width: int, base_height: int, base_depth: int):
    mip_level_resize_factor = compute_mip_level_resize_factor(mip_level)
    f = lambda x: round(max(1, x * mip_level_resize_factor))

    return f(base_width), f(base_height), f(base_depth)


def compute_mip_level_resize_factor(mip_level: int):
    return 0.5 ** (mip_level - 1)
