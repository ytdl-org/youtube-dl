from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate



class TheChiveIE(InfoExtractor):
    _VALID_URL = r'http://(www\.)?thechive\.com/[^/]+/[^/]+/[^/]+/(?P<video_id>[A-Za-z\-]+)'
    _TEST = {
        'url': "http://thechive.com/2015/02/20/so-thats-what-a-set-of-redneck-bagpipes-sound-like-video/",
        'md5': "366710dda77cfa727bdef3523ba8466f",
        'info_dict': {
            'id': "so-thats-what-a-set-of-redneck-bagpipes-sound-like-video",
            'title': "So that's what a set of redneck bagpipes sound like... (Video)",
            'description': "Okay that was pretty good. Now play Freebird!...",
            'thumbnail': "https://thechive.files.wordpress.com/2015/02/0_07dghz0w-thumbnail2.jpg",
            'author': "Ben",
            'upload_date': "20150220",
            'ext': "mp4"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._html_search_regex(r'(?s)<meta name="description" content="(.*?)" />', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage)
        author = self._html_search_regex(
            r'(?s)itemprop="author">(.+?)</span>', webpage, 'author', fatal=False).capitalize() 
        upload_date = unified_strdate(self._html_search_regex(
            r'(?s)itemprop="datePublished" datetime="(.+?)">', webpage, 'upload_date', fatal=False))

        # Adapted from extractor/musicvault.py
        VIDEO_URL_TEMPLATE = 'http://cdnapi.kaltura.com/p/%(uid)s/sp/%(wid)s/playManifest/entryId/%(entry_id)s/format/url/protocol/http'

        kaltura_id = self._search_regex(
            r'entry_id=([^"]+)',
            webpage, 'kaltura ID')
        video_url = VIDEO_URL_TEMPLATE % {
            'entry_id': kaltura_id,
            'wid': self._search_regex(r'partner_id/([0-9]+)\?', webpage, 'wid'),
            'uid': self._search_regex(r'uiconf_id/([0-9]+)/', webpage, 'uid'),
        }

        return {
            'url': video_url,
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'author': author,
            'upload_date': upload_date,
            'ext': 'mp4'
        }