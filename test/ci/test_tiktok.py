import unittest
import youtube_dl


class TikTokTestYoutubeDl(unittest.TestCase):
    def test_meta_data(self):
        url = 'https://www.tiktok.com/@danieltbraun/video/6817099671043853574'
        params = {}
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertEquals(info['share_count'], 110)



if __name__ == '__main__':
    unittest.main()
