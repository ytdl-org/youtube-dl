# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError, js_to_json, urljoin


class SexDotComIE(InfoExtractor):
    IE_DESC = 'Sex.com'
    _VALID_URL = r'https?://(?:www\.)?sex\.com/pin/(?P<id>[0-9]+)'
    _TESTS = [{
        # Direct video, two formats
        'url': 'https://www.sex.com/pin/55064004-jessica-nigri-cosplay/',
        'md5': 'd1c14632c1c453ee680c94533bc01321',
        'info_dict': {
            'id': '55064004',
            'ext': 'mp4',
            'title': 'Jessica Nigri Cosplay',
            'formats': [
                {'ext': 'mp4', 'format_id': 'SD', 'height': 360},
                {'ext': 'mp4', 'format_id': 'HD', 'height': 720},
            ],
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # Embedded youtube.com
        'url': 'https://www.sex.com/pin/54022740-bella-hadid-cannes-2016-red-dress-hd/',
        'info_dict': {
            'id': 'bZgp8wOEaKY',
            'ext': 'mp4',
            'upload_date': '20160526',
            'title': 'Bella Hadid robe tapis rouge Cannes 2016',
            'uploader': 'Véronique ESPINASSE',
            'description': 'Innocente beauté...',
            'uploader_id': 'UCIgl6XJAreFl0wwaN1wm3Pg',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # Embedded xhamster.com
        'url': 'https://www.sex.com/pin/56529538-flawless-tease/',
        'info_dict': {
            'id': '8461824',
            'ext': 'mp4',
            'title': 'shorts tease',
            'age_limit': 18,
            'upload_date': '20171031',
            'uploader': 'anatolio',
            'timestamp': 1509470696,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # gif
        'url': 'https://www.sex.com/pin/55000357-cat-4/',
        'md5': 'bba5e04e0555e928852b3ab05c93f1a9',
        'info_dict': {
            'id': '55000357',
            'ext': 'gif',
            'title': 'cat 4',
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # image
        'url': 'https://www.sex.com/pin/35756851/',
        'md5': 'fc174f007933b0cae74682ca3532e423',
        'info_dict': {
            'id': '35756851',
            'ext': 'jpg',
            'title': 'Pin #35756851',
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'(?s)<h1[^>]*>.*?<span[^>]+(["\']?)name\1[^>]*>(?P<title>.+?)</span>.*</h1>',
            webpage, 'title', group='title', fatal=False)
        if not title:
            # We prefer the above title; 'og:title' also contains uploader name
            title = self._og_search_title(webpage)

        # Direct video
        formats = self._try_videojs(webpage, url, video_id)
        if formats:
            return {
                'id': video_id,
                'title': title,
                'formats': formats,
                'age_limit': 18,
            }

        # It's fairly difficult to distinguish between the various advert
        # <iframe>s and the one embedding real content.
        # So we find the "image_frame" div first, content is always its child.
        container = self._search_regex(
            r'(?s)<div[^>]+class=(["\']?)image_frame\1[^>]*>(?P<content>.+?)</div>',
            webpage, 'content container', group='content')

        # Try embedded content iframe; YouTube, XHamster, XVideos and more.
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//.*?)\1', container)
        if mobj:
            return self.url_result(
                mobj.group('url'), video_id=video_id, video_title=title)

        # Try image or gif
        mobj = re.search(r'<img[^>]+src=(["\'])(?P<url>.+?)\1', container)
        if mobj:
            img_url = urljoin(url, mobj.group('url'))
            return {
                'id': video_id,
                'title': title,
                'url': img_url,
                'http_headers': {
                    'Referer': url,
                },
                'age_limit': 18,
            }

        raise ExtractorError('%s: Cannot identify content in container' % video_id)

    def _try_videojs(self, webpage, url, video_id):
        """Parse arguments of videojs updateSrc() method call."""

        mobj = re.search(r'[a-z]\.updateSrc\s*\((?P<sources>[^)]+?)\)', webpage)
        if not mobj:
            return None

        sources = self._parse_json(
            mobj.group('sources'), video_id=video_id,
            transform_source=js_to_json)

        formats = []
        for source in sources:
            if 'src' not in source or 'type' not in source:
                self.report_warning(
                    '%s: Unable to handle source: %r' % (video_id, source))
                continue

            _type = source['type']
            formats.append({
                'url': urljoin(url, source['src']),
                'ext': _type[6:] if _type.startswith('video/') else None,
                'format_id': source.get('label'),
                'height': source.get('res'),
            })

        self._sort_formats(formats)
        return formats
