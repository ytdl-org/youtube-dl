# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import parse_iso8601, ExtractorError


class CtsNewsIE(InfoExtractor):
    IE_DESC = '華視新聞'
    # https connection failed (Connection reset)
    _VALID_URL = r'http://news\.cts\.com\.tw/[a-z]+/[a-z]+/\d+/(?P<id>\d+)\.html'
    _TESTS = [{
        'url': 'http://news.cts.com.tw/cts/international/201501/201501291578109.html',
        'md5': 'a9875cb790252b08431186d741beaabe',
        'info_dict': {
            'id': '201501291578109',
            'ext': 'mp4',
            'title': '以色列.真主黨交火 3人死亡',
            'description': 'md5:95e9b295c898b7ff294f09d450178d7d',
            'timestamp': 1422528540,
            'upload_date': '20150129',
        }
    }, {
        # News count not appear on page but still available in database
        'url': 'http://news.cts.com.tw/cts/international/201309/201309031304098.html',
        'md5': '3aee7e0df7cdff94e43581f54c22619e',
        'info_dict': {
            'id': '201309031304098',
            'ext': 'mp4',
            'title': '韓國31歲童顏男 貌如十多歲小孩',
            'description': 'md5:f183feeba3752b683827aab71adad584',
            'thumbnail': 're:^https?://.*\.jpg$',
            'timestamp': 1378205880,
            'upload_date': '20130903',
        }
    }, {
        # With Youtube embedded video
        'url': 'http://news.cts.com.tw/cts/money/201501/201501291578003.html',
        'md5': '1d842c771dc94c8c3bca5af2cc1db9c5',
        'add_ie': ['Youtube'],
        'info_dict': {
            'id': 'OVbfO7d0_hQ',
            'ext': 'mp4',
            'title': 'iPhone6熱銷 蘋果財報亮眼',
            'description': 'md5:f395d4f485487bb0f992ed2c4b07aa7d',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20150128',
            'uploader_id': 'TBSCTS',
            'uploader': '中華電視公司',
        }
    }]

    def _real_extract(self, url):
        news_id = self._match_id(url)
        page = self._download_webpage(url, news_id)

        if self._search_regex(r'(CTSPlayer2)', page, 'CTSPlayer2 identifier', default=None):
            feed_url = self._html_search_regex(
                r'(http://news\.cts\.com\.tw/action/mp4feed\.php\?news_id=\d+)',
                page, 'feed url')
            video_url = self._download_webpage(
                feed_url, news_id, note='Fetching feed')
        else:
            self.to_screen('Not CTSPlayer video, trying Youtube...')
            youtube_url = self._search_regex(
                r'src="(//www\.youtube\.com/embed/[^"]+)"', page, 'youtube url',
                default=None)
            if not youtube_url:
                raise ExtractorError('The news includes no videos!', expected=True)

            return {
                '_type': 'url',
                'url': youtube_url,
                'ie_key': 'Youtube',
            }

        description = self._html_search_meta('description', page)
        title = self._html_search_meta('title', page)
        thumbnail = self._html_search_meta('image', page)

        datetime_str = self._html_search_regex(
            r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2})', page, 'date and time')
        # Transform into ISO 8601 format with timezone info
        datetime_str = datetime_str.replace('/', '-') + ':00+0800'
        timestamp = parse_iso8601(datetime_str, delimiter=' ')

        return {
            'id': news_id,
            'url': video_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
        }
