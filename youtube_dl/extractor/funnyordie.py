from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    unified_timestamp,
)


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
            'thumbnail': r're:^http:.*\.jpg$',
            'uploader': 'DASjr',
            'timestamp': 1317904928,
            'upload_date': '20111006',
            'duration': 318.3,
        },
    }, {
        'url': 'http://www.funnyordie.com/embed/e402820827',
        'info_dict': {
            'id': 'e402820827',
            'ext': 'mp4',
            'title': 'Please Use This Song (Jon Lajoie)',
            'description': 'Please use this to sell something.  www.jonlajoie.com',
            'thumbnail': r're:^http:.*\.jpg$',
            'timestamp': 1398988800,
            'upload_date': '20140502',
        },
        'params': {
            'skip_download': True,
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
            r'<source[^>]+src=(["\'])(?P<url>.+?/master\.m3u8[^"\']*)\1',
            webpage, 'm3u8 url', group='url')

        formats = []

        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native',
            m3u8_id='hls', fatal=False)
        source_formats = list(filter(
            lambda f: f.get('vcodec') != 'none', m3u8_formats))

        bitrates = [int(bitrate) for bitrate in re.findall(r'[,/]v(\d+)(?=[,/])', m3u8_url)]
        bitrates.sort()

        if source_formats:
            self._sort_formats(source_formats)

        for bitrate, f in zip(bitrates, source_formats or [{}] * len(bitrates)):
            for path, ext in links:
                ff = f.copy()
                if ff:
                    if ext != 'mp4':
                        ff = dict(
                            [(k, v) for k, v in ff.items()
                             if k in ('height', 'width', 'format_id')])
                    ff.update({
                        'format_id': ff['format_id'].replace('hls', ext),
                        'ext': ext,
                        'protocol': 'http',
                    })
                else:
                    ff.update({
                        'format_id': '%s-%d' % (ext, bitrate),
                        'vbr': bitrate,
                    })
                ff['url'] = self._proto_relative_url(
                    '%s%d.%s' % (path, bitrate, ext))
                formats.append(ff)
        self._check_formats(formats, video_id)

        formats.extend(m3u8_formats)
        self._sort_formats(
            formats, field_preference=('height', 'width', 'tbr', 'format_id'))

        subtitles = {}
        for src, src_lang in re.findall(r'<track kind="captions" src="([^"]+)" srclang="([^"]+)"', webpage):
            subtitles[src_lang] = [{
                'ext': src.split('/')[-1],
                'url': 'http://www.funnyordie.com%s' % src,
            }]

        timestamp = unified_timestamp(self._html_search_meta(
            'uploadDate', webpage, 'timestamp', default=None))

        uploader = self._html_search_regex(
            r'<h\d[^>]+\bclass=["\']channel-preview-name[^>]+>(.+?)</h',
            webpage, 'uploader', default=None)

        title, description, thumbnail, duration = [None] * 4

        medium = self._parse_json(
            self._search_regex(
                r'jsonMedium\s*=\s*({.+?});', webpage, 'JSON medium',
                default='{}'),
            video_id, fatal=False)
        if medium:
            title = medium.get('title')
            duration = float_or_none(medium.get('duration'))
            if not timestamp:
                timestamp = unified_timestamp(medium.get('publishDate'))

        post = self._parse_json(
            self._search_regex(
                r'fb_post\s*=\s*(\{.*?\});', webpage, 'post details',
                default='{}'),
            video_id, fatal=False)
        if post:
            if not title:
                title = post.get('name')
            description = post.get('description')
            thumbnail = post.get('picture')

        if not title:
            title = self._og_search_title(webpage)
        if not description:
            description = self._og_search_description(webpage)
        if not duration:
            duration = int_or_none(self._html_search_meta(
                ('video:duration', 'duration'), webpage, 'duration', default=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }
