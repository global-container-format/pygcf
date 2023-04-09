from gcf import ContainerFlags, Header, Resource, ResourceDescriptor, ResourceType
from gcf.vulkan import Format


class MyResource(Resource):
    def __init__(self, descriptor: ResourceDescriptor, data_length=16):
        super().__init__(descriptor)

        self.data_length = data_length

    @property
    def content_data(self) -> bytes:
        return bytes(range(self.data_length))


def test_init():
    h = Header(1)
    d = ResourceDescriptor(ResourceType.Test, Format.UNDEFINED, 16, header=h)
    r = MyResource(d)

    assert r.descriptor == d


def test_serialize_without_padding():
    h = Header(1)
    d = ResourceDescriptor(ResourceType.Test, Format.UNDEFINED, 16, header=h)
    r = MyResource(d)

    raw_descriptor = d.serialize()
    raw_resource = r.serialize()

    assert raw_resource == raw_descriptor + r.content_data


def test_serialize_with_padding():
    h = Header(1)
    d = ResourceDescriptor(ResourceType.Test, Format.UNDEFINED, 15, header=h)
    r = MyResource(d, data_length=15)

    raw_descriptor = d.serialize()
    raw_resource = r.serialize()

    assert raw_resource == raw_descriptor + r.content_data + b'\0'


def test_serialize_unpadded():
    h = Header(1, flags=[ContainerFlags.Unpadded])
    d = ResourceDescriptor(ResourceType.Test, Format.UNDEFINED, 15, header=h)
    r = MyResource(d, data_length=15)

    raw_descriptor = d.serialize()
    raw_resource = r.serialize()

    assert raw_resource == raw_descriptor + r.content_data
