from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DFBIE(InfoExtractor):
    IE_NAME = 'tv.dfb.de'
    _VALID_URL = r'https?://tv\.dfb\.de/video/[^/]+/(?P<id>\d+)'

    _TEST = {
        'url': 'http://tv.dfb.de/video/highlights-des-empfangs-in-berlin/9070/',
        # The md5 is different each time
        'info_dict': {
            'id': '9070',
            'ext': 'flv',
            'title': 'Highlights des Empfangs in Berlin',
            'upload_date': '20140716',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        player_info = self._download_xml(
            'http://tv.dfb.de/server/hd_video.php?play=%s' % video_id,
            video_id)
        video_info = player_info.find('video')

        f4m_info = self._download_xml(self._proto_relative_url(video_info.find('url').text.strip()), video_id)
        token_el = f4m_info.find('token')
        manifest_url = token_el.attrib['url'] + '?' + 'hdnea=' + token_el.attrib['auth'] + '&hdcore=3.2.0'

        return {
            'id': video_id,
            'title': video_info.find('title').text,
            'url': manifest_url,
            'ext': 'flv',
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': ''.join(video_info.find('time_date').text.split('.')[::-1]),
        }
