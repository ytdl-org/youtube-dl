# Here should go the real base InfoExtractor class and all the modules needed.

from ..utils import *

class BaseIETest(object):
    @classmethod
    def test(cls):
        print(cls.__name__ +' is a subclass of BaseIETest')
