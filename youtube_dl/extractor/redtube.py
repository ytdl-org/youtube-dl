import re

from .common import InfoExtractor


class RedTubeIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?redtube\.com/(?P<id>[0-9]+)'
    _TEST = {
        u'url': u'http://www.redtube.com/66418',
        u'file': u'66418.mp4',
        u'md5': u'7b8c22b5e7098a3e1c09709df1126d2d',
        u'info_dict': {
            u"title": u"Sucked on a toilet",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        video_extension = 'mp4'
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(
            r'<source src="(.+?)" type="video/mp4">', webpage, u'video URL')

        video_title = self._html_search_regex(
            r'<h1 class="videoTitle slidePanelMovable">(.+?)</h1>',
            webpage, u'title')

        # No self-labeling, but they describe themselves as
        # "Home of Videos Porno"
        age_limit = 18

        return {
            'id':        video_id,
            'url':       video_url,
            'ext':       video_extension,
            'title':     video_title,
            'age_limit': age_limit,
        }
