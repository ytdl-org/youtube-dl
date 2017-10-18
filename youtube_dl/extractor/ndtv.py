# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote_plus
)
from ..utils import (
    int_or_none,
    remove_end,
    unified_strdate,
)


class NDTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|gadgets|khabar|profit)\.)?ndtv\.com/videos?/(?:[^/]+/)*[^/?^&]+-(?P<id>\d+)'

    _TESTS = [
        {
            'url': 'http://www.ndtv.com/video/news/news/ndtv-exclusive-don-t-need-character-certificate-from-rahul-gandhi-says-arvind-kejriwal-300710',
            'md5': '39f992dbe5fb531c395d8bbedb1e5e88',
            'info_dict': {
                'id': '300710',
                'ext': 'mp4',
                'title': "NDTV exclusive: Don't need character certificate from Rahul Gandhi, says Arvind Kejriwal",
                'description': 'md5:ab2d4b4a6056c5cb4caa6d729deabf02',
                'upload_date': '20131208',
                'duration': 1327,
                'thumbnail': r're:https?://.*\.jpg',
            },
        },
        {
            'url': 'http://gadgets.ndtv.com/videos/uncharted-the-lost-legacy-review-465568',
            'md5': '1169bb2c0b288d65da4f4832a32e4489',
            'info_dict': {
                'id': '465568',
                'ext': 'mp4',
                'title': "Uncharted: The Lost Legacy Review",
                'description': 'md5:f8299743bc50c4cbd0dd307a3830fcb0',
                'upload_date': '20170816',
                'duration': 168,
                'thumbnail': r're:https?://.*\.jpg',
            }
        },
        {
            'url': 'https://khabar.ndtv.com/video/show/prime-time/prime-time-ill-system-and-poor-education-468818',
            'md5': '78efcf3880ef3fd9b83d405ca94a38eb',
            'info_dict': {
                'id': '468818',
                'ext': 'mp4',
                'title': "प्राइम टाइम: सिस्टम बीमार, स्कूल बदहाल",
                'description': 'md5:f410512f1b49672e5695dea16ef2731d',
                'upload_date': '20170928',
                'duration': 2218,
                'thumbnail': r're:https?://.*\.jpg',
            }
        },
        {
            'url': 'http://profit.ndtv.com/videos/news/video-indian-economy-on-very-solid-track-international-monetary-fund-chief-470040',
            'md5': '16f192bb61ae8721770ca82554a125e6',
            'info_dict': {
                'id': '470040',
                'ext': 'mp4',
                'title': "Indian Economy On 'Very Solid Track': International Monetary Fund Chief",
                'description': 'md5:e84e6b93a9ece5573df6344626fb6df7',
                'upload_date': '20171015',
                'duration': 137,
                'thumbnail': r're:https?://.*\.jpg',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = compat_urllib_parse_unquote_plus(
            self._search_regex(r"__title\s*=\s*'([^']+)'", webpage, 'title') or
            self._og_search_title(webpage))

        filename = self._search_regex(
            r"__filename\s*=\s*'([^']+)'", webpage, 'video filename')
        video_url = 'https://ndtvod.bc-ssl.cdn.bitgravity.com/23372/ndtv/%s' % filename

        duration = int_or_none(self._search_regex(
            r"__duration\s*=\s*'([^']+)'", webpage, 'duration', fatal=False))

        upload_date = unified_strdate(self._html_search_meta(
            'publish-date', webpage, 'upload date', fatal=False))

        description = remove_end(self._og_search_description(webpage), ' (Read more)')

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': self._og_search_thumbnail(webpage),
            'duration': duration,
            'upload_date': upload_date,
        }
