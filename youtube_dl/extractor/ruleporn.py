# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RulepornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ruleporn\.com/(?:[a-z]+(?:-[a-z]+)+)'
    _TEST = {
        'url': 'http://ruleporn.com/brunette-nympho-chick-takes-her-boyfriend-in-every-angle/',
        'md5': '86861ebc624a1097c7c10eaf06d7d505',
        'info_dict': {
            'id': '48212',
            'ext': 'mp4',
            'title': 'Brunette Nympho Chick Takes Her Boyfriend In Every Angle',
        }
    }

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None)

        video_id = self._search_regex(r'http://lovehomeporn.com/embed/([0-9]+)', webpage, 'video_id', fatal=True)
        title = self._search_regex(r'<h2 title="((?:\w|\s|\d)+)">', webpage, 'title', fatal=True)
        info_xml = self._download_xml('http://lovehomeporn.com/media/nuevo/econfig.php?key=%s&rp=true' % video_id, video_id)
        url = info_xml.find('file').text

        return {
            'id': video_id,
            'title': title,
            'url': url,
        }
