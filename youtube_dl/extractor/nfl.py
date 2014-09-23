# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    remove_end,
)


class NFLIE(InfoExtractor):
    IE_NAME = 'nfl.com'
    _VALID_URL = r'(?x)https?://(?:www\.)?nfl\.com/(?:videos/(?:.+)/|.*?\#video=)(?P<id>\d..[0-9]+)'
    _PLAYER_CONFIG_URL = 'http://www.nfl.com/static/content/static/config/video/config.json'
    _TEST = {
        'url': 'http://www.nfl.com/videos/nfl-game-highlights/0ap3000000398478/Week-3-Redskins-vs-Eagles-highlights',
        # 'md5': '5eb8c40a727dda106d510e5d6ffa79e5',  # md5 checksum fluctuates
        'info_dict': {
            'id': '0ap3000000398478',
            'ext': 'mp4',
            'title': 'Week 3: Washington Redskins vs. Philadelphia Eagles highlights',
            'description': 'md5:56323bfb0ac4ee5ab24bd05fdf3bf478',
            'upload_date': '20140921',
            'timestamp': 1411337580,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        config = self._download_json(self._PLAYER_CONFIG_URL, video_id,
                                     note='Downloading player config')
        url_template = 'http://nfl.com{contentURLTemplate:s}'.format(**config)
        video_data = self._download_json(url_template.format(id=video_id), video_id)

        cdns = config.get('cdns')
        if not cdns:
            raise ExtractorError('Failed to get CDN data', expected=True)

        formats = []
        streams = video_data.get('cdnData', {}).get('bitrateInfo', [])
        for name, cdn in cdns.items():
            # LimeLight streams don't seem to work
            if cdn.get('name') == 'LIMELIGHT':
                continue

            protocol = cdn.get('protocol')
            host = remove_end(cdn.get('host', ''), '/')
            if not (protocol and host):
                continue

            path_prefix = cdn.get('pathprefix', '')
            if path_prefix and not path_prefix.endswith('/'):
                path_prefix = '%s/' % path_prefix

            get_url = lambda p: '{protocol:s}://{host:s}/{prefix:s}{path:}'.format(
                protocol=protocol,
                host=host,
                prefix=path_prefix,
                path=p,
            )

            if protocol == 'rtmp':
                preference = -2
            elif 'prog' in name.lower():
                preference = -1
            else:
                preference = 0

            for stream in streams:
                path = stream.get('path')
                if not path:
                    continue

                formats.append({
                    'url': get_url(path),
                    'vbr': int_or_none(stream.get('rate', 0), 1000),
                    'preference': preference,
                    'format_note': name,
                })

        self._sort_formats(formats)

        thumbnail = None
        for q in ('xl', 'l', 'm', 's', 'xs'):
            thumbnail = video_data.get('imagePaths', {}).get(q)
            if thumbnail:
                break

        return {
            'id': video_id,
            'title': video_data.get('storyHeadline'),
            'formats': formats,
            'description': video_data.get('caption'),
            'duration': video_data.get('duration'),
            'thumbnail': thumbnail,
            'timestamp': int_or_none(video_data.get('posted'), 1000),
        }
