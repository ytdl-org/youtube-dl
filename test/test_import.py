import unittest

import sys
import os.path
import subprocess

class TestImport(unittest.TestCase):
    def test_import(self):
        rootDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        subprocess.check_call([sys.executable, '-c', 'import youtube_dl'], cwd=rootDir)

if __name__ == '__main__':
    unittest.main()
