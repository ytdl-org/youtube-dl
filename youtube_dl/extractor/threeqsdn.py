from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    js_to_json,
    mimetype2ext,
    unsmuggle_url,
)


class ThreeQSDNIE(InfoExtractor):
    IE_NAME = '3qsdn'
    IE_DESC = '3Q SDN'
    _VALID_URL = r'(?:https?://playout\.3qsdn\.com/|3qsdn:)(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'
    _API_URL = 'http://playout.3qsdn.com/'
    _TESTS = [{
        # ondemand from http://www.philharmonie.tv/veranstaltung/26/
        'url': 'http://playout.3qsdn.com/0280d6b9-1215-11e6-b427-0cc47a188158?protocol=http',
        'md5': 'ab040e37bcfa2e0c079f92cb1dd7f6cd',
        'info_dict': {
            'id': '0280d6b9-1215-11e6-b427-0cc47a188158',
            'ext': 'mp4',
            'title': '160504_sixpianos',
            'description': '160504_sixpianos',
            'is_live': False,
        },
        'expected_warnings': ['Failed to download MPD manifest', 'Failed to parse JSON'],
    }, {
        # live video stream
        'url': 'https://playout.3qsdn.com/d755d94b-4ab9-11e3-9162-0025907ad44f?js=true',
        'info_dict': {
            'id': 'd755d94b-4ab9-11e3-9162-0025907ad44f',
            'ext': 'mp4',
            'title': 're:^d755d94b-4ab9-11e3-9162-0025907ad44f [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            'is_live': True,
        },
        'params': {
            'skip_download': True,  # m3u8 downloads
        },
        'expected_warnings': ['Failed to download MPD manifest'],
    }, {
        # playlist
        'url': 'http://playout.3qsdn.com/2a70223f-b56f-11e6-a78b-0cc47a188158',
        'info_dict': {
            'id': '2a70223f-b56f-11e6-a78b-0cc47a188158',
        },
        'playlist_count': 11,
    }, {
        # live audio stream
        'url': 'http://playout.3qsdn.com/9edf36e0-6bf2-11e2-a16a-9acf09e2db48',
        'only_matching': True,
    }, {
        # live audio stream with some 404 URLs
        'url': 'http://playout.3qsdn.com/ac5c3186-777a-11e2-9c30-9acf09e2db48',
        'only_matching': True,
    }, {
        # geo restricted with 'This content is not available in your country'
        'url': 'http://playout.3qsdn.com/d63a3ffe-75e8-11e2-9c30-9acf09e2db48',
        'only_matching': True,
    }, {
        # geo restricted with 'playout.3qsdn.com/forbidden'
        'url': 'http://playout.3qsdn.com/8e330f26-6ae2-11e2-a16a-9acf09e2db48',
        'only_matching': True,
    }, {
        # live video with rtmp link
        'url': 'https://playout.3qsdn.com/6092bb9e-8f72-11e4-a173-002590c750be',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+\b(?:data-)?src=(["\'])(?P<url>%s.*?)\1' % ThreeQSDNIE._VALID_URL, webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url, smuggled_data = unsmuggle_url(url, {})

        js = self._download_webpage(
            self._API_URL + video_id, video_id,
            query={'js': 'true'})

        playout_ids = [m.group('id').replace('\\x2D', '-') for m in re.finditer(
            r'sdnPlayoutId\s*:\s*["\'](?P<id>.+?)["\']', js)]
        if playout_ids:
            if smuggled_data.get('first_video_only'):
                return self.url_result(self._API_URL + playout_ids[0], self.ie_key())
            return self.playlist_result(
                [self.url_result(self._API_URL + vid, self.ie_key()) for vid in playout_ids], video_id)

        if any(p in js for p in (
                '>This content is not available in your country',
                'playout.3qsdn.com/forbidden')):
            self.raise_geo_restricted()

        stream_content = self._search_regex(
            r'streamContent\s*:\s*(["\'])(?P<content>.+?)\1', js,
            'stream content', default='demand', group='content')

        live = stream_content == 'live'

        stream_type = self._search_regex(
            r'streamType\s*:\s*(["\'])(?P<type>audio|video)\1', js,
            'stream type', default='video', group='type')

        formats = []
        urls = set()

        def extract_formats(item_url, item={}):
            if not item_url or item_url in urls:
                return
            urls.add(item_url)
            ext = mimetype2ext(item.get('type')) or determine_ext(item_url, default_ext=None)
            if ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    item_url, video_id, mpd_id='mpd', fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    item_url, video_id, 'mp4',
                    entry_protocol='m3u8' if live else 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    item_url, video_id, f4m_id='hds', fatal=False))
            else:
                if not self._is_valid_url(item_url, video_id):
                    return
                formats.append({
                    'url': item_url,
                    'format_id': item.get('quality'),
                    'ext': 'mp4' if item_url.startswith('rtsp') else ext,
                    'vcodec': 'none' if stream_type == 'audio' else None,
                })

        for item_js in re.findall(r'({[^{]*?\b(?:src|source)\s*:\s*["\'].+?})', js):
            f = self._parse_json(
                item_js, video_id, transform_source=js_to_json, fatal=False)
            if not f:
                continue
            extract_formats(f.get('src'), f)

        # More relaxed version to collect additional URLs and acting
        # as a future-proof fallback
        for _, src in re.findall(r'\b(?:src|source)\s*:\s*(["\'])((?:https?|rtsp)://.+?)\1', js):
            extract_formats(src)

        self._sort_formats(formats)

        webpage = self._download_webpage(self._API_URL + video_id, video_id)
        title = self._live_title(video_id) if live else self._og_search_title(webpage, default=None)
        if not title:
            title = video_id
        description = self._og_search_description(webpage, default=None)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'is_live': live,
            'formats': formats,
        }
