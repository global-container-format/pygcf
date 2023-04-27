"""
Utilities.
"""
from typing import Tuple


def compute_mip_level_size(mip_level: int, base_width: int, base_height: int, base_depth: int) -> Tuple[int, int, int]:
    """Compute the mip level size.

    Compute the factor used to multiply the base image size to obtain the
    given mip level size.

    :param mip_level: The desired mip level.
    :param base_width: The width of the base image size.
    :param base_height: The height of the base image size.
    :param base_depth: The depth of the base image size.

    :returns: A tuple containing the mip level width, height and depth.
    """
    mip_level_resize_factor = compute_mip_level_resize_factor(mip_level)

    def scale_size(base_size: int) -> int:
        return round(max(1, base_size * mip_level_resize_factor))

    return scale_size(base_width), scale_size(base_height), scale_size(base_depth)


def compute_mip_level_resize_factor(mip_level: int):
    """Compute the mip level resize factor.

    Compute the factor used to multiply the base image size to obtain the
    given mip level size.
    """
    return 0.5**mip_level
