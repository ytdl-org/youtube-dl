# flake8: noqa
from __future__ import unicode_literals

import re


class LazyLoadExtractor(object):
    _module = None

    @classmethod
    def ie_key(cls):
        return cls.__name__[:-2]

    def __new__(cls):
        mod = __import__(cls._module, fromlist=(cls.__name__,))
        real_cls = getattr(mod, cls.__name__)
        return real_cls.__new__(real_cls)
