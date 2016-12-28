from __future__ import unicode_literals


class JSBase(object):
    def __init__(self, cls=None):
        if cls is None:
            cls = self.__class__

        if cls is JSBase:
            self.prototype = {}
        else:
            super(cls, self).__init__(cls.__bases__[0])
            self.prototype.update(cls.prototype)

    def get_proto_prop(self, prop):
        return self.prototype[prop](self)


class JSObject(JSBase):
    def __init__(self, value=None):
        super(JSObject, self).__init__()
        self.value = value
        self.props = {}

    @staticmethod
    def get_prototype_of(o):
        return 'prototype'

    def has_own_prop(self):
        return 'object has own prop'

    def to_string(self):
        return 'object to string'

    prototype = {'hasOwnProperty': has_own_prop, 'toLocaleString': to_string}
    props = {'prototype ': prototype, 'getPrototypeOf': get_prototype_of}


class JSArray(JSObject):

    def __init__(self, length=0):
        super(JSArray, self).__init__()
        self.value = []
        self.props = {'length': length}

    @staticmethod
    def is_array(arg):
        return 'is array'

    def concat(self):
        return 'concat'

    def join(self):
        return 'join'

    def to_string(self):
        return 'array to string'

    prototype = {'concat': concat, 'join': join, 'toLocaleString': to_string}
    props = {'prototype ': prototype, 'isArray': is_array, 'length': 1}
