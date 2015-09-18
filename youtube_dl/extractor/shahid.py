# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
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

    def _handle_error(self, response):
        if not isinstance(response, dict):
            return
        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, '\n'.join(error.values())),
                expected=True)

    def _download_json(self, url, video_id, note='Downloading JSON metadata'):
        response = super(ShahidIE, self)._download_json(url, video_id, note)['data']
        self._handle_error(response)
        return response

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        api_vars = {
            'id': video_id,
            'type': 'player',
            'url': 'http://api.shahid.net/api/v1_1',
            'playerType': 'episode',
        }

        flashvars = self._search_regex(
            r'var\s+flashvars\s*=\s*({[^}]+})', webpage, 'flashvars', default=None)
        if flashvars:
            for key in api_vars.keys():
                value = self._search_regex(
                    r'\b%s\s*:\s*(?P<q>["\'])(?P<value>.+?)(?P=q)' % key,
                    flashvars, 'type', default=None, group='value')
                if value:
                    api_vars[key] = value

        player = self._download_json(
            'https://shahid.mbc.net/arContent/getPlayerContent-param-.id-%s.type-%s.html'
            % (video_id, api_vars['type']), video_id, 'Downloading player JSON')

        formats = self._extract_m3u8_formats(player['url'], video_id, 'mp4')

        video = self._download_json(
            '%s/%s/%s?%s' % (
                api_vars['url'], api_vars['playerType'], api_vars['id'],
                compat_urllib_parse.urlencode({
                    'apiKey': 'sh@hid0nlin3',
                    'hash': 'b2wMCTHpSmyxGqQjJFOycRmLSex+BpTK/ooxy6vHaqs=',
                })),
            video_id, 'Downloading video JSON')

        video = video[api_vars['playerType']]

        title = video['title']
        description = video.get('description')
        thumbnail = video.get('thumbnailUrl')
        duration = int_or_none(video.get('duration'))
        timestamp = parse_iso8601(video.get('referenceDate'))
        categories = [
            category['name']
            for category in video.get('genres', []) if 'name' in category]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'categories': categories,
            'formats': formats,
        }
