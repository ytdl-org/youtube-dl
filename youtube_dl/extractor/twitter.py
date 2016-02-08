# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    xpath_text,
    remove_end,
    int_or_none,
    ExtractorError,
    sanitized_Request,
)


class TwitterCardIE(InfoExtractor):
    IE_NAME = 'twitter:card'
    _VALID_URL = r'https?://(?:www\.)?twitter\.com/i/cards/tfw/v1/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/560070183650213889',
            'md5': '4fa26a35f9d1bf4b646590ba8e84be19',
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
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/654001591733886977',
            'md5': 'b6f35e8b08a0bec6c8af77a2f4b3a814',
            'info_dict': {
                'id': 'dq4Oj5quskI',
                'ext': 'mp4',
                'title': 'Ubuntu 11.10 Overview',
                'description': 'Take a quick peek at what\'s new and improved in Ubuntu 11.10.\n\nOnce installed take a look at 10 Things to Do After Installing: http://www.omgubuntu.co.uk/2011/10/10-things-to-do-after-installing-ubuntu-11-10/',
                'upload_date': '20111013',
                'uploader': 'OMG! Ubuntu!',
                'uploader_id': 'omgubuntu',
            },
            'add_ie': ['Youtube'],
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/665289828897005568',
            'md5': 'ab2745d0b0ce53319a534fccaa986439',
            'info_dict': {
                'id': 'iBb2x00UVlv',
                'ext': 'mp4',
                'upload_date': '20151113',
                'uploader_id': '1189339351084113920',
                'uploader': '@ArsenalTerje',
                'title': 'Vine by @ArsenalTerje',
            },
            'add_ie': ['Vine'],
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
            request = sanitized_Request(url)
            request.add_header('User-Agent', user_agent)
            webpage = self._download_webpage(request, video_id)

            iframe_url = self._html_search_regex(
                r'<iframe[^>]+src="((?:https?:)?//(?:www.youtube.com/embed/[^"]+|(?:www\.)?vine\.co/v/\w+/card))"',
                webpage, 'video iframe', default=None)
            if iframe_url:
                return self.url_result(iframe_url)

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

    _TESTS = [{
        'url': 'https://twitter.com/freethenipple/status/643211948184596480',
        'md5': 'db6612ec5d03355953c3ca9250c97e5e',
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
    }, {
        'url': 'https://twitter.com/giphz/status/657991469417025536/photo/1',
        'md5': 'f36dcd5fb92bf7057f155e7d927eeb42',
        'info_dict': {
            'id': '657991469417025536',
            'ext': 'mp4',
            'title': 'Gifs - tu vai cai tu vai cai tu nao eh capaz disso tu vai cai',
            'description': 'Gifs on Twitter: "tu vai cai tu vai cai tu nao eh capaz disso tu vai cai https://t.co/tM46VHFlO5"',
            'thumbnail': 're:^https?://.*\.png',
            'uploader': 'Gifs',
            'uploader_id': 'giphz',
        },
    }, {
        'url': 'https://twitter.com/starwars/status/665052190608723968',
        'md5': '39b7199856dee6cd4432e72c74bc69d4',
        'info_dict': {
            'id': '665052190608723968',
            'ext': 'mp4',
            'title': 'Star Wars - A new beginning is coming December 18. Watch the official 60 second #TV spot for #StarWars: #TheForceAwakens.',
            'description': 'Star Wars on Twitter: "A new beginning is coming December 18. Watch the official 60 second #TV spot for #StarWars: #TheForceAwakens."',
            'uploader_id': 'starwars',
            'uploader': 'Star Wars',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user_id')
        twid = mobj.group('id')

        webpage = self._download_webpage(self._TEMPLATE_URL % (user_id, twid), twid)

        username = remove_end(self._og_search_title(webpage), ' on Twitter')

        title = description = self._og_search_description(webpage).strip('').replace('\n', ' ').strip('“”')

        # strip  'https -_t.co_BJYgOjSeGA' junk from filenames
        title = re.sub(r'\s+(https?://[^ ]+)', '', title)

        info = {
            'uploader_id': user_id,
            'uploader': username,
            'webpage_url': url,
            'description': '%s on Twitter: "%s"' % (username, description),
            'title': username + ' - ' + title,
        }

        card_id = self._search_regex(
            r'["\']/i/cards/tfw/v1/(\d+)', webpage, 'twitter card url', default=None)
        if card_id:
            card_url = 'https://twitter.com/i/cards/tfw/v1/' + card_id
            info.update({
                '_type': 'url_transparent',
                'ie_key': 'TwitterCard',
                'url': card_url,
            })
            return info

        mobj = re.search(r'''(?x)
            <video[^>]+class="animated-gif"[^>]+
                (?:data-height="(?P<height>\d+)")?[^>]+
                (?:data-width="(?P<width>\d+)")?[^>]+
                (?:poster="(?P<poster>[^"]+)")?[^>]*>\s*
                <source[^>]+video-src="(?P<url>[^"]+)"
        ''', webpage)

        if mobj:
            info.update({
                'id': twid,
                'url': mobj.group('url'),
                'height': int_or_none(mobj.group('height')),
                'width': int_or_none(mobj.group('width')),
                'thumbnail': mobj.group('poster'),
            })
            return info

        raise ExtractorError('There\'s not video in this tweet.')
