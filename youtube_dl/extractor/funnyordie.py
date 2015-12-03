from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import ExtractorError


class FunnyOrDieIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funnyordie\.com/(?P<type>embed|articles|videos)/(?P<id>[0-9a-f]+)(?:$|[?#/])'
    _TESTS = [{
        'url': 'http://www.funnyordie.com/videos/0732f586d7/heart-shaped-box-literal-video-version',
        'md5': 'bcd81e0c4f26189ee09be362ad6e6ba9',
        'info_dict': {
            'id': '0732f586d7',
            'ext': 'mp4',
            'title': 'Heart-Shaped Box: Literal Video Version',
            'description': 'md5:ea09a01bc9a1c46d9ab696c01747c338',
            'thumbnail': 're:^http:.*\.jpg$',
        },
    }, {
        'url': 'http://www.funnyordie.com/embed/e402820827',
        'info_dict': {
            'id': 'e402820827',
            'ext': 'mp4',
            'title': 'Please Use This Song (Jon Lajoie)',
            'description': 'Please use this to sell something.  www.jonlajoie.com',
            'thumbnail': 're:^http:.*\.jpg$',
        },
    }, {
        'url': 'http://www.funnyordie.com/articles/ebf5e34fc8/10-hours-of-walking-in-nyc-as-a-man',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        links = re.findall(r'<source src="([^"]+/v)[^"]+\.([^"]+)" type=\'video', webpage)
        if not links:
            raise ExtractorError('No media links available for %s' % video_id)

        links.sort(key=lambda link: 1 if link[1] == 'mp4' else 0)

        m3u8_url = self._search_regex(
            r'<source[^>]+src=(["\'])(?P<url>.+?/master\.m3u8)\1',
            webpage, 'm3u8 url', default=None, group='url')

        formats = []

        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
        if m3u8_formats:
            formats.extend(m3u8_formats)

        bitrates = [int(bitrate) for bitrate in re.findall(r'[,/]v(\d+)[,/]', m3u8_url)]
        bitrates.sort()

        for bitrate in bitrates:
            for link in links:
                formats.append({
                    'url': self._proto_relative_url('%s%d.%s' % (link[0], bitrate, link[1])),
                    'format_id': '%s-%d' % (link[1], bitrate),
                    'vbr': bitrate,
                })

        subtitles = {}
        for src, src_lang in re.findall(r'<track kind="captions" src="([^"]+)" srclang="([^"]+)"', webpage):
            subtitles[src_lang] = [{
                'ext': src.split('/')[-1],
                'url': 'http://www.funnyordie.com%s' % src,
            }]

        post_json = self._search_regex(
            r'fb_post\s*=\s*(\{.*?\});', webpage, 'post details')
        post = json.loads(post_json)

        return {
            'id': video_id,
            'title': post['name'],
            'description': post.get('description'),
            'thumbnail': post.get('picture'),
            'formats': formats,
            'subtitles': subtitles,
        }
