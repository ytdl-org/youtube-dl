# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class Formula1IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?formula1\.com/(?:content/fom-website/)?en/video/\d{4}/\d{1,2}/(?P<id>.+?)\.html'
    _TESTS = [{
        'url': 'http://www.formula1.com/content/fom-website/en/video/2016/5/Race_highlights_-_Spain_2016.html',
        'md5': '8c79e54be72078b26b89e0e111c0502b',
        'info_dict': {
            'id': 'JvYXJpMzE6pArfHWm5ARp5AiUmD-gibV',
            'ext': 'mp4',
            'title': 'Race highlights - Spain 2016',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['Ooyala'],
    }, {
        'url': 'http://www.formula1.com/en/video/2016/5/Race_highlights_-_Spain_2016.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        ooyala_embed_code = self._search_regex(
            r'data-videoid="([^"]+)"', webpage, 'ooyala embed code')
        return self.url_result(
            'ooyala:%s' % ooyala_embed_code, 'Ooyala', ooyala_embed_code)


class F1TVIE(InfoExtractor):
    _VALID_URL = r'https?://f1tv\.formula1\.com/en/(?:[^/]+)/(?:[^/]+)/(?P<id>.+)'

    _TESTS = [{
        'url': 'https://f1tv.formula1.com/en/current-season/singapore-grand-prix/2019-singapore-grand-prix-race',
        'info_dict': {
            'id': '2019-singapore-grand-prix-race',
            'ext': 'mp4',
            'title': '2019 Singapore Grand Prix Formula 1 Race',
        },
        'params': {
            'format': 'bestvideo',
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://f1tv.formula1.com/en/current-season/singapore-grand-prix/2019-singapore-grand-prix-race',
        'only_matching': True,
    }]

    _API_BASE = 'https://f1tv.formula1.com/api'

    def _real_extract(self, url):
        slug = self._match_id(url)

        metadata = self._download_json(
            self._API_BASE + '/session-occurrence/?slug=' + slug + '&fields=session_name,channel_urls&fields_to_expand=channel_urls',
            slug
        )
        metadata = metadata['objects'][0]

        # Select world feed perspective
        for channel in metadata['channel_urls']:
            if channel.get('name') == 'WIF':
                channelUrl = channel['self']
                break

        channel = self._download_json(
            self._API_BASE + '/viewings/', slug,
            headers={'Content-Type': 'application/json'},
            data='{"channel_url": "' + channelUrl + '"}',
            note='Downloading JSON channel info'
        )

        formats = self._extract_m3u8_formats(
            channel['tokenised_url'], slug,
            'mp4', 'm3u8_native', m3u8_id='hls'
        )

        return {
            'id': slug,
            'title': metadata['session_name'],
            'formats': formats,
        }
