import re

from .common import InfoExtractor


class KickStarterIE(InfoExtractor):
    _VALID_URL = r'https?://www\.kickstarter\.com/projects/(?P<id>\d*)/.*'
    _TEST = {
        u"url": u"https://www.kickstarter.com/projects/1404461844/intersection-the-story-of-josh-grant?ref=home_location",
        u"file": u"1404461844.mp4",
        u"md5": u"c81addca81327ffa66c642b5d8b08cab",
        u"info_dict": {
            u"title": u"Intersection: The Story of Josh Grant by Kyle Cowling",
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')
        webpage_src = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'data-video="(.*?)">',
            webpage_src, u'video URL')
        if 'mp4' in video_url:
            ext = 'mp4'
        else:
            ext = 'flv'
        video_title = self._html_search_regex(r"<title>(.*?)</title>",
            webpage_src, u'title').rpartition(u'\u2014 Kickstarter')[0].strip()

        results = [{
                    'id': video_id,
                    'url': video_url,
                    'title': video_title,
                    'ext': ext,
                    }]
        return results
