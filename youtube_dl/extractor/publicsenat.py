# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class PublicSenatIE(InfoExtractor):
    IE_NAME = 'Publicsenat.fr'
    IE_DESC = 'Public Senat extractor'
    _VALID_URL = r'(https?://|www.)+replay\.publicsenat\.fr(/.*/(?P<id>[0-9]*)(#.*)?)?'
    _TEST = {
        'url': 'http://replay.publicsenat.fr/vod/documentaire/a-la-recherche-de-bernard-maris,-l-anti-economiste/192668#videosPV',
        'md5': 'fa1902d5b4f28a304d293f4c4d296fb9',
        'info_dict': {
            'ext': 'mp4',
            'title': 'Documentaire : A la recherche de Bernard Maris',
            'id': 'k7GE6aZIlHHPdieDh7w',
            'upload_date': '20160104',
            'uploader': 'Public Sénat',
            'description': 'md5:463fa20248134567e1125bc805f1b905',
            'uploader_id': 'xa9gza',
            'timestamp': 1451931617,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # the video are hosted on dailymotion.com
        url = self._html_search_regex(r'<input.*value="(?P<url>.*dailymotion.*)"', webpage, 'url')

        return {
            'url': url,
            '_type': 'url',
            'ie_key': 'Dailymotion',
        }
