# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    str_or_none,
    unified_timestamp,
)


class TegnaMediaIE(InfoExtractor):
    SUBSCRIPTION_KEY = ''

    def _real_extract(self, url):
        show_id = self._match_id(url)
        webpage = self._download_webpage(url, show_id)

        player_info = self._html_search_regex(
            r'<div[^>]+class="js-jwloader"(?P<info>[^>]+)', webpage, 'player info')
        data_id = self._search_regex(
            r'data-id="(?P<id>\d+)"', player_info, 'video id')
        data_site = self._search_regex(
            r'data-site="(?P<data_site>\d+)"', player_info, 'data site')

        api_url = 'http://api.tegna-tv.com/video/v2/getAllVideoPathsById/%s/%s?subscription-key=%s' % (data_id, data_site, self.SUBSCRIPTION_KEY)
        video_json = self._download_json(api_url, show_id)

        video_id = str_or_none(video_json['Id'])
        title = str_or_none(video_json['Title'])
        description = str_or_none(video_json['Description'])
        thumbnail = str_or_none(video_json['Image'])

        duration = parse_duration(str_or_none(video_json['VideoLength']))
        timestamp = unified_timestamp(str_or_none(video_json['DateCreated']))

        formats = []
        for elem in video_json.get('Sources'):
            path = str_or_none(elem['Path'])
            if elem.get('Format') == 'MP4':
                formats.append(
                    {
                        'url': path,
                        'format_id': 'mp4-' + str_or_none(elem['EncodingRate']),
                        'vbr': int_or_none(elem['EncodingRate']),
                    }
                )
            elif elem.get('Format') == 'HLS':
                forms = self._extract_m3u8_formats(
                    path, video_id, ext='mp4', entry_protocol='m3u8_native')
                formats += forms
            elif elem.get('Format') == 'HDS':
                # I am not sure how to extract this format, I have tried the
                # following, but this format seems to be only mentioned
                # in the json, but not really available:
                # forms = self._extract_akamai_formats(path, video_id)
                # formats += forms
                pass

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
        }


class NineNewsIE(TegnaMediaIE):
    _VALID_URL = r'https?://(?:www\.)?9news\.com/.+/(?P<id>[0-9]+)'
    SUBSCRIPTION_KEY = 'ae1d3e46c9914e9b87757fead91d7654'

    _TEST = {
        'url': 'http://www.9news.com/news/local/father-worries-about-immigration-status/408808900',
        'md5': 'e367c89e52eed4ff3bcc696d664e4f4b',
        'info_dict': {
            'id': '2512310',
            'ext': 'mp4',
            'title': 'Father worries about immigration status',
            'description': '9NEWS @ 9. 2/15/2017',
            'thumbnail': 'http://kusa-download.edgesuite.net/video/2512310/2512310_Still.jpg',
            'duration': 96.0,
            'timestamp': 1487218434,
            'upload_date': '20170216',
        }
    }

    def _real_extract(self, url):
        return super(NineNewsIE, self)._real_extract(url)


class TwelveNewsIE(TegnaMediaIE):
    _VALID_URL = r'https?://(?:www\.)?12news\.com/.+/(?P<id>[0-9]+)'
    SUBSCRIPTION_KEY = 'd721cdf2210c493cb8a194d1e53b4ef5'

    _TEST = {
        'url': 'http://www.12news.com/news/local/valley/dps-stops-wrong-way-driver-after-several-miles/408864874',
        'info_dict': {
            'id': '2514219',
            'ext': 'mp4',
            'title': '''Megan Melanson's initial court appearance''',
            'description': 'md5:24188e754669c29700e8dd6d19e4943b',
            'timestamp': 1487360943,
            'upload_date': '20170217',
        },
        'params': {
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        return super(TwelveNewsIE, self)._real_extract(url)


class THVElevenIE(TegnaMediaIE):
    _VALID_URL = r'https?://(?:www\.)?thv11\.com/.+/(?P<id>[0-9]+)'
    SUBSCRIPTION_KEY = 'd8d2110b71e5490f8652a270ef1cc8c2'

    def _real_extract(self, url):
        return super(THVElevenIE, self)._real_extract(url)
