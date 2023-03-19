import sys
import platform

print(platform.python_implementation())

if sys.version[0:3] > '3.5' and sys.version[0:3] < '4.0' and platform.python_implementation() != 'pypy':
    import unittest
    import yourbase

    yourbase.attach(unittest)