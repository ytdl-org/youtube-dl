from __future__ import unicode_literals

import sys
import platform


print("davi logs", sys.version[0:3])
print("davi logs", platform.python_implementation())

import unittest
import yourbase

yourbase.attach(unittest)
