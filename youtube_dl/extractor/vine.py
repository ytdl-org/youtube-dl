import re

from .common import InfoExtractor


class VineIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?vine\.co/v/(?P<id>\w+)'
    _TEST = {
        u'url': u'https://vine.co/v/b9KOOWX7HUx',
        u'file': u'b9KOOWX7HUx.mp4',
        u'md5': u'2f36fed6235b16da96ce9b4dc890940d',
        u'info_dict': {
            u"uploader": u"Jack Dorsey", 
            u"title": u"Chicken."
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'https://vine.co/v/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'<meta property="twitter:player:stream" content="(.+?)"',
            webpage, u'video URL')

        uploader = self._html_search_regex(r'<p class="username">(.*?)</p>',
            webpage, u'uploader', fatal=False, flags=re.DOTALL)

        return [{
            'id':        video_id,
            'url':       video_url,
            'ext':       'mp4',
            'title':     self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader':  uploader,
        }]
