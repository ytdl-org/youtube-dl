# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    int_or_none,
    parse_iso8601,
    try_get,
)

import re


class RumbleEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rumble\.com/(?:embed/(?:[0-9a-z]+\.)?(?P<id>[0-9a-z]+)|(.*?)\.html)'
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
    }, {
        'url': 'https://rumble.com/vhlrar-mike-lindell-to-confront-brian-kemp-and-doug-ducey-over-election-fraud.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        if re.match(r'https?://(?:www\.)?rumble\.com/(.*?)\.html', url):
            video_id = ""
            content, urlh = self._download_webpage_handle(url, video_id)
            video_id = re.findall(r'"embedUrl":"https://rumble\.com/embed/(.*?)/"', content)[0]
        else:
            video_id = self._match_id(url)
        video = self._download_json(
            'https://rumble.com/embedJS/', video_id,
            query={'request': 'video', 'v': video_id})
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


class RumbleRegularIE(RumbleEmbedIE):
    _VALID_URL = r'https?://(?:www\.)?rumble\.com/(.*?)\.html'
    _TESTS = [{
        'url': 'https://rumble.com/vhlrar-mike-lindell-to-confront-brian-kemp-and-doug-ducey-over-election-fraud.html',
        'md5': '36a18a049856720189f30977ccbb2c34',
        'info_dict': {
            'id': 'v5pv5f',
            'ext': 'mp4',
            'title': 'WMAR 2 News Latest Headlines | October 20, 6pm',
            'timestamp': 1571611968,
            'upload_date': '20191020',
        }
    }, {
        'url': 'https://rumble.com/vhlrar-mike-lindell-to-confront-brian-kemp-and-doug-ducey-over-election-fraud.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = ""
        content, urlh = self._download_webpage_handle(url, video_id)
        video_id = re.findall(r'"embedUrl":"https://rumble\.com/embed/(.*?)/"', content)[0]

        # this is
        #video_id = self._match_id(url)
        video = self._download_json(
            'https://rumble.com/embedJS/', video_id,
            query={'request': 'video', 'v': video_id})
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
