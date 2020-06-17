import unittest
import youtube_dl


class facebookMetaData(unittest.TestCase):
    def test_metadata_fetch(self):
        params = {}
        url = "https://www.facebook.com/iihfhockey/videos/2742345396033296/"
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertTrue(info.has_key('like_count'))
        self.assertTrue(info.has_key('reactions_count'))

    def _test_metadata_fetch_with_log_in(self):
        url = "https://www.facebook.com/iihfhockey/videos/2742345396033296/"
        params = {}
        with open("cookie_file") as file:
            proxy = "ec2-35-175-164-238.compute-1.amazonaws.com:3128"
            params['cookiefile'] = file.name
            params['proxy'] = proxy
            ydl = youtube_dl.YoutubeDL(params)
            info = ydl.extract_info(url, download=False)
            self.assertTrue(info.get('timestamp'))
            self.assertTrue(info.get('view_count'))
            self.assertTrue(info.get('width'))
            self.assertTrue(info.get('uploader_id'))
            self.assertTrue(info.get('thumbnail'))


if __name__ == '__main__':
    unittest.main()
