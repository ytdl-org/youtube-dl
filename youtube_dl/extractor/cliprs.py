# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
)


class ClipRsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?clip\.rs/(?P<id>[^/]+)/\d+'
    _TEST = {
        'url': 'http://www.clip.rs/premijera-frajle-predstavljaju-novi-spot-za-pesmu-moli-me-moli/3732',
        'md5': 'c412d57815ba07b56f9edc7b5d6a14e5',
        'info_dict': {
            'id': '1488842.1399140381',
            'ext': 'mp4',
            'title': 'PREMIJERA Frajle predstavljaju novi spot za pesmu Moli me, moli',
            'description': 'md5:56ce2c3b4ab31c5a2e0b17cb9a453026',
            'duration': 229,
            'timestamp': 1459850243,
            'upload_date': '20160405',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'id=(["\'])mvp:(?P<id>.+?)\1', webpage, 'mvp id', group='id')

        response = self._download_json(
            'http://qi.ckm.onetapi.pl/', video_id,
            query={
                'body[id]': video_id,
                'body[jsonrpc]': '2.0',
                'body[method]': 'get_asset_detail',
                'body[params][ID_Publikacji]': video_id,
                'body[params][Service]': 'www.onet.pl',
                'content-type': 'application/jsonp',
                'x-onet-app': 'player.front.onetapi.pl',
            })

        error = response.get('error')
        if error:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error['message']), expected=True)

        video = response['result'].get('0')

        formats = []
        for _, formats_dict in video['formats'].items():
            if not isinstance(formats_dict, dict):
                continue
            for format_id, format_list in formats_dict.items():
                if not isinstance(format_list, list):
                    continue
                for f in format_list:
                    if not f.get('url'):
                        continue
                    formats.append({
                        'url': f['url'],
                        'format_id': format_id,
                        'height': int_or_none(f.get('vertical_resolution')),
                        'width': int_or_none(f.get('horizontal_resolution')),
                        'abr': float_or_none(f.get('audio_bitrate')),
                        'vbr': float_or_none(f.get('video_bitrate')),
                    })
        self._sort_formats(formats)

        meta = video.get('meta', {})

        title = self._og_search_title(webpage, default=None) or meta['title']
        description = self._og_search_description(webpage, default=None) or meta.get('description')
        duration = meta.get('length') or meta.get('lenght')
        timestamp = parse_iso8601(meta.get('addDate'), ' ')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }
