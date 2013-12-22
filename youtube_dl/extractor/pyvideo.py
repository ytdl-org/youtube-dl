import re
import os

from .common import InfoExtractor


class PyvideoIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?pyvideo\.org/video/(?P<id>\d+)/(.*)'
    _TESTS = [{
        u'url': u'http://pyvideo.org/video/1737/become-a-logging-expert-in-30-minutes',
        u'file': u'24_4WWkSmNo.mp4',
        u'md5': u'de317418c8bc76b1fd8633e4f32acbc6',
        u'info_dict': {
            u"title": u"Become a logging expert in 30 minutes",
            u"description": u"md5:9665350d466c67fb5b1598de379021f7",
            u"upload_date": u"20130320",
            u"uploader": u"NextDayVideo",
            u"uploader_id": u"NextDayVideo",
        },
        u'add_ie': ['Youtube'],
    },
    {
        u'url': u'http://pyvideo.org/video/2542/gloriajw-spotifywitherikbernhardsson182m4v',
        u'md5': u'5fe1c7e0a8aa5570330784c847ff6d12',
        u'info_dict': {
            u'id': u'2542',
            u'ext': u'm4v',
            u'title': u'Gloriajw-SpotifyWithErikBernhardsson182',
        },
    },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        m_youtube = re.search(r'(https?://www\.youtube\.com/watch\?v=.*)', webpage)

        if m_youtube is not None:
            return self.url_result(m_youtube.group(1), 'Youtube')

        title = self._html_search_regex(r'<div class="section">.*?<h3>([^>]+?)</h3>',
            webpage, u'title', flags=re.DOTALL)
        video_url = self._search_regex([r'<source src="(.*?)"',
            r'<dt>Download</dt>.*?<a href="(.+?)"'],
            webpage, u'video url', flags=re.DOTALL)
        return {
            'id': video_id,
            'title': os.path.splitext(title)[0],
            'url': video_url,
        }
