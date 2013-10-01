import re

from .common import InfoExtractor


class FunnyOrDieIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?funnyordie\.com/videos/(?P<id>[0-9a-f]+)/.*$'
    _TEST = {
        u'url': u'http://www.funnyordie.com/videos/0732f586d7/heart-shaped-box-literal-video-version',
        u'file': u'0732f586d7.mp4',
        u'md5': u'f647e9e90064b53b6e046e75d0241fbd',
        u'info_dict': {
            u"description": u"Lyrics changed to match the video. Spoken cameo by Obscurus Lupa (from ThatGuyWithTheGlasses.com). Based on a concept by Dustin McLean (DustFilms.com). Performed, edited, and written by David A. Scott.", 
            u"title": u"Heart-Shaped Box: Literal Video Version"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(
            [r'type="video/mp4" src="(.*?)"', r'src="([^>]*?)" type=\'video/mp4\''],
            webpage, u'video URL', flags=re.DOTALL)

        info = {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
        }
        return [info]
