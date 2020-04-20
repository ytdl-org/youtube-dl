import unittest
import youtube_dl


class TikTokTestYoutubeDl(unittest.TestCase):
    def test_meta_data(self):
        url = 'https://www.tiktok.com/@danieltbraun/video/6817099671043853574'
        params = {}
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertEquals(info['title'], "She got a face full of DUSTBIN #foryou")


if __name__ == '__main__':
    unittest.main()
