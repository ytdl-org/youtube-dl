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

        video_url = self._html_search_regex(r'<video[^>]*>\s*<source[^>]*>\s*<source src="(?P<url>[^"]+)"',
            webpage, u'video URL', flags=re.DOTALL)

        title = self._html_search_regex((r"<h1 class='player_page_h1'.*?>(?P<title>.*?)</h1>",
            r'<title>(?P<title>[^<]+?)</title>'), webpage, 'title', flags=re.DOTALL)

        video_description = self._html_search_regex(r'<meta property="og:description" content="(?P<desc>.*?)"',
            webpage, u'description', fatal=False, flags=re.DOTALL)

        info = {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': video_description,
        }
        return [info]
