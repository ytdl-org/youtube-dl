import unittest
import os.path

import youtube_dl


class TikTokTestYoutubeDl(unittest.TestCase):
    def test_meta_data(self):
        url = 'https://www.tiktok.com/@oriangaon/video/6807126376001441030'
        params = {}
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertEquals(info['id'], '6807126376001441030')
        self.assertEquals(info['url'], 'https://www.tiktok.com/@oriangaon/video/6807126376001441030')
        self.assertEquals(info['title'], '#foryou #foyou Mmmmm....,,')
        self.assertEquals(info['uploader'], 'Oriangaon')
        self.assertEquals(info['timestamp'], 1584907616)
        self.assertEquals(info['thumbnail'],
                          'https://p16-va-default.akamaized.net/obj/tos-maliva-p-0068/d1a8fbd3e42dda3a1baa01ee9edad289')
        self.assertGreaterEqual(info['view_count'], 79864)
        self.assertEquals(info['uploader_id'], '6772113344733955077')
        self.assertFalse(info['is_live'])
        self.assertEquals(info['live_status'], 'not_live')
        self.assertGreaterEqual(info['like_count'], 2213)
        self.assertGreaterEqual(info['share_count'], 109)
        self.assertGreaterEqual(info['comment_count'], 40)
        self.assertEquals(info['duration'], 10)
        self.assertEquals(info['ext'], 'mp.4')
        self.assertGreater(len(info['embed_code']),0)

    def test_download_video(self):
        url = 'https://www.tiktok.com/@ballislife/video/6783617809113943301'
        params = {}
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=True)
        self.assertTrue(os.path.exists("Imagine lebron freaking out over something you did! #foryou #ballislife #lebron #nba-6783617809113943301.mp.4"))




if __name__ == '__main__':
    unittest.main()
