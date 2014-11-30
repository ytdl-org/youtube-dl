# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse_urlparse,
    int_or_none,
    remove_end,
)


class NFLIE(InfoExtractor):
    IE_NAME = 'nfl.com'
    _VALID_URL = r'''(?x)https?://
        (?P<host>(?:www\.)?(?:nfl\.com|.*?\.clubs\.nfl\.com))/
        (?:.+?/)*
        (?P<id>(?:\d[a-z]{2}\d{13}|\w{8}\-(?:\w{4}\-){3}\w{12}))'''
    _TESTS = [
        {
            'url': 'http://www.nfl.com/videos/nfl-game-highlights/0ap3000000398478/Week-3-Redskins-vs-Eagles-highlights',
            'md5': '394ef771ddcd1354f665b471d78ec4c6',
            'info_dict': {
                'id': '0ap3000000398478',
                'ext': 'mp4',
                'title': 'Week 3: Redskins vs. Eagles highlights',
                'description': 'md5:56323bfb0ac4ee5ab24bd05fdf3bf478',
                'upload_date': '20140921',
                'timestamp': 1411337580,
                'thumbnail': 're:^https?://.*\.jpg$',
            }
        },
        {
            'url': 'http://prod.www.steelers.clubs.nfl.com/video-and-audio/videos/LIVE_Post_Game_vs_Browns/9d72f26a-9e2b-4718-84d3-09fb4046c266',
            'md5': 'cf85bdb4bc49f6e9d3816d130c78279c',
            'info_dict': {
                'id': '9d72f26a-9e2b-4718-84d3-09fb4046c266',
                'ext': 'mp4',
                'title': 'LIVE: Post Game vs. Browns',
                'description': 'md5:6a97f7e5ebeb4c0e69a418a89e0636e8',
                'upload_date': '20131229',
                'timestamp': 1388354455,
                'thumbnail': 're:^https?://.*\.jpg$',
            }
        }
    ]

    @staticmethod
    def prepend_host(host, url):
        if not url.startswith('http'):
            if not url.startswith('/'):
                url = '/%s' % url
            url = 'http://{0:}{1:}'.format(host, url)
        return url

    @staticmethod
    def format_from_stream(stream, protocol, host, path_prefix='',
                           preference=0, note=None):
        url = '{protocol:}://{host:}/{prefix:}{path:}'.format(
            protocol=protocol,
            host=host,
            prefix=path_prefix,
            path=stream.get('path'),
        )
        return {
            'url': url,
            'vbr': int_or_none(stream.get('rate', 0), 1000),
            'preference': preference,
            'format_note': note,
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, host = mobj.group('id'), mobj.group('host')

        webpage = self._download_webpage(url, video_id)

        config_url = NFLIE.prepend_host(host, self._search_regex(
            r'(?:config|configURL)\s*:\s*"([^"]+)"', webpage, 'config URL'))
        config = self._download_json(config_url, video_id,
                                     note='Downloading player config')
        url_template = NFLIE.prepend_host(
            host, '{contentURLTemplate:}'.format(**config))
        video_data = self._download_json(
            url_template.format(id=video_id), video_id)

        formats = []
        cdn_data = video_data.get('cdnData', {})
        streams = cdn_data.get('bitrateInfo', [])
        if cdn_data.get('format') == 'EXTERNAL_HTTP_STREAM':
            parts = compat_urllib_parse_urlparse(cdn_data.get('uri'))
            protocol, host = parts.scheme, parts.netloc
            for stream in streams:
                formats.append(
                    NFLIE.format_from_stream(stream, protocol, host))
        else:
            cdns = config.get('cdns')
            if not cdns:
                raise ExtractorError('Failed to get CDN data', expected=True)

            for name, cdn in cdns.items():
                # LimeLight streams don't seem to work
                if cdn.get('name') == 'LIMELIGHT':
                    continue

                protocol = cdn.get('protocol')
                host = remove_end(cdn.get('host', ''), '/')
                if not (protocol and host):
                    continue

                prefix = cdn.get('pathprefix', '')
                if prefix and not prefix.endswith('/'):
                    prefix = '%s/' % prefix

                preference = 0
                if protocol == 'rtmp':
                    preference = -2
                elif 'prog' in name.lower():
                    preference = 1

                for stream in streams:
                    formats.append(
                        NFLIE.format_from_stream(stream, protocol, host,
                                                 prefix, preference, name))

        self._sort_formats(formats)

        thumbnail = None
        for q in ('xl', 'l', 'm', 's', 'xs'):
            thumbnail = video_data.get('imagePaths', {}).get(q)
            if thumbnail:
                break

        return {
            'id': video_id,
            'title': video_data.get('headline'),
            'formats': formats,
            'description': video_data.get('caption'),
            'duration': video_data.get('duration'),
            'thumbnail': thumbnail,
            'timestamp': int_or_none(video_data.get('posted'), 1000),
        }
