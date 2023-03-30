from __future__ import unicode_literals

import sys
import platform


print("davi logs", sys.version[0:3])
print("davi logs", platform.python_implementation())

if sys.version[0:3] == '3.6':
    import unittest
    import yourbase

    yourbase.attach(unittest)
