# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    determine_ext,
    dict_get,
    ExtractorError,
    float_or_none,
    int_or_none,
    remove_end,
    try_get,
    xpath_text,
)

from .periscope import PeriscopeIE


class TwitterBaseIE(InfoExtractor):
    def _extract_formats_from_vmap_url(self, vmap_url, video_id):
        vmap_data = self._download_xml(vmap_url, video_id)
        video_url = xpath_text(vmap_data, './/MediaFile').strip()
        if determine_ext(video_url) == 'm3u8':
            return self._extract_m3u8_formats(
                video_url, video_id, ext='mp4', m3u8_id='hls',
                entry_protocol='m3u8_native')
        return [{
            'url': video_url,
        }]

    @staticmethod
    def _search_dimensions_in_video_url(a_format, video_url):
        m = re.search(r'/(?P<width>\d+)x(?P<height>\d+)/', video_url)
        if m:
            a_format.update({
                'width': int(m.group('width')),
                'height': int(m.group('height')),
            })


class TwitterCardIE(TwitterBaseIE):
    IE_NAME = 'twitter:card'
    _VALID_URL = r'https?://(?:www\.)?twitter\.com/i/(?:cards/tfw/v1|videos(?:/tweet)?)/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/560070183650213889',
            # MD5 checksums are different in different places
            'info_dict': {
                'id': '560070183650213889',
                'ext': 'mp4',
                'title': 'Twitter Card',
                'thumbnail': r're:^https?://.*\.jpg$',
                'duration': 30.033,
            },
            'skip': 'Video gone',
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/623160978427936768',
            'md5': '7ee2a553b63d1bccba97fbed97d9e1c8',
            'info_dict': {
                'id': '623160978427936768',
                'ext': 'mp4',
                'title': 'Twitter Card',
                'thumbnail': r're:^https?://.*\.jpg',
                'duration': 80.155,
            },
            'skip': 'Video gone',
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/654001591733886977',
            'md5': 'b6d9683dd3f48e340ded81c0e917ad46',
            'info_dict': {
                'id': 'dq4Oj5quskI',
                'ext': 'mp4',
                'title': 'Ubuntu 11.10 Overview',
                'description': 'md5:a831e97fa384863d6e26ce48d1c43376',
                'upload_date': '20111013',
                'uploader': 'OMG! Ubuntu!',
                'uploader_id': 'omgubuntu',
            },
            'add_ie': ['Youtube'],
        },
        {
            'url': 'https://twitter.com/i/cards/tfw/v1/665289828897005568',
            'md5': '6dabeaca9e68cbb71c99c322a4b42a11',
            'info_dict': {
                'id': 'iBb2x00UVlv',
                'ext': 'mp4',
                'upload_date': '20151113',
                'uploader_id': '1189339351084113920',
                'uploader': 'ArsenalTerje',
                'title': 'Vine by ArsenalTerje',
                'timestamp': 1447451307,
            },
            'add_ie': ['Vine'],
        }, {
            'url': 'https://twitter.com/i/videos/tweet/705235433198714880',
            'md5': '884812a2adc8aaf6fe52b15ccbfa3b88',
            'info_dict': {
                'id': '705235433198714880',
                'ext': 'mp4',
                'title': 'Twitter web player',
                'thumbnail': r're:^https?://.*',
            },
        }, {
            'url': 'https://twitter.com/i/videos/752274308186120192',
            'only_matching': True,
        },
    ]

    def _parse_media_info(self, media_info, video_id):
        formats = []
        for media_variant in media_info.get('variants', []):
            media_url = media_variant['url']
            if media_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(media_url, video_id, ext='mp4', m3u8_id='hls'))
            elif media_url.endswith('.mpd'):
                formats.extend(self._extract_mpd_formats(media_url, video_id, mpd_id='dash'))
            else:
                vbr = int_or_none(dict_get(media_variant, ('bitRate', 'bitrate')), scale=1000)
                a_format = {
                    'url': media_url,
                    'format_id': 'http-%d' % vbr if vbr else 'http',
                    'vbr': vbr,
                }
                # Reported bitRate may be zero
                if not a_format['vbr']:
                    del a_format['vbr']

                self._search_dimensions_in_video_url(a_format, media_url)

                formats.append(a_format)
        return formats

    def _extract_mobile_formats(self, username, video_id):
        webpage = self._download_webpage(
            'https://mobile.twitter.com/%s/status/%s' % (username, video_id),
            video_id, 'Downloading mobile webpage',
            headers={
                # A recent mobile UA is necessary for `gt` cookie
                'User-Agent': 'Mozilla/5.0 (Android 6.0.1; Mobile; rv:54.0) Gecko/54.0 Firefox/54.0',
            })
        main_script_url = self._html_search_regex(
            r'<script[^>]+src="([^"]+main\.[^"]+)"', webpage, 'main script URL')
        main_script = self._download_webpage(
            main_script_url, video_id, 'Downloading main script')
        bearer_token = self._search_regex(
            r'BEARER_TOKEN\s*:\s*"([^"]+)"',
            main_script, 'bearer token')
        guest_token = self._search_regex(
            r'document\.cookie\s*=\s*decodeURIComponent\("gt=(\d+)',
            webpage, 'guest token')
        api_data = self._download_json(
            'https://api.twitter.com/2/timeline/conversation/%s.json' % video_id,
            video_id, 'Downloading mobile API data',
            headers={
                'Authorization': 'Bearer ' + bearer_token,
                'x-guest-token': guest_token,
            })
        media_info = try_get(api_data, lambda o: o['globalObjects']['tweets'][video_id]
                                                  ['extended_entities']['media'][0]['video_info']) or {}
        return self._parse_media_info(media_info, video_id)

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
            r'data-(?:player-)?config="([^"]+)"', webpage,
            'data player config', default='{}'),
            video_id)

        if config.get('source_type') == 'vine':
            return self.url_result(config['player_url'], 'Vine')

        periscope_url = PeriscopeIE._extract_url(webpage)
        if periscope_url:
            return self.url_result(periscope_url, PeriscopeIE.ie_key())

        video_url = config.get('video_url') or config.get('playlist', [{}])[0].get('source')

        if video_url:
            if determine_ext(video_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(video_url, video_id, ext='mp4', m3u8_id='hls'))
            else:
                f = {
                    'url': video_url,
                }

                self._search_dimensions_in_video_url(f, video_url)

                formats.append(f)

        vmap_url = config.get('vmapUrl') or config.get('vmap_url')
        if vmap_url:
            formats.extend(
                self._extract_formats_from_vmap_url(vmap_url, video_id))

        media_info = None

        for entity in config.get('status', {}).get('entities', []):
            if 'mediaInfo' in entity:
                media_info = entity['mediaInfo']

        if media_info:
            formats.extend(self._parse_media_info(media_info, video_id))
            duration = float_or_none(media_info.get('duration', {}).get('nanos'), scale=1e9)

        username = config.get('user', {}).get('screen_name')
        if username:
            formats.extend(self._extract_mobile_formats(username, video_id))

        self._remove_duplicate_formats(formats)
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
            'thumbnail': r're:^https?://.*\.jpg',
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
            'thumbnail': r're:^https?://.*\.png',
            'uploader': 'Gifs',
            'uploader_id': 'giphz',
        },
        'expected_warnings': ['height', 'width'],
        'skip': 'Account suspended',
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
            'title': 'Donte - BEAT PROD: @suhmeduh #Damndaniel',
            'description': 'Donte on Twitter: "BEAT PROD: @suhmeduh  https://t.co/HBrQ4AfpvZ #Damndaniel https://t.co/byBooq2ejZ"',
            'thumbnail': r're:^https?://.*\.jpg',
            'uploader': 'Donte',
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
            'title': 'FilmDrunk - Vine of the day',
            'description': 'FilmDrunk on Twitter: "Vine of the day https://t.co/xmTvRdqxWf"',
            'uploader': 'FilmDrunk',
            'uploader_id': 'Filmdrunk',
            'timestamp': 1402826626,
            'upload_date': '20140615',
        },
        'add_ie': ['Vine'],
    }, {
        'url': 'https://twitter.com/captainamerica/status/719944021058060289',
        'info_dict': {
            'id': '719944021058060289',
            'ext': 'mp4',
            'title': 'Captain America - @King0fNerd Are you sure you made the right choice? Find out in theaters.',
            'description': 'Captain America on Twitter: "@King0fNerd Are you sure you made the right choice? Find out in theaters. https://t.co/GpgYi9xMJI"',
            'uploader_id': 'captainamerica',
            'uploader': 'Captain America',
        },
        'params': {
            'skip_download': True,  # requires ffmpeg
        },
    }, {
        'url': 'https://twitter.com/OPP_HSD/status/779210622571536384',
        'info_dict': {
            'id': '1zqKVVlkqLaKB',
            'ext': 'mp4',
            'title': 'Sgt Kerry Schmidt - LIVE on #Periscope: Road rage, mischief, assault, rollover and fire in one occurrence',
            'description': 'Sgt Kerry Schmidt on Twitter: "LIVE on #Periscope: Road rage, mischief, assault, rollover and fire in one occurrence  https://t.co/EKrVgIXF3s"',
            'upload_date': '20160923',
            'uploader_id': 'OPP_HSD',
            'uploader': 'Sgt Kerry Schmidt',
            'timestamp': 1474613214,
        },
        'add_ie': ['Periscope'],
    }, {
        # has mp4 formats via mobile API
        'url': 'https://twitter.com/news_al3alm/status/852138619213144067',
        'info_dict': {
            'id': '852138619213144067',
            'ext': 'mp4',
            'title': 'عالم الأخبار - كلمة تاريخية بجلسة الجناسي التاريخية.. النائب خالد مؤنس العتيبي للمعارضين : اتقوا الله .. الظلم ظلمات يوم القيامة',
            'description': 'عالم الأخبار on Twitter: "كلمة تاريخية بجلسة الجناسي التاريخية.. النائب خالد مؤنس العتيبي للمعارضين : اتقوا الله .. الظلم ظلمات يوم القيامة   https://t.co/xg6OhpyKfN"',
            'uploader': 'عالم الأخبار',
            'uploader_id': 'news_al3alm',
        },
        'params': {
            'format': 'best[format_id^=http-]',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('user_id')
        twid = mobj.group('id')

        webpage, urlh = self._download_webpage_handle(
            self._TEMPLATE_URL % (user_id, twid), twid)

        if 'twitter.com/account/suspended' in urlh.geturl():
            raise ExtractorError('Account suspended by Twitter.', expected=True)

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

        twitter_card_url = None
        if 'class="PlayableMedia' in webpage:
            twitter_card_url = '%s//twitter.com/i/videos/tweet/%s' % (self.http_scheme(), twid)
        else:
            twitter_card_iframe_url = self._search_regex(
                r'data-full-card-iframe-url=([\'"])(?P<url>(?:(?!\1).)+)\1',
                webpage, 'Twitter card iframe URL', default=None, group='url')
            if twitter_card_iframe_url:
                twitter_card_url = compat_urlparse.urljoin(url, twitter_card_iframe_url)

        if twitter_card_url:
            info.update({
                '_type': 'url_transparent',
                'ie_key': 'TwitterCard',
                'url': twitter_card_url,
            })
            return info

        raise ExtractorError('There\'s no video in this tweet.')


class TwitterAmplifyIE(TwitterBaseIE):
    IE_NAME = 'twitter:amplify'
    _VALID_URL = r'https?://amp\.twimg\.com/v/(?P<id>[0-9a-f\-]{36})'

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
        formats = self._extract_formats_from_vmap_url(vmap_url, video_id)

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
        formats[0].update({
            'width': video_w,
            'height': video_h,
        })

        return {
            'id': video_id,
            'title': 'Twitter Video',
            'formats': formats,
            'thumbnails': thumbnails,
        }
