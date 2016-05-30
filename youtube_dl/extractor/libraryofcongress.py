# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import determine_ext


class LibraryOfCongressIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?loc\.gov/item/(?P<id>[0-9]+)'
    _TESTS = [{
    'url': 'http://loc.gov/item/90716351/',
        'info_dict': {
            'id': '90716351',
            'ext': 'mp4',
            'title': 'Pa\'s trip to Mars /'
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'https://www.loc.gov/item/97516576/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)
        json_id = self._search_regex('media-player-([0-9A-Z]{32})', webpage, 'json id')

        data = self._parse_json(self._download_webpage(
            'https://media.loc.gov/services/v1/media?id=%s' % json_id,
            video_id), video_id)
        data = data['mediaObject']

        media_url = data['derivatives'][0]['derivativeUrl']
        media_url = media_url.replace('rtmp', 'https')

        is_video = data['mediaType'].lower() == 'v'
        if not determine_ext(media_url) in ('mp4', 'mp3'):
            media_url += '.mp4' if is_video else '.mp3'

        if media_url.index('vod/mp4:') > -1:
            media_url = media_url.replace('vod/mp4:', 'hls-vod/media/') + '.m3u8'
        elif url.index('vod/mp3:') > -1:
            media_url = media_url.replace('vod/mp3:', '')

        formats = []
        if determine_ext(media_url) == 'm3u8':
            formats = self._extract_m3u8_formats(media_url, video_id, ext='mp4')
        elif determine_ext(media_url) is 'mp3':
            formats.append({
                'url': media_url,
                'ext': 'mp3',
            })

        return {
            'id': video_id,
            'thumbnail': self._og_search_thumbnail(webpage),
            'title': self._og_search_title(webpage),
            'formats': formats,
        }
