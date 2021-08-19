from gcf.blob import BlobResourceDescriptor
import os
from . import ResourceDescriptor, ResourceType, Header
from .image import ImageResourceDescriptor, MipLevelDescriptor


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


def skip_resources(f, n: int, header: Header):
    """Skip the given number of resources from file."""
    for _ in range(n):
        descriptor = ResourceDescriptor.from_file(f, header)
        f.seek(descriptor.size, os.SEEK_CUR)


def decode_resource_descriptor(descriptor: ResourceDescriptor):
    """Convert a generic resource descriptor into a more specific one depending on the resource type."""
    if descriptor.resource_type == ResourceType.Image:
        return ImageResourceDescriptor.from_resource_descriptor(descriptor)
    elif descriptor.resource_type == ResourceType.Blob:
        return BlobResourceDescriptor.from_resource_descriptor(descriptor)

    return descriptor


def skip_mip_levels(f, n: int):
    """Skip the given number of mip levels from file."""
    for _ in range(n):
        descriptor = MipLevelDescriptor.from_file(f)
        f.seek(descriptor.compressed_size, os.SEEK_CUR)
