# coding: utf-8
from __future__ import unicode_literals

import itertools
import json
import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    int_or_none,
    js_to_json,
    mimetype2ext,
    sanitized_Request,
    unified_strdate,
)


class SandiaIE(InfoExtractor):
    IE_DESC = 'Sandia National Laboratories'
    _VALID_URL = r'https?://digitalops\.sandia\.gov/Mediasite/Play/(?P<id>[0-9a-f]+)'
    _TEST = {
        'url': 'http://digitalops.sandia.gov/Mediasite/Play/24aace4429fc450fb5b38cdbf424a66e1d',
        'md5': '9422edc9b9a60151727e4b6d8bef393d',
        'info_dict': {
            'id': '24aace4429fc450fb5b38cdbf424a66e1d',
            'ext': 'mp4',
            'title': 'Xyce Software Training - Section 1',
            'description': 're:(?s)SAND Number: SAND 2013-7800.{200,}',
            'upload_date': '20120904',
            'duration': 7794,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        req = sanitized_Request(url)
        req.add_header('Cookie', 'MediasitePlayerCaps=ClientPlugins=4')
        webpage = self._download_webpage(req, video_id)

        js_path = self._search_regex(
            r'<script type="text/javascript" src="(/Mediasite/FileServer/Presentation/[^"]+)"',
            webpage, 'JS code URL')
        js_url = compat_urlparse.urljoin(url, js_path)

        js_code = self._download_webpage(
            js_url, video_id, note='Downloading player')

        def extract_str(key, **args):
            return self._search_regex(
                r'Mediasite\.PlaybackManifest\.%s\s*=\s*(.+);\s*?\n' % re.escape(key),
                js_code, key, **args)

        def extract_data(key, **args):
            data_json = extract_str(key, **args)
            if data_json is None:
                return data_json
            return self._parse_json(
                data_json, video_id, transform_source=js_to_json)

        formats = []
        for i in itertools.count():
            fd = extract_data('VideoUrls[%d]' % i, default=None)
            if fd is None:
                break
            formats.append({
                'format_id': '%s' % i,
                'format_note': fd['MimeType'].partition('/')[2],
                'ext': mimetype2ext(fd['MimeType']),
                'url': fd['Location'],
                'protocol': 'f4m' if fd['MimeType'] == 'video/x-mp4-fragmented' else None,
            })
        self._sort_formats(formats)

        slide_baseurl = compat_urlparse.urljoin(
            url, extract_data('SlideBaseUrl'))
        slide_template = slide_baseurl + re.sub(
            r'\{0:D?([0-9+])\}', r'%0\1d', extract_data('SlideImageFileNameTemplate'))
        slides = []
        last_slide_time = 0
        for i in itertools.count(1):
            sd = extract_str('Slides[%d]' % i, default=None)
            if sd is None:
                break
            timestamp = int_or_none(self._search_regex(
                r'^Mediasite\.PlaybackManifest\.CreateSlide\("[^"]*"\s*,\s*([0-9]+),',
                sd, 'slide %s timestamp' % i, fatal=False))
            slides.append({
                'url': slide_template % i,
                'duration': timestamp - last_slide_time,
            })
            last_slide_time = timestamp
        formats.append({
            'format_id': 'slides',
            'protocol': 'slideshow',
            'url': json.dumps(slides),
            'preference': -10000,  # Downloader not yet written
        })
        self._sort_formats(formats)

        title = extract_data('Title')
        description = extract_data('Description', fatal=False)
        duration = int_or_none(extract_data(
            'Duration', fatal=False), scale=1000)
        upload_date = unified_strdate(extract_data('AirDate', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'upload_date': upload_date,
            'duration': duration,
        }
