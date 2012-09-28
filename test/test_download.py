#!/usr/bin/env python2
import unittest
import hashlib
import os

from youtube_dl.FileDownloader import FileDownloader
from youtube_dl.InfoExtractors  import YoutubeIE

class DownloadTest(unittest.TestCase):
    #calculated with the md5sum utility
    #md5sum (GNU coreutils) 8.19
    YOUTUBE_MD5 = "ba4092da68c9ded8ef3aaace5ffd1860"
    YOUTUBE_URL = "http://www.youtube.com/watch?v=u0VbyYcljx8&feature=related"
    YOUTUBE_FILE = "u0VbyYcljx8.flv"

    def test_youtube(self):
        #let's download a file from youtube
        global YOUTUBE_URL
        fd = FileDownloader({})
        fd.add_info_extractor(YoutubeIE())
        fd.download([DownloadTest.YOUTUBE_URL])
        self.assertTrue(os.path.exists(DownloadTest.YOUTUBE_FILE))
        md5_down_file = md5_for_file(DownloadTest.YOUTUBE_FILE)
        self.assertEqual(md5_down_file, DownloadTest.YOUTUBE_MD5)

    def cleanUp(self):
        if os.path.exists(DownloadTest.YOUTUBE_FILE):
            os.remove(DownloadTest.YOUTUBE_FILE)

def md5_for_file(f, block_size=2**20):
    md5 = hashlib.md5()
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
        return md5.digest()
