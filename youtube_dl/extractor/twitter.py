# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request
from ..utils import (
    float_or_none,
    xpath_text,
    remove_end,
)


class TwitterCardIE(InfoExtractor):
    IE_NAME = 'twitter:card'
    _VALID_URL = r'https?://(?:www\.)?twitter\.com/i/cards/tfw/v1/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/560070183650213889',
            'md5': '7d2f6b4d2eb841a7ccc893d479bfceb4',
            'info_dict': {
                'id': '560070183650213889',
                'ext': 'mp4',
                'title': 'TwitterCard',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 30.033,
            }
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/623160978427936768',
            'md5': '7ee2a553b63d1bccba97fbed97d9e1c8',
            'info_dict': {
                'id': '623160978427936768',
                'ext': 'mp4',
                'title': 'TwitterCard',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 80.155,
            },
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Different formats served for different User-Agents
        USER_AGENTS = [
            'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)',  # mp4
            'Mozilla/5.0 (Windows NT 5.2; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',  # webm
        ]

        config = None
        formats = []
        for user_agent in USER_AGENTS:
            request = compat_urllib_request.Request(url)
            request.add_header('User-Agent', user_agent)
            webpage = self._download_webpage(request, video_id)

            config = self._parse_json(self._html_search_regex(
                r'data-player-config="([^"]+)"', webpage, 'data player config'),
                video_id)
            if 'playlist' not in config:
                if 'vmapUrl' in config:
                    vmap_data = self._download_xml(config['vmapUrl'], video_id)
                    video_url = xpath_text(vmap_data, './/MediaFile').strip()
                    formats.append({
                        'url': video_url,
                    })
                    break   # same video regardless of UA
                continue

            video_url = config['playlist'][0]['source']

            f = {
                'url': video_url,
            }

            m = re.search(r'/(?P<width>\d+)x(?P<height>\d+)/', video_url)
            if m:
                f.update({
                    'width': int(m.group('width')),
                    'height': int(m.group('height')),
                })
            formats.append(f)
        self._sort_formats(formats)

        thumbnail = config.get('posterImageUrl')
        duration = float_or_none(config.get('duration'))

        return {
            'id': video_id,
            'title': 'TwitterCard',
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }


class TwitterIE(InfoExtractor):
    IE_NAME = 'twitter'
    _VALID_URL = r'https?://(?:www\.|m\.|mobile\.)?twitter\.com/(?P<user_id>[^/]+)/status/(?P<id>\d+)'
    _TEMPLATE_URL = 'https://twitter.com/%s/status/%s'

    _TEST = {
        'url': 'https://twitter.com/freethenipple/status/643211948184596480',
        'md5': '31cd83a116fc41f99ae3d909d4caf6a0',
        'info_dict': {
            'id': '643211948184596480',
            'ext': 'mp4',
            'title': 'FREE THE NIPPLE - FTN supporters on Hollywood Blvd today!',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 12.922,
            'description': 'FREE THE NIPPLE on Twitter: "FTN supporters on Hollywood Blvd today! http://t.co/c7jHH749xJ"',
            'uploader': 'FREE THE NIPPLE',
            'uploader_id': 'freethenipple',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user_id')
        twid = mobj.group('id')

        webpage = self._download_webpage(self._TEMPLATE_URL % (user_id, twid), twid)

        username = remove_end(self._og_search_title(webpage), ' on Twitter')

        title = self._og_search_description(webpage).strip('').replace('\n', ' ')

        # strip  'https -_t.co_BJYgOjSeGA' junk from filenames
        mobj = re.match(r'“(.*)\s+(http://[^ ]+)”', title)
        title, short_url = mobj.groups()

        card_id = self._search_regex(
            r'["\']/i/cards/tfw/v1/(\d+)', webpage, 'twitter card url')
        card_url = 'https://twitter.com/i/cards/tfw/v1/' + card_id

        return {
            '_type': 'url_transparent',
            'ie_key': 'TwitterCard',
            'uploader_id': user_id,
            'uploader': username,
            'url': card_url,
            'webpage_url': url,
            'description': '%s on Twitter: "%s %s"' % (username, title, short_url),
            'title': username + ' - ' + title,
        }
