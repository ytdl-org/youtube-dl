from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class DFBIE(InfoExtractor):
    IE_NAME = 'tv.dfb.de'
    _VALID_URL = r'https?://tv\.dfb\.de/video/(?P<display_id>[^/]+)/(?P<id>\d+)'

    _TEST = {
        'url': 'http://tv.dfb.de/video/u-19-em-stimmen-zum-spiel-gegen-russland/11633/',
        # The md5 is different each time
        'info_dict': {
            'id': '11633',
            'display_id': 'u-19-em-stimmen-zum-spiel-gegen-russland',
            'ext': 'flv',
            'title': 'U 19-EM: Stimmen zum Spiel gegen Russland',
            'upload_date': '20150714',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)
        player_info = self._download_xml(
            'http://tv.dfb.de/server/hd_video.php?play=%s' % video_id,
            display_id)
        video_info = player_info.find('video')

        f4m_info = self._download_xml(
            self._proto_relative_url(video_info.find('url').text.strip()), display_id)
        token_el = f4m_info.find('token')
        manifest_url = token_el.attrib['url'] + '?' + 'hdnea=' + token_el.attrib['auth'] + '&hdcore=3.2.0'
        formats = self._extract_f4m_formats(manifest_url, display_id)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': video_info.find('title').text,
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': unified_strdate(video_info.find('time_date').text),
            'formats': formats,
        }
