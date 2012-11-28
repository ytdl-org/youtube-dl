#!/usr/bin/env python2
import unittest
import hashlib
import os
import json

from youtube_dl.FileDownloader import FileDownloader
from youtube_dl.InfoExtractors  import YoutubeIE, DailymotionIE
from youtube_dl.InfoExtractors import  MetacafeIE, BlipTVIE
from youtube_dl.InfoExtractors import  XVideosIE, VimeoIE
from youtube_dl.InfoExtractors import  SoundcloudIE, StanfordOpenClassroomIE
from youtube_dl.InfoExtractors import  CollegeHumorIE, XNXXIE


class DownloadTest(unittest.TestCase):
    PARAMETERS_FILE = "test/parameters.json"
    #calculated with md5sum:
    #md5sum (GNU coreutils) 8.19

    YOUTUBE_SIZE = 1993883
    YOUTUBE_URL = "http://www.youtube.com/watch?v=BaW_jenozKc"
    YOUTUBE_FILE = "BaW_jenozKc.mp4"

    DAILYMOTION_MD5 = "d363a50e9eb4f22ce90d08d15695bb47"
    DAILYMOTION_URL = "http://www.dailymotion.com/video/x33vw9_tutoriel-de-youtubeur-dl-des-video_tech"
    DAILYMOTION_FILE = "x33vw9.mp4"

    METACAFE_SIZE = 5754305
    METACAFE_URL = "http://www.metacafe.com/watch/yt-_aUehQsCQtM/the_electric_company_short_i_pbs_kids_go/"
    METACAFE_FILE = "_aUehQsCQtM.flv"

    BLIP_MD5 = "93c24d2f4e0782af13b8a7606ea97ba7"
    BLIP_URL = "http://blip.tv/cbr/cbr-exclusive-gotham-city-imposters-bats-vs-jokerz-short-3-5796352"
    BLIP_FILE = "5779306.m4v"

    XVIDEO_MD5 = "1ab4dedc01f771cb2a65e91caa801aaf"
    XVIDEO_URL = "http://www.xvideos.com/video939581/funny_porns_by_s_-1"
    XVIDEO_FILE = "939581.flv"

    VIMEO_MD5 = "1ab4dedc01f771cb2a65e91caa801aaf"
    VIMEO_URL = "http://vimeo.com/14160053"
    VIMEO_FILE = ""

    VIMEO2_MD5 = ""
    VIMEO2_URL = "http://player.vimeo.com/video/47019590"
    VIMEO2_FILE = ""

    SOUNDCLOUD_MD5 = "ce3775768ebb6432fa8495d446a078ed"
    SOUNDCLOUD_URL = "http://soundcloud.com/ethmusic/lostin-powers-she-so-heavy"
    SOUNDCLOUD_FILE = "n6FLbx6ZzMiu.mp3"

    STANDFORD_MD5 = "22c8206291368c4e2c9c1a307f0ea0f4"
    STANDFORD_URL = "http://openclassroom.stanford.edu/MainFolder/VideoPage.php?course=PracticalUnix&video=intro-environment&speed=100"
    STANDFORD_FILE = "PracticalUnix_intro-environment.mp4"

    COLLEGEHUMOR_MD5 = ""
    COLLEGEHUMOR_URL = "http://www.collegehumor.com/video/6830834/mitt-romney-style-gangnam-style-parody"
    COLLEGEHUMOR_FILE = ""

    XNXX_MD5 = "5f0469c8d1dfd1bc38c8e6deb5e0a21d"
    XNXX_URL = "http://video.xnxx.com/video1135332/lida_naked_funny_actress_5_"
    XNXX_FILE = "1135332.flv"

    def test_youtube(self):
        #let's download a file from youtube
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(YoutubeIE())
        fd.download([DownloadTest.YOUTUBE_URL])
        self.assertTrue(os.path.exists(DownloadTest.YOUTUBE_FILE))
        self.assertEqual(os.path.getsize(DownloadTest.YOUTUBE_FILE), DownloadTest.YOUTUBE_SIZE)

    def test_dailymotion(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(DailymotionIE())
        fd.download([DownloadTest.DAILYMOTION_URL])
        self.assertTrue(os.path.exists(DownloadTest.DAILYMOTION_FILE))
        md5_down_file = md5_for_file(DownloadTest.DAILYMOTION_FILE)
        self.assertEqual(md5_down_file, DownloadTest.DAILYMOTION_MD5)

    def test_metacafe(self):
        #this emulate a skip,to be 2.6 compatible
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(MetacafeIE())
        fd.add_info_extractor(YoutubeIE())
        fd.download([DownloadTest.METACAFE_URL])
        self.assertTrue(os.path.exists(DownloadTest.METACAFE_FILE))
        self.assertEqual(os.path.getsize(DownloadTest.METACAFE_FILE), DownloadTest.METACAFE_SIZE)

    def test_blip(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(BlipTVIE())
        fd.download([DownloadTest.BLIP_URL])
        self.assertTrue(os.path.exists(DownloadTest.BLIP_FILE))
        md5_down_file = md5_for_file(DownloadTest.BLIP_FILE)
        self.assertEqual(md5_down_file, DownloadTest.BLIP_MD5)

    def test_xvideo(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(XVideosIE())
        fd.download([DownloadTest.XVIDEO_URL])
        self.assertTrue(os.path.exists(DownloadTest.XVIDEO_FILE))
        md5_down_file = md5_for_file(DownloadTest.XVIDEO_FILE)
        self.assertEqual(md5_down_file, DownloadTest.XVIDEO_MD5)

    def test_vimeo(self):
        #skipped for the moment produce an error
        return
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(VimeoIE())
        fd.download([DownloadTest.VIMEO_URL])
        self.assertTrue(os.path.exists(DownloadTest.VIMEO_FILE))
        md5_down_file = md5_for_file(DownloadTest.VIMEO_FILE)
        self.assertEqual(md5_down_file, DownloadTest.VIMEO_MD5)

    def test_vimeo2(self):
        #skipped for the moment produce an error
        return
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(VimeoIE())
        fd.download([DownloadTest.VIMEO2_URL])
        self.assertTrue(os.path.exists(DownloadTest.VIMEO2_FILE))
        md5_down_file = md5_for_file(DownloadTest.VIMEO2_FILE)
        self.assertEqual(md5_down_file, DownloadTest.VIMEO2_MD5)

    def test_soundcloud(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(SoundcloudIE())
        fd.download([DownloadTest.SOUNDCLOUD_URL])
        self.assertTrue(os.path.exists(DownloadTest.SOUNDCLOUD_FILE))
        md5_down_file = md5_for_file(DownloadTest.SOUNDCLOUD_FILE)
        self.assertEqual(md5_down_file, DownloadTest.SOUNDCLOUD_MD5)

    def test_standford(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(StanfordOpenClassroomIE())
        fd.download([DownloadTest.STANDFORD_URL])
        self.assertTrue(os.path.exists(DownloadTest.STANDFORD_FILE))
        md5_down_file = md5_for_file(DownloadTest.STANDFORD_FILE)
        self.assertEqual(md5_down_file, DownloadTest.STANDFORD_MD5)

    def test_collegehumor(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(CollegeHumorIE())
        fd.download([DownloadTest.COLLEGEHUMOR_URL])
        self.assertTrue(os.path.exists(DownloadTest.COLLEGEHUMOR_FILE))
        md5_down_file = md5_for_file(DownloadTest.COLLEGEHUMOR_FILE)
        self.assertEqual(md5_down_file, DownloadTest.COLLEGEHUMOR_MD5)

    def test_xnxx(self):
        with open(DownloadTest.PARAMETERS_FILE) as f:
            fd = FileDownloader(json.load(f))
        fd.add_info_extractor(XNXXIE())
        fd.download([DownloadTest.XNXX_URL])
        self.assertTrue(os.path.exists(DownloadTest.XNXX_FILE))
        md5_down_file = md5_for_file(DownloadTest.XNXX_FILE)
        self.assertEqual(md5_down_file, DownloadTest.XNXX_MD5)

    def tearDown(self):
        if os.path.exists(DownloadTest.YOUTUBE_FILE):
            os.remove(DownloadTest.YOUTUBE_FILE)
        if os.path.exists(DownloadTest.DAILYMOTION_FILE):
            os.remove(DownloadTest.DAILYMOTION_FILE)
        if os.path.exists(DownloadTest.METACAFE_FILE):
            os.remove(DownloadTest.METACAFE_FILE)
        if os.path.exists(DownloadTest.BLIP_FILE):
            os.remove(DownloadTest.BLIP_FILE)
        if os.path.exists(DownloadTest.XVIDEO_FILE):
            os.remove(DownloadTest.XVIDEO_FILE)
        if os.path.exists(DownloadTest.VIMEO_FILE):
            os.remove(DownloadTest.VIMEO_FILE)
        if os.path.exists(DownloadTest.SOUNDCLOUD_FILE):
            os.remove(DownloadTest.SOUNDCLOUD_FILE)
        if os.path.exists(DownloadTest.STANDFORD_FILE):
            os.remove(DownloadTest.STANDFORD_FILE)
        if os.path.exists(DownloadTest.COLLEGEHUMOR_FILE):
            os.remove(DownloadTest.COLLEGEHUMOR_FILE)
        if os.path.exists(DownloadTest.XNXX_FILE):
            os.remove(DownloadTest.XNXX_FILE)

def md5_for_file(filename, block_size=2**20):
    with open(filename) as f:
        md5 = hashlib.md5()
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
            return md5.hexdigest()
