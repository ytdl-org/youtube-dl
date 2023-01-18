# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    try_get,
)


class rumbleBase(InfoExtractor):
    def rumble_video_info(self, video_id):
        video = self._download_json(
            'https://rumble.com/embedJS/', video_id,
            query={'request': 'video', 'v': video_id})
        if not video:
            return None

        title = video['title']

        formats = []
        for height, ua in (video.get('ua') or {}).items():
            for i in range(2):
                f_url = try_get(ua, lambda x: x[i], compat_str)
                if f_url:
                    ext = determine_ext(f_url)
                    f = {
                        'ext': ext,
                        'format_id': '%s-%sp' % (ext, height),
                        'height': int_or_none(height),
                        'url': f_url,
                    }
                    bitrate = try_get(ua, lambda x: x[i + 2]['bitrate'])
                    if bitrate:
                        f['tbr'] = int_or_none(bitrate)
                    formats.append(f)
        self._sort_formats(formats)

        author = video.get('author') or {}

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': video.get('i'),
            'timestamp': parse_iso8601(video.get('pubDate')),
            'channel': author.get('name'),
            'channel_url': author.get('url'),
            'duration': int_or_none(video.get('duration')),
        }


class RumbleEmbedIE(rumbleBase):
    _VALID_URL = r'https?://(?:www\.)?rumble\.com/embed/(?:[0-9a-z]+\.)?(?P<id>[0-9a-z]+)'
    _TESTS = [{
        'url': 'https://rumble.com/embed/v5pv5f',
        'md5': '36a18a049856720189f30977ccbb2c34',
        'info_dict': {
            'id': 'v5pv5f',
            'ext': 'mp4',
            'title': 'WMAR 2 News Latest Headlines | October 20, 6pm',
            'timestamp': 1571611968,
            'upload_date': '20191020',
        }
    }, {
        'url': 'https://rumble.com/embed/ufe9n.v5pv5f',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.rumble_video_info(video_id)


class RumblePageIE(rumbleBase):
    _VALID_URL = r'https?://rumble\.com/[a-zA-Z0-9-_.]*\.html'
    _TEST = {
        'url': 'https://rumble.com/v8c1bt-wmar-2-news-latest-headlines-october-20-6pm.html',
        'md5': '36a18a049856720189f30977ccbb2c34',
        'info_dict': {
            'id': 'v5pv5f',
            'ext': 'mp4',
            'title': 'WMAR 2 News Latest Headlines | October 20, 6pm',
            'timestamp': 1571611968,
            'upload_date': '20191020',
        }}

    _RUMBLE_JS_RE = r'Rumble *\( *["\']play["\'], *\{[^}]*["\']video["\'] *: *["\'](?P<id>[^"\']+)'

    def _real_extract(self, url):
        page = self._download_webpage(url, 'Rumble Page')
        video_id = self._search_regex(self._RUMBLE_JS_RE, page, "id")
        return self.rumble_video_info(video_id)


class RumblePlaylistIE(rumbleBase):
    _VALID_URL = r'https?://rumble.com/(?:c|user)/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://rumble.com/c/PeakProsperity',
        'playlist_mincount': 25,
        'info_dict': {
            'id': 'PeakProsperity',
        }}

    def _real_extract(self, url):
        urls = []
        id = self._match_id(url)
        page = self._download_webpage(url, id)
        for mobj in re.finditer(r'<a class=video-item--a href=\/(?P<href>[a-zA-Z0-9\-.]+)>', page):
            urls.append('https://rumble.com/' + mobj.group('href'))

        return self.playlist_from_matches(urls, id)


def rumble_embedded_id(page_data):
    '''For use by extractors of sites which use emedded Rumble videos. Given
    a webpage as a string returns a list of url result dicts for each embedded
    rumble video found. None is returned if no embeds were found. Duplicates
    are not removed'''

    embeds = []
    # The JS embeds
    for mobj in re.finditer(RumblePageIE._RUMBLE_JS_RE, page_data):
        embeds.append(InfoExtractor.url_result('https://rumble.com/embed/' + mobj.group('id'),'RumbleEmbed',mobj.group('id')))

    # The iframes embeds
    for mobj in re.finditer(RumbleEmbedIE._VALID_URL, page_data):
        embeds.append(InfoExtractor.url_result('https://rumble.com/embed/' + mobj.group('id'),'RumbleEmbed',mobj.group('id')))

    return embeds if embeds else None
