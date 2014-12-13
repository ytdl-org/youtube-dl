# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RestudyIE(InfoExtractor):
    _VALID_URL = r'https://www.restudy.dk/video/play/id/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.restudy.dk/video/play/id/1637',
        # MD5 sum of first 10241 bytes of the video file, as reported by
        # head -c 10241 Leiden-frosteffekt-1637.mp4 | md5sum
        'md5': '4e755c4287f292a1fe5363834a683818',
        'info_dict': {
            'id': '1637',
            'ext': 'mp4',
            'title': 'Leiden-frosteffekt',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        xml_url = (
            'https://www.restudy.dk/awsmedia/SmilDirectory/video_%s.xml'
            % video_id)
        xml = self._download_webpage(xml_url, video_id)

        base = self._search_regex(
            r'<meta base="([^"]+)', xml, 'meta base')
        # TODO: Provide multiple video qualities instead of forcing highest
        filename = self._search_regex(
            r'<video src="mp4:([^"]+_high\.mp4)', xml, 'filename')
        url = '%s%s' % (base, filename)
        title = self._og_search_title(webpage)
        return {
            'id': video_id,
            'title': title,
            'url': url,
            'protocol': 'rtmp',
        }
