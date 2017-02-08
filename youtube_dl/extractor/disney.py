# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    compat_str,
    determine_ext,
)


class DisneyIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?P<domain>(?:[^/]+\.)?(?:disney\.[a-z]{2,3}(?:\.[a-z]{2})?|disney(?:(?:me|latino)\.com|turkiye\.com\.tr)|starwars\.com))/(?:embed/|(?:[^/]+/)+[\w-]+-)(?P<id>[a-z0-9]{24})'''
    _TESTS = [{
        'url': 'http://video.disney.com/watch/moana-trailer-545ed1857afee5a0ec239977',
        'info_dict': {
            'id': '545ed1857afee5a0ec239977',
            'ext': 'mp4',
            'title': 'Moana - Trailer',
            'description': 'A fun adventure for the entire Family!  Bring home Moana on Digital HD Feb 21 & Blu-ray March 7',
            'upload_date': '20170112',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'http://videos.disneylatino.com/ver/spider-man-de-regreso-a-casa-primer-adelanto-543a33a1850bdcfcca13bae2',
        'only_matching': True,
    }, {
        'url': 'http://video.en.disneyme.com/watch/future-worm/robo-carp-2001-544b66002aa7353cdd3f5114',
        'only_matching': True,
    }, {
        'url': 'http://video.disneyturkiye.com.tr/izle/7c-7-cuceler/kimin-sesi-zaten-5456f3d015f6b36c8afdd0e2',
        'only_matching': True,
    }, {
        'url': 'http://disneyjunior.disney.com/embed/546a4798ddba3d1612e4005d',
        'only_matching': True,
    }, {
        'url': 'http://www.starwars.com/embed/54690d1e6c42e5f09a0fb097',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        domain, video_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(
            'http://%s/embed/%s' % (domain, video_id), video_id)
        video_data = self._parse_json(self._search_regex(
            r'Disney\.EmbedVideo=({.+});', webpage, 'embed data'), video_id)['video']

        for external in video_data.get('externals', []):
            if external.get('source') == 'vevo':
                return self.url_result('vevo:' + external['data_id'], 'Vevo')

        title = video_data['title']

        formats = []
        for flavor in video_data.get('flavors', []):
            flavor_format = flavor.get('format')
            flavor_url = flavor.get('url')
            if not flavor_url or not re.match(r'https?://', flavor_url):
                continue
            tbr = int_or_none(flavor.get('bitrate'))
            if tbr == 99999:
                formats.extend(self._extract_m3u8_formats(
                    flavor_url, video_id, 'mp4', m3u8_id=flavor_format, fatal=False))
                continue
            format_id = []
            if flavor_format:
                format_id.append(flavor_format)
            if tbr:
                format_id.append(compat_str(tbr))
            ext = determine_ext(flavor_url)
            if flavor_format == 'applehttp' or ext == 'm3u8':
                ext = 'mp4'
            width = int_or_none(flavor.get('width'))
            height = int_or_none(flavor.get('height'))
            formats.append({
                'format_id': '-'.join(format_id),
                'url': flavor_url,
                'width': width,
                'height': height,
                'tbr': tbr,
                'ext': ext,
                'vcodec': 'none' if (width == 0 and height == 0) else None,
            })
        self._sort_formats(formats)

        subtitles = {}
        for caption in video_data.get('captions', []):
            caption_url = caption.get('url')
            caption_format = caption.get('format')
            if not caption_url or caption_format.startswith('unknown'):
                continue
            subtitles.setdefault(caption.get('language', 'en'), []).append({
                'url': caption_url,
                'ext': {
                    'webvtt': 'vtt',
                }.get(caption_format, caption_format),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description') or video_data.get('short_desc'),
            'thumbnail': video_data.get('thumb') or video_data.get('thumb_secure'),
            'duration': int_or_none(video_data.get('duration_sec')),
            'upload_date': unified_strdate(video_data.get('publish_date')),
            'formats': formats,
            'subtitles': subtitles,
        }
