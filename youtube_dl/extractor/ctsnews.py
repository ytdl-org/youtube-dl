# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import parse_iso8601, ExtractorError


class CtsNewsIE(InfoExtractor):
    _VALID_URL = r'http://news\.cts\.com\.tw/[a-z]+/[a-z]+/\d+/(?P<id>\d+)\.html'
    _TESTS = [{
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
    }]

    def _real_extract(self, url):
        news_id = self._match_id(url)
        page = self._download_webpage(url, news_id)

        if not self._search_regex(r'(CTSPlayer2)', page, 'CTSPlayer2 identifier', fatal=False):
            raise ExtractorError('The news includes no videos!')

        feed_pattern = r'(http://news.cts.com.tw/action/mp4feed.php\?news_id=\d+)'
        feed_url = self._html_search_regex(feed_pattern, page, 'feed url')
        feed_page = self._download_webpage(feed_url, news_id)

        description = self._html_search_meta('description', page)
        title = self._html_search_meta('title', page)
        thumbnail = self._html_search_meta('image', page)

        datetime_pattern = r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2})'
        datetime_str = self._html_search_regex(datetime_pattern, page, 'date and time')
        time = (datetime_str + ':00+08:00').replace('/', '-')
        timestamp = parse_iso8601(time, delimiter=' ')

        return {
            'id': news_id,
            'title': title,
            'description': description,
            'url': feed_page,
            'thumbnail': thumbnail,
            'timestamp': timestamp
        }
