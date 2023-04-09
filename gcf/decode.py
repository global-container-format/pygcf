from gcf.blob import BlobResourceDescriptor

from . import ResourceDescriptor, ResourceType
from .image import ImageResourceDescriptor


def decode_resource_descriptor(descriptor: ResourceDescriptor):
    """Convert a generic resource descriptor into a more specific one depending on the resource type."""
    if descriptor.resource_type == ResourceType.Image:
        return ImageResourceDescriptor.from_resource_descriptor(descriptor)
    elif descriptor.resource_type == ResourceType.Blob:
        return BlobResourceDescriptor.from_resource_descriptor(descriptor)

    return descriptor
