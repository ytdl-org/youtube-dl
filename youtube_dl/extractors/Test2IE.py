
# Is that actually needed?, if I comment it, it doesn't fail in python2.6 or python2.7
#from __future__ import absolute_import

from .ie import *

class Test2IE(BaseIETest):
    IE_NAME = 'Test2'
