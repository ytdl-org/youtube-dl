#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
from time import sleep

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.archive import Archive


class TestArchive(unittest.TestCase):
    def setUp(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        test_archive = os.path.join(cur_dir, "test_archive.txt")
        self.archive = Archive(test_archive)

    def tearDown(self):
        if os.path.exists(self.archive.filepath):
            os.remove(self.archive.filepath)

    def test_archive_disabled(self):
        self.assertTrue(Archive(None)._disabled)
        self.assertTrue(Archive("")._disabled)
        self.assertFalse(Archive("/anything")._disabled)

    def test_archive_read_empty_file(self):
        self.archive._read_file()

    def test_archive_exists(self):
        self.archive.record_download("dl_id")
        self.assertTrue("dl_id" in self.archive._data)
        self.assertTrue("dl_id" in self.archive)

    def test_archive_not_exists(self):
        self.assertFalse("dl_id" in self.archive)

    def test_archive_multiple_writes(self):
        self.archive.record_download("dl_id 1")
        self.archive.record_download("dl_id 2")
        self.archive.record_download("dl_id 3")
        expected = "dl_id 1" + "\n" + "dl_id 2" + "\n" + "dl_id 3" + "\n"
        with open(self.archive.filepath, "r", encoding="utf-8") as f_in:
            self.assertEqual(f_in.read(), expected)


if __name__ == "__main__":
    unittest.main()
