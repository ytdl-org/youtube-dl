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
        self.assertEquals(info['webpage_url'], 'https://www.tiktok.com/@oriangaon/video/6807126376001441030')
        self.assertEquals(info['title'], '#foryou #foyou Mmmmm....,,')
        self.assertEquals(info['uploader'], 'Oriangaon')
        self.assertEquals(info['timestamp'], 1584907616)
        self.assertTrue(info['thumbnail'])
        self.assertGreaterEqual(info['view_count'], 79864)
        self.assertEquals(info['uploader_id'], '6772113344733955077')
        self.assertFalse(info['is_live'])
        self.assertEquals(info['live_status'], 'not_live')
        self.assertGreaterEqual(info['like_count'], 2213)
        self.assertGreaterEqual(info['share_count'], 109)
        self.assertGreaterEqual(info['comment_count'], 40)
        self.assertEquals(info['duration'], 10)
        self.assertEquals(info['ext'], 'mp4')
        self.assertGreater(len(info['embed_code']),0)
        self.assertGreaterEqual(info['uploader_like_count'], 1357)
        self.assertEqual(info['uploader_url'], "https://www.tiktok.com/@oriangaon")

    def test_download_video(self):
        url = 'https://www.tiktok.com/@ballislife/video/6783617809113943301'
        params = {}
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=True)
        file_name="Imagine lebron freaking out over something you did! #foryou #ballislife #lebron #nba-6783617809113943301.mp4"
        self.assertTrue(os.path.exists(file_name))
        os.remove(file_name)


if __name__ == '__main__':
    unittest.main()
