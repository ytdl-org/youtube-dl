import re

from .common import InfoExtractor

class HentaiStigmaIE(InfoExtractor):
    _VALID_URL = r'^https?://hentai\.animestigma\.com/(?P<videoid>[^/]+)'
    _TEST = {
        u'url': u'http://hentai.animestigma.com/inyouchuu-etsu-bonus/',
        u'file': u'inyouchuu-etsu-bonus.mp4',
        u'md5': u'4e3d07422a68a4cc363d8f57c8bf0d23',
        u'info_dict': {
            u"title": u"Inyouchuu Etsu Bonus",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        # Get the video title
        video_title = self._html_search_regex(r'<h2 class="posttitle"><a[^>]*>([^<]+)</a>',
            webpage, u'title').strip()

        # Get the wrapper url
        wrap_url = self._html_search_regex(r'<iframe src="([^"]+mp4)"', webpage, u'wrapper url')

        # Get wrapper content
        wrap_webpage = self._download_webpage(wrap_url, video_id)

        video_url = self._html_search_regex(r'clip:\s*{\s*url: "([^"]*)"', wrap_webpage, u'video url')

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'format': 'mp4',
                'age_limit': 18}

        return [info]
