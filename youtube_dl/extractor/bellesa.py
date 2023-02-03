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
            'description': 'Jenna opens up about her troubles navigating a long-distance relationship. Her girlfriends ask if she’d ever be open to cheating on him but she says she would never, they’ve been together since college. Lena and Carter sit on either side of her and remind her it isn’t cheating if it’s with a girl…they start kissing and rubbing her chest, going down on her together. This girl on girl scene is so sensual, and the nerves on Jenna are real — exploring your sexuality takes courage, but there’s a lot of good vibes in this threesome.',
            'creator': 'Bellesa Films',
            'upload_date': '20191216',
            'timestamp': 1576539207,
            'duration': 721,
            'tags': ['HD Porn', 'Porn for Women', 'Orgasm', 'Bellesa Films', 'Threesome', 'FFF', 'Girl on Girl', 'Lesbians', 'Lesbian Porn', 'Nipple Licking', 'Finger', 'Cunnilingus', 'Anilingus', 'Eating Out', 'Clit Play', 'Clit Stimulation', 'Natural Breasts', 'Face Sitting', 'Spitting'],
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
                r'<title[^>]*>(?P<title>.+?)\s+\|\s+Bellesa',
                webpage, 'title', default=None,
                group='title', fatal=False)

            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(title)), expected=True)

        initial_data_raw = self._search_regex(r'window\.__INITIAL_DATA__\s+=\s+(.+?);</script>', webpage, 'initial_data')

        try:
            initial_data = json.loads(initial_data_raw)
        except json.JSONDecodeError:
            raise ExtractorError('%s said: cannot decode initial data', self.IE_NAME, expected=True)

        video = try_get(initial_data, lambda x: x['video'])
        if not video:
            raise ExtractorError('%s said: initial data malformed' % self.IE_NAME, expected=True)

        resolutions = try_get(video, lambda x: x['resolutions'])
        source = try_get(video, lambda x: x['source'])

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
        if title:
            title = title.strip()
        else:
            # fallback to og:title, which needs some treatment
            title = self._og_search_title(webpage)
            if title:
                title = title.split('|')[0].strip()

        tags = None
        tag_string = video.get('tags')
        if tag_string:
            tags = [c for c in map(lambda s: s.strip(), tag_string.split(','))]

        categories = None
        if 'categories' in video:
            categories = [c['name'] for c in video.get('categories')]

        description = try_get(video, lambda x: x['description'])
        if description:
            description = description.strip()

        return {
            'id': video_id,
            'title': title,
            'thumbnail': try_get(video, lambda x: x['image']),
            'description': description,
            'creator': try_get(video, lambda x: x['content_provider'][0]['name']),
            'timestamp': try_get(video, lambda x: x['posted_on']),
            'duration': try_get(video, lambda x: x['duration']),
            'view_count': try_get(video, lambda x: x['views']),
            'tags': tags,
            'categories': categories,
            'age_limit': 18,
            'formats': formats,
        }
