# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    str_or_none,
)


class ShahidIE(InfoExtractor):
    _VALID_URL = r'https?://shahid\.mbc\.net/ar/episode/(?P<id>\d+)/?'
    _TESTS = [{
        'url': 'https://shahid.mbc.net/ar/episode/90574/%D8%A7%D9%84%D9%85%D9%84%D9%83-%D8%B9%D8%A8%D8%AF%D8%A7%D9%84%D9%84%D9%87-%D8%A7%D9%84%D8%A5%D9%86%D8%B3%D8%A7%D9%86-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-1-%D9%83%D9%84%D9%8A%D8%A8-3.html',
        'info_dict': {
            'id': '90574',
            'ext': 'mp4',
            'title': 'الملك عبدالله الإنسان الموسم 1 كليب 3',
            'description': 'الفيلم الوثائقي - الملك عبد الله الإنسان',
            'duration': 2972,
            'timestamp': 1422057420,
            'upload_date': '20150123',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        # shahid plus subscriber only
        'url': 'https://shahid.mbc.net/ar/episode/90511/%D9%85%D8%B1%D8%A7%D9%8A%D8%A7-2011-%D8%A7%D9%84%D9%85%D9%88%D8%B3%D9%85-1-%D8%A7%D9%84%D8%AD%D9%84%D9%82%D8%A9-1.html',
        'only_matching': True
    }]

    def _call_api(self, path, video_id, note):
        data = self._download_json(
            'http://api.shahid.net/api/v1_1/' + path, video_id, note, query={
                'apiKey': 'sh@hid0nlin3',
                'hash': 'b2wMCTHpSmyxGqQjJFOycRmLSex+BpTK/ooxy6vHaqs=',
            }).get('data', {})

        error = data.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, '\n'.join(error.values())),
                expected=True)

        return data

    def _real_extract(self, url):
        video_id = self._match_id(url)

        player = self._call_api(
            'Content/Episode/%s' % video_id,
            video_id, 'Downloading player JSON')

        if player.get('drm'):
            raise ExtractorError('This video is DRM protected.', expected=True)

        formats = self._extract_m3u8_formats(player['url'], video_id, 'mp4')
        self._sort_formats(formats)

        video = self._call_api(
            'episode/%s' % video_id, video_id,
            'Downloading video JSON')['episode']

        title = video['title']
        categories = [
            category['name']
            for category in video.get('genres', []) if 'name' in category]

        return {
            'id': video_id,
            'title': title,
            'description': video.get('description'),
            'thumbnail': video.get('thumbnailUrl'),
            'duration': int_or_none(video.get('duration')),
            'timestamp': parse_iso8601(video.get('referenceDate')),
            'categories': categories,
            'series': video.get('showTitle') or video.get('showName'),
            'season': video.get('seasonTitle'),
            'season_number': int_or_none(video.get('seasonNumber')),
            'season_id': str_or_none(video.get('seasonId')),
            'episode_number': int_or_none(video.get('number')),
            'episode_id': video_id,
            'formats': formats,
        }
