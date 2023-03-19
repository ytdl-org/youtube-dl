import sys


if sys.version[0:3] > '3.5' and sys.version[0:3] < '4.0':
    import unittest
    import yourbase

    yourbase.attach(unittest)