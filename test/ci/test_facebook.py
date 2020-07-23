import unittest
import youtube_dl
from youtube_dl.utils import DownloadError


class facebookMetaData(unittest.TestCase):
    def test_likes_metadata(self):
        params = {}
        url = "https://www.facebook.com/iihfhockey/videos/2742345396033296/"
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertGreater(info.get('like_count'), 200)

    def test_reactions_metadata(self):
        params = {}
        url = "https://www.facebook.com/supercarblondie/videos/519426815548240/"
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertGreater(info.get('reactions_count'), 1000000)
        self.assertGreater(info.get('like_count'), 800000)

    def test_comments_live_video(self):
        params = {}
        url = "https://www.facebook.com/Medianetlive/videos/676754012901513/"
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertGreater(info.get('comment_count'), 0)

    def test_meta_data(self):
        params = {}
        url = "https://www.facebook.com/parapsychological.centr/videos/177407933624543/"
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        self.assertGreater(info.get('comment_count'), 0)

    def test_metadata_fetch_with_log_in(self):
        url = "https://www.facebook.com/oristandup/videos/675360549895283"
        params = {}
        with open("cookie_file") as file:
            proxy = "ec2-3-221-82-67.compute-1.amazonaws.com:3128"
            params['cookiefile'] = file.name
            params['proxy'] = proxy
            ydl = youtube_dl.YoutubeDL(params)
            info = ydl.extract_info(url, download=False)
            print (info.get('title'))
            print (info.get('timestamp'))
            self.assertTrue(info.get('timestamp'))
            self.assertTrue(info.get('view_count'))
            self.assertTrue(info.get('comment_count'))
            self.assertTrue(info.get('width'))
            self.assertTrue(info.get('uploader_id'))
            self.assertTrue(info.get('thumbnail'))

    def test_unavailable_video(self):
        url = "https://www.facebook.com/101457238278830/videos/287839102599521/"
        params = {}
        with open("cookie_file") as file:
            try:
                proxy = "ec2-3-221-82-67.compute-1.amazonaws.com:3128"
                params['cookiefile'] = file.name
                params['proxy'] = proxy
                ydl = youtube_dl.YoutubeDL(params)
                info = ydl.extract_info(url, download=False)
            except DownloadError:
                self.assertRaises(DownloadError)

    def test_paid_videos_timestamp(self):
        params = {}
        url = "https://www.facebook.com/148456285190063/videos/307226959975478"
        ydl = youtube_dl.YoutubeDL(params)
        info = ydl.extract_info(url, download=False)
        print (info.get('timestamp'))
        self.assertTrue(info.get('timestamp'))



if __name__ == '__main__':
    unittest.main()
