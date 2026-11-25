# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_timestamp,
    url_or_none,
)


class UNOIE(InfoExtractor):
    _VALID_URL = r'https?://media\.un\.org/(?:\w+/)+(?P<id>k\d[\w]+)'
    _TESTS = [{
        'url': 'https://media.un.org/en/asset/k1r/k1r3vy9ikk',
        'md5': '981c41cb283227f079d1e5059fd0d30c',
        'info_dict': {
            'id': '1_r3vy9ikk',
            'ext': 'mp4',
            'title': 'md5:abde2a46d396051535e5e6fd6f627a19',
            'description': 'md5:2cba11ee153ae3e6ae2c629e7c4e39b0',
            'thumbnail': 're:https?://.+/thumbnail/.+',
            'duration': 5768,
            'timestamp': 1625216872,
            'upload_date': '20210702',
            'uploader_id': 'UNWebTV_New_York',
        }
    }, {
        'url': 'https://media.un.org/en/asset/k12/k12gpkg3qx',
        'md5': '5978503ca886a922a0f00cf5a7e82395',
        'info_dict': {
            'id': '1_vohfjqkj',
            'ext': 'mp4',
            'title': '1851st Meeting, 81st session Committee on the Elimination of Discrimination Against Women (CEDAW)',
            'description': 'Informal meeting with NGOs and human rights institutions - 1851st Meeting, 81st session CEDAW',
            'thumbnail': 're:https?://.+/thumbnail/.+',
            'duration': 3502,
            'timestamp': 1644235332,
            'upload_date': '20220207',
            'uploader_id': 'nathalie.minard@un.org',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        partner_id = self._search_regex(r'partnerId\s*:\s*(\d+)\b', webpage, 'Partner ID')
        video_id = self._search_regex(r'/p/%s(?:/\w+)+?/entry_id/(\w+)/' % (partner_id, ), webpage, 'Kaltura ID')
        title = (
            self._html_search_meta(('title', 'og:title'), webpage)
            or self._html_search_regex(r'<title\b[^>]*>([^<]+)</title\b', webpage, 'title').rsplit('|', 1)[0]).strip()
        result = self.url_result(
            'kaltura:%s:%s' % (partner_id, video_id), 'Kaltura',
            video_title=title,
            video_id=video_id)
        if result:
            result.update({
                '_type': 'url_transparent',
                'description': self._html_search_meta(('description', 'og:description'), webpage, 'description'),
                'creator': self._html_search_meta('author', webpage),
                'upoader_id': self._html_search_meta('publisher', webpage),
                'thumbnail': url_or_none(self._og_search_thumbnail(webpage)),
                'timestamp': unified_timestamp(self._og_search_property('updated_time', webpage)),
            })
        return result
