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
)


class TwitterBaseIE(InfoExtractor):
    def _get_vmap_video_url(self, vmap_url, video_id):
        vmap_data = self._download_xml(vmap_url, video_id)
        return xpath_text(vmap_data, './/MediaFile').strip()


class TwitterCardIE(TwitterBaseIE):
    IE_NAME = 'twitter:card'
    _VALID_URL = r'https?://(?:www\.)?twitter\.com/i/(?:cards/tfw/v1|videos/tweet)/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/560070183650213889',
            # MD5 checksums are different in different places
            'info_dict': {
                'id': '560070183650213889',
                'ext': 'mp4',
                'title': 'Twitter Card',
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
                'title': 'Twitter Card',
                'thumbnail': 're:^https?://.*\.jpg',
                'duration': 80.155,
            },
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/654001591733886977',
            'md5': 'd4724ffe6d2437886d004fa5de1043b3',
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
                'uploader': 'ArsenalTerje',
                'title': 'Vine by ArsenalTerje',
            },
            'add_ie': ['Vine'],
        }, {
            'url': 'https://twitter.com/i/videos/tweet/705235433198714880',
            'md5': '3846d0a07109b5ab622425449b59049d',
            'info_dict': {
                'id': '705235433198714880',
                'ext': 'mp4',
                'title': 'Twitter web player',
                'thumbnail': 're:^https?://.*\.jpg',
            },
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        config = None
        formats = []
        duration = None

        webpage = self._download_webpage(url, video_id)

        iframe_url = self._html_search_regex(
            r'<iframe[^>]+src="((?:https?:)?//(?:www.youtube.com/embed/[^"]+|(?:www\.)?vine\.co/v/\w+/card))"',
            webpage, 'video iframe', default=None)
        if iframe_url:
            return self.url_result(iframe_url)

        config = self._parse_json(self._html_search_regex(
            r'data-(?:player-)?config="([^"]+)"', webpage, 'data player config'),
            video_id)

        if config.get('source_type') == 'vine':
            return self.url_result(config['player_url'], 'Vine')

        def _search_dimensions_in_video_url(a_format, video_url):
            m = re.search(r'/(?P<width>\d+)x(?P<height>\d+)/', video_url)
            if m:
                a_format.update({
                    'width': int(m.group('width')),
                    'height': int(m.group('height')),
                })

        video_url = config.get('video_url') or config.get('playlist', [{}])[0].get('source')

        if video_url:
            f = {
                'url': video_url,
            }

            _search_dimensions_in_video_url(f, video_url)

            formats.append(f)

        vmap_url = config.get('vmapUrl') or config.get('vmap_url')
        if vmap_url:
            formats.append({
                'url': self._get_vmap_video_url(vmap_url, video_id),
            })

        media_info = None

        for entity in config.get('status', {}).get('entities', []):
            if 'mediaInfo' in entity:
                media_info = entity['mediaInfo']

        if media_info:
            for media_variant in media_info['variants']:
                media_url = media_variant['url']
                if media_url.endswith('.m3u8'):
                    formats.extend(self._extract_m3u8_formats(media_url, video_id, ext='mp4', m3u8_id='hls'))
                elif media_url.endswith('.mpd'):
                    formats.extend(self._extract_mpd_formats(media_url, video_id, mpd_id='dash'))
                else:
                    vbr = int_or_none(media_variant.get('bitRate'), scale=1000)
                    a_format = {
                        'url': media_url,
                        'format_id': 'http-%d' % vbr if vbr else 'http',
                        'vbr': vbr,
                    }
                    # Reported bitRate may be zero
                    if not a_format['vbr']:
                        del a_format['vbr']

                    _search_dimensions_in_video_url(a_format, media_url)

                    formats.append(a_format)

            duration = float_or_none(media_info.get('duration', {}).get('nanos'), scale=1e9)

        self._sort_formats(formats)

        title = self._search_regex(r'<title>([^<]+)</title>', webpage, 'title')
        thumbnail = config.get('posterImageUrl') or config.get('image_src')
        duration = float_or_none(config.get('duration')) or duration

        return {
            'id': video_id,
            'title': title,
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
        'info_dict': {
            'id': '643211948184596480',
            'ext': 'mp4',
            'title': 'FREE THE NIPPLE - FTN supporters on Hollywood Blvd today!',
            'thumbnail': 're:^https?://.*\.jpg',
            'description': 'FREE THE NIPPLE on Twitter: "FTN supporters on Hollywood Blvd today! http://t.co/c7jHH749xJ"',
            'uploader': 'FREE THE NIPPLE',
            'uploader_id': 'freethenipple',
        },
        'params': {
            'skip_download': True,  # requires ffmpeg
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
        'expected_warnings': ['height', 'width'],
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
    }, {
        'url': 'https://twitter.com/BTNBrentYarina/status/705235433198714880',
        'info_dict': {
            'id': '705235433198714880',
            'ext': 'mp4',
            'title': 'Brent Yarina - Khalil Iverson\'s missed highlight dunk. And made highlight dunk. In one highlight.',
            'description': 'Brent Yarina on Twitter: "Khalil Iverson\'s missed highlight dunk. And made highlight dunk. In one highlight."',
            'uploader_id': 'BTNBrentYarina',
            'uploader': 'Brent Yarina',
        },
        'params': {
            # The same video as https://twitter.com/i/videos/tweet/705235433198714880
            # Test case of TwitterCardIE
            'skip_download': True,
        },
    }, {
        'url': 'https://twitter.com/jaydingeer/status/700207533655363584',
        'md5': '',
        'info_dict': {
            'id': '700207533655363584',
            'ext': 'mp4',
            'title': 'jay - BEAT PROD: @suhmeduh #Damndaniel',
            'description': 'jay on Twitter: "BEAT PROD: @suhmeduh  https://t.co/HBrQ4AfpvZ #Damndaniel https://t.co/byBooq2ejZ"',
            'thumbnail': 're:^https?://.*\.jpg',
            'uploader': 'jay',
            'uploader_id': 'jaydingeer',
        },
        'params': {
            'skip_download': True,  # requires ffmpeg
        },
    }, {
        'url': 'https://twitter.com/Filmdrunk/status/713801302971588609',
        'md5': '89a15ed345d13b86e9a5a5e051fa308a',
        'info_dict': {
            'id': 'MIOxnrUteUd',
            'ext': 'mp4',
            'title': 'Dr.Pepperの飲み方 #japanese #バカ #ドクペ #電動ガン',
            'uploader': 'TAKUMA',
            'uploader_id': '1004126642786242560',
            'upload_date': '20140615',
        },
        'add_ie': ['Vine'],
    }, {
        'url': 'https://twitter.com/captainamerica/status/719944021058060289',
        # md5 constantly changes
        'info_dict': {
            'id': '719944021058060289',
            'ext': 'mp4',
            'title': 'Captain America - @King0fNerd Are you sure you made the right choice? Find out in theaters.',
            'description': 'Captain America on Twitter: "@King0fNerd Are you sure you made the right choice? Find out in theaters. https://t.co/GpgYi9xMJI"',
            'uploader_id': 'captainamerica',
            'uploader': 'Captain America',
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

        mobj = re.search(r'''(?x)
            <video[^>]+class="animated-gif"(?P<more_info>[^>]+)>\s*
                <source[^>]+video-src="(?P<url>[^"]+)"
        ''', webpage)

        if mobj:
            more_info = mobj.group('more_info')
            height = int_or_none(self._search_regex(
                r'data-height="(\d+)"', more_info, 'height', fatal=False))
            width = int_or_none(self._search_regex(
                r'data-width="(\d+)"', more_info, 'width', fatal=False))
            thumbnail = self._search_regex(
                r'poster="([^"]+)"', more_info, 'poster', fatal=False)
            info.update({
                'id': twid,
                'url': mobj.group('url'),
                'height': height,
                'width': width,
                'thumbnail': thumbnail,
            })
            return info

        if 'class="PlayableMedia' in webpage:
            info.update({
                '_type': 'url_transparent',
                'ie_key': 'TwitterCard',
                'url': '%s//twitter.com/i/videos/tweet/%s' % (self.http_scheme(), twid),
            })

            return info

        raise ExtractorError('There\'s no video in this tweet.')


class TwitterAmplifyIE(TwitterBaseIE):
    IE_NAME = 'twitter:amplify'
    _VALID_URL = 'https?://amp\.twimg\.com/v/(?P<id>[0-9a-f\-]{36})'

    _TEST = {
        'url': 'https://amp.twimg.com/v/0ba0c3c7-0af3-4c0a-bed5-7efd1ffa2951',
        'md5': '7df102d0b9fd7066b86f3159f8e81bf6',
        'info_dict': {
            'id': '0ba0c3c7-0af3-4c0a-bed5-7efd1ffa2951',
            'ext': 'mp4',
            'title': 'Twitter Video',
            'thumbnail': 're:^https?://.*',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vmap_url = self._html_search_meta(
            'twitter:amplify:vmap', webpage, 'vmap url')
        video_url = self._get_vmap_video_url(vmap_url, video_id)

        thumbnails = []
        thumbnail = self._html_search_meta(
            'twitter:image:src', webpage, 'thumbnail', fatal=False)

        def _find_dimension(target):
            w = int_or_none(self._html_search_meta(
                'twitter:%s:width' % target, webpage, fatal=False))
            h = int_or_none(self._html_search_meta(
                'twitter:%s:height' % target, webpage, fatal=False))
            return w, h

        if thumbnail:
            thumbnail_w, thumbnail_h = _find_dimension('image')
            thumbnails.append({
                'url': thumbnail,
                'width': thumbnail_w,
                'height': thumbnail_h,
            })

        video_w, video_h = _find_dimension('player')
        formats = [{
            'url': video_url,
            'width': video_w,
            'height': video_h,
        }]

        return {
            'id': video_id,
            'title': 'Twitter Video',
            'formats': formats,
            'thumbnails': thumbnails,
        }
