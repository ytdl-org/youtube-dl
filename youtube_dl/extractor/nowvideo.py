import re

from .common import InfoExtractor
from ..utils import compat_urlparse


class NowVideoIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?nowvideo\.ch/video/(?P<id>\w+)'
    _TEST = {
        u'url': u'http://www.nowvideo.ch/video/0mw0yow7b6dxa',
        u'file': u'0mw0yow7b6dxa.flv',
        u'md5': u'f8fbbc8add72bd95b7850c6a02fc8817',
        u'info_dict': {
            u"title": u"youtubedl test video _BaW_jenozKc.mp4"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://www.nowvideo.ch/video/' + video_id
        embed_url = 'http://embed.nowvideo.ch/embed.php?v=' + video_id
        webpage = self._download_webpage(webpage_url, video_id)
        embed_page = self._download_webpage(embed_url, video_id,
            u'Downloading embed page')

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'<h4>(.*)</h4>',
            webpage, u'video title')

        video_key = self._search_regex(r'var fkzd="(.*)";',
            embed_page, u'video key')

        api_call = "http://www.nowvideo.ch/api/player.api.php?file={0}&numOfErrors=0&cid=1&key={1}".format(video_id, video_key)
        api_response = self._download_webpage(api_call, video_id,
            u'Downloading API page')
        video_url = compat_urlparse.parse_qs(api_response)[u'url'][0]

        return [{
            'id':        video_id,
            'url':       video_url,
            'ext':       'flv',
            'title':     video_title,
        }]
