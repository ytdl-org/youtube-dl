# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    smuggle_url,
    unescapeHTML,
    url_or_none,
)


class KickStarterIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?kickstarter\.com/projects/(?P<id>[^/]*)/.*'
    _TESTS = [{
        'url': 'https://www.kickstarter.com/projects/1404461844/intersection-the-story-of-josh-grant/description',
        'md5': 'c81addca81327ffa66c642b5d8b08cab',
        'info_dict': {
            'id': '1404461844',
            'ext': 'mp4',
            'title': 'Intersection: The Story of Josh Grant by Kyle Cowling',
            'description': (
                'A unique motocross documentary that examines the '
                'life and mind of one of sports most elite athletes: Josh Grant.'
            ),
        },
    }, {
        'note': 'Embedded video (not using the native kickstarter video service)',
        'url': 'https://www.kickstarter.com/projects/597507018/pebble-e-paper-watch-for-iphone-and-android/posts/659178',
        'info_dict': {
            'id': '78704821',
            'ext': 'mp4',
            'uploader_id': 'pebble',
            'uploader': 'Pebble Technology',
            'title': 'Pebble iOS Notifications',
        },
        'add_ie': ['Vimeo'],
    }, {
        'url': 'https://www.kickstarter.com/projects/1420158244/power-drive-2000/widget/video.html',
        'info_dict': {
            'id': '1420158244',
            'ext': 'mp4',
            'title': 'Power Drive 2000',
        },
    }, {  # hls
        'url': 'https://www.kickstarter.com/projects/mccaskellgames/last-one-standing-the-battle-royale-board-game',
        'md5': 'fec77f16122b967e638b3de52b69ebe0',
        'info_dict': {
            'id': 'mccaskellgames',
            'ext': 'mp4',
            'title': 'Last One Standing: The Battle Royale Board Game by Brendan McCaskell',
            'description': 'Up to 8 players find themselves on an ever-shrinking map where they must shoot, move and loot to be the last one standing.',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>\s*(.*?)(?:\s*&mdash;\s*Kickstarter)?\s*</title>',
            webpage, 'title')

        video_data = self._parse_json(self._search_regex(
            r'data-video="(.*?)"',
            webpage, 'video URL', default='{}'
        ), video_id, transform_source=unescapeHTML)

        formats = []
        if video_data:
            hls_url = url_or_none(video_data.get('hls'))
            if hls_url:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, video_id, 'mp4', 'm3u8_native', fatal=False)
                )
            height = int_or_none(video_data.get('height'))
            width = int_or_none(video_data.get('widht'))
            for quality in ['base', 'high']:
                video_url = url_or_none(video_data.get(quality))
                if video_url:
                    formats.append({'url': video_url, 'height': height, 'width': width})

        if not formats:  # fallback
            video_url = url_or_none(self._search_regex(
                r'data-video-url="(.*?)"',
                webpage, 'video URL', default=''
            ))
            if video_url:
                formats.append({'url': video_url})

        if not formats:  # No native kickstarter, look for embedded videos
            return {
                '_type': 'url_transparent',
                'ie_key': 'Generic',
                'url': smuggle_url(url, {'to_generic': True}),
                'title': title,
            }

        thumbnail = self._og_search_thumbnail(webpage, default=None)
        if thumbnail is None:
            thumbnail = self._html_search_regex(
                r'<img[^>]+class="[^"]+\s*poster\s*[^"]+"[^>]+src="([^"]+)"',
                webpage, 'thumbnail image', fatal=False)

        self._sort_formats(formats)
        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': thumbnail,
        }
