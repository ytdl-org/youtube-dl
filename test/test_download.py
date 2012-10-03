#!/usr/bin/env python2
import unittest
import hashlib
import os

from youtube_dl.FileDownloader import FileDownloader
from youtube_dl.InfoExtractors  import YoutubeIE

class DownloadTest(unittest.TestCase):
	#calculated with md5sum:
	#	md5sum (GNU coreutils) 8.19
	YOUTUBE_MD5 = "8547978241cb87dd6782b10b8e90acc3"
	YOUTUBE_URL = "http://www.youtube.com/watch?v=BaW_jenozKc"
	YOUTUBE_FILE = "BaW_jenozKc.flv"

	def test_youtube(self):
		#let's download a file from youtube
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
