# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SampleFocusIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?samplefocus\.com/samples/(?P<id>[^/?&#]+)'
    _TESTS = [{
        'url': 'https://samplefocus.com/samples/lil-peep-sad-emo-guitar',
        'md5': '48c8d62d60be467293912e0e619a5120',
        'info_dict': {
            'id': 'lil-peep-sad-emo-guitar',
            'ext': 'mp3',
            'title': 'Lil Peep Sad Emo Guitar',
            'description': 'Listen to Lil Peep Sad Emo Guitar. Royalty-Free sound that is tagged as electric guitar, emo, guitar, and lil peep. Download for FREE + discover 1000\'s of sounds.',
            'thumbnail': r're:^https?://.+\.png',
            'license': 'Standard License'
        }
    }, {
        'url': 'https://samplefocus.com/samples/dababy-style-bass-808',
        'only_matching': True
    }, {
        'url': 'https://samplefocus.com/samples/young-chop-kick',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage, fatal=False) or self._html_search_regex(
            r'<h1>(.+?)</h1>', webpage, 'title', default=video_id)

        mp3_url = self._html_search_regex(
            r'<input[^>]+id=(?:["\'])sample_mp3(?:["\'])[^>]+value=(?:["\'])(.+?)(?:["\'])[^>]*>',
            webpage, 'mp3', fatal=False) or self._html_search_regex(
            r'<meta[^>]+itemprop=(?:["\'])contentUrl(?:["\'])[^>]+content=(?:["\'])?([^>"\']+)(?:["\'])?[^>]*>',
            webpage, 'mp3 url')

        tb = self._og_search_thumbnail(webpage) or self._html_search_regex(
            r'<img[^>]+class=(?:["\'])waveform responsive-img[^>]+src=(?:["\'])([^"\']+)',
            webpage, 'mp3', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': mp3_url,
            'ext': 'mp3',
            'thumbnail': tb,
            'description': self._html_search_meta('description', webpage),
            'license': self._html_search_regex(r'<a[^>]+href=(?:["\'])/license(?:["\'])[^>]*>([^<]+)<', webpage, 'license')
        }
