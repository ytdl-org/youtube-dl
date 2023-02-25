# coding: utf-8
from __future__ import unicode_literals

import json

from ..utils import (
    clean_html,
    ExtractorError,
    try_get,
)
from .common import InfoExtractor


class BellesaIE(InfoExtractor):
    _VALID_URL = r'''https?://www\.bellesa\.co/videos/(?P<id>[0-9]+)/'''
    _TESTS = [{
        'url': 'https://www.bellesa.co/videos/2189/my-first-time-kissing-women',
        'md5': '543b002f4d1e5b4a0dde243f4a43fd28',
        'info_dict': {
            'id': '2189',
            'ext': 'mp4',
            'title': 'My First Time Kissing Women',
            'thumbnail': 'https://c.bellesa.co/dkvdbifey/image/upload/v1599024046/video_upload/2189cover.jpg',
            'description': 'md5:69eea8a4ee31d42d6fd6302ad9e09ab2',
            'creator': 'Bellesa Films',
            'upload_date': '20191216',
            'timestamp': 1576539207,
            'duration': 721,
            'tags': 'mincount: 1',
            'categories': ['Girl on Girl', 'Story'],
            'age_limit': 18,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.bellesa.co/videos/%s/' % video_id, video_id)

        # videos on this page are embedded into a container called VideoCard - if there is
        # nothing on the page referencing a VideoCard we cannot extract the information and
        # thus need to raise an error
        if 'VideoCard' not in webpage:
            title = self._html_search_regex(
                r'(?s)<title\b[^>]*>(?P<title>.+?)(?:\|\s+Bellesa)?</title',
                webpage, 'title', default=None,
                group='title', fatal=False)

            raise ExtractorError('[%s] %s: %s' % (self.IE_NAME, video_id, clean_html(title)), expected=True)

        initial_data_raw = self._search_regex(r'(?s)window\s*\.\s*__INITIAL_DATA__\s*=\s*(\{.+?\})\s*;\s*</script>', webpage, 'initial_data')

        try:
            initial_data = json.loads(initial_data_raw)
        except json.JSONDecodeError:
            raise ExtractorError('%s said: cannot decode initial data', self.IE_NAME, expected=True)

        video = try_get(initial_data, lambda x: x['video'], dict) or {}

        resolutions = video.get('resolutions')
        source = video.get('source')

        if not resolutions or not source:
            raise ExtractorError('%s said: cannot extract playlist information from meta data' % self.IE_NAME, expected=True)

        m3u8_url = 'https://s.bellesa.co/hls/v/%s/,%s,.mp4.urlset/master.m3u8' % (source, resolutions)
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls',
            fatal=False)

        self._sort_formats(formats)

        # get from video meta data first
        title = video.get('title')
        title = strip_or_none(video.get('title'))
        if not title:
            # fallback to og:title, which needs some treatment
            title = self._og_search_title(webpage)
            if title:
                title = title.split('|')[0].strip()

        tags = list(filter(None, map(lambda s: s.strip(), (video.get('tags') or '').split(','))))

        categories = None
        if 'categories' in video:
            categories = [c['name'] for c in video.get('categories')]
        list(filter(None, map(lambda d: strip_or_none(d['name']), (video.get('categories') or []))))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': url_or_none(video.get('image')),
            'description': strip_or_none(video.get('description')) or None,
            'creator': try_get(video, lambda x: x['content_provider'][0]['name'].strip(), compat_str),
            'timestamp': int_or_none(video.get('posted_on')),
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('views')),
            'tags': tags or None,
            'categories': categories or None,
            'age_limit': 18,
            'formats': formats,
        }
