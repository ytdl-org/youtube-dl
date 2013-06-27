import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,

    ExtractorError,
)


class Vbox7IE(InfoExtractor):
    """Information Extractor for Vbox7"""
    _VALID_URL = r'(?:http://)?(?:www\.)?vbox7\.com/play:([^/]+)'
    _TEST = {
        u'url': u'http://vbox7.com/play:249bb972c2',
        u'file': u'249bb972c2.flv',
        u'md5': u'9c70d6d956f888bdc08c124acc120cfe',
        u'info_dict': {
            u"title": u"\u0421\u043c\u044f\u0445! \u0427\u0443\u0434\u043e - \u0447\u0438\u0441\u0442 \u0437\u0430 \u0441\u0435\u043a\u0443\u043d\u0434\u0438 - \u0421\u043a\u0440\u0438\u0442\u0430 \u043a\u0430\u043c\u0435\u0440\u0430"
        }
    }

    def _real_extract(self,url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(1)

        redirect_page, urlh = self._download_webpage_handle(url, video_id)
        new_location = self._search_regex(r'window\.location = \'(.*)\';', redirect_page, u'redirect location')
        redirect_url = urlh.geturl() + new_location
        webpage = self._download_webpage(redirect_url, video_id, u'Downloading redirect page')

        title = self._html_search_regex(r'<title>(.*)</title>',
            webpage, u'title').split('/')[0].strip()

        ext = "flv"
        info_url = "http://vbox7.com/play/magare.do"
        data = compat_urllib_parse.urlencode({'as3':'1','vid':video_id})
        info_request = compat_urllib_request.Request(info_url, data)
        info_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        info_response = self._download_webpage(info_request, video_id, u'Downloading info webpage')
        if info_response is None:
            raise ExtractorError(u'Unable to extract the media url')
        (final_url, thumbnail_url) = map(lambda x: x.split('=')[1], info_response.split('&'))

        return [{
            'id':        video_id,
            'url':       final_url,
            'ext':       ext,
            'title':     title,
            'thumbnail': thumbnail_url,
        }]
