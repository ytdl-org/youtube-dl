import sys


if sys.version[0:3] > '3.5':
    import unittest
    import yourbase

    yourbase.attach(unittest)