# coding: utf-8
from __future__ import unicode_literals

import codecs
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_duration,
)


class CDAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www\.)?cda\.pl/video|ebd\.cda\.pl/[0-9]+x[0-9]+)/(?P<id>[0-9a-z]+)'
    _BASE_URL = 'http://www.cda.pl/'
    _TESTS = [{
        'url': 'http://www.cda.pl/video/5749950c',
        'md5': '6f844bf51b15f31fae165365707ae970',
        'info_dict': {
            'id': '5749950c',
            'ext': 'mp4',
            'height': 720,
            'title': 'Oto dlaczego przed zakrętem należy zwolnić.',
            'description': 'md5:269ccd135d550da90d1662651fcb9772',
            'thumbnail': r're:^https?://.*\.jpg$',
            'average_rating': float,
            'duration': 39
        }
    }, {
        'url': 'http://www.cda.pl/video/57413289',
        'md5': 'a88828770a8310fc00be6c95faf7f4d5',
        'info_dict': {
            'id': '57413289',
            'ext': 'mp4',
            'title': 'Lądowanie na lotnisku na Maderze',
            'description': 'md5:60d76b71186dcce4e0ba6d4bbdb13e1a',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'crash404',
            'view_count': int,
            'average_rating': float,
            'duration': 137
        }
    }, {
        'url': 'http://ebd.cda.pl/0x0/5749950c',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self._set_cookie('cda.pl', 'cda.player', 'html5')
        webpage = self._download_webpage(
            self._BASE_URL + '/video/' + video_id, video_id)

        if 'Ten film jest dostępny dla użytkowników premium' in webpage:
            raise ExtractorError('This video is only available for premium users.', expected=True)

        formats = []

        uploader = self._search_regex(r'''(?x)
            <(span|meta)[^>]+itemprop=(["\'])author\2[^>]*>
            (?:<\1[^>]*>[^<]*</\1>|(?!</\1>)(?:.|\n))*?
            <(span|meta)[^>]+itemprop=(["\'])name\4[^>]*>(?P<uploader>[^<]+)</\3>
        ''', webpage, 'uploader', default=None, group='uploader')
        view_count = self._search_regex(
            r'Odsłony:(?:\s|&nbsp;)*([0-9]+)', webpage,
            'view_count', default=None)
        average_rating = self._search_regex(
            r'<(?:span|meta)[^>]+itemprop=(["\'])ratingValue\1[^>]*>(?P<rating_value>[0-9.]+)',
            webpage, 'rating', fatal=False, group='rating_value')

        info_dict = {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'uploader': uploader,
            'view_count': int_or_none(view_count),
            'average_rating': float_or_none(average_rating),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'duration': None,
        }

        def extract_format(page, version):
            json_str = self._search_regex(
                r'player_data=(\\?["\'])(?P<player_data>.+?)\1', page,
                '%s player_json' % version, fatal=False, group='player_data')
            if not json_str:
                return
            player_data = self._parse_json(
                json_str, '%s player_data' % version, fatal=False)
            if not player_data:
                return
            video = player_data.get('video')
            if not video or 'file' not in video:
                self.report_warning('Unable to extract %s version information' % version)
                return
            if video['file'].startswith('uggc'):
                video['file'] = codecs.decode(video['file'], 'rot_13')
                if video['file'].endswith('adc.mp4'):
                    video['file'] = video['file'].replace('adc.mp4', '.mp4')
            f = {
                'url': video['file'],
            }
            m = re.search(
                r'<a[^>]+data-quality="(?P<format_id>[^"]+)"[^>]+href="[^"]+"[^>]+class="[^"]*quality-btn-active[^"]*">(?P<height>[0-9]+)p',
                page)
            if m:
                f.update({
                    'format_id': m.group('format_id'),
                    'height': int(m.group('height')),
                })
            info_dict['formats'].append(f)
            if not info_dict['duration']:
                info_dict['duration'] = parse_duration(video.get('duration'))

        extract_format(webpage, 'default')

        for href, resolution in re.findall(
                r'<a[^>]+data-quality="[^"]+"[^>]+href="([^"]+)"[^>]+class="quality-btn"[^>]*>([0-9]+p)',
                webpage):
            webpage = self._download_webpage(
                self._BASE_URL + href, video_id,
                'Downloading %s version information' % resolution, fatal=False)
            if not webpage:
                # Manually report warning because empty page is returned when
                # invalid version is requested.
                self.report_warning('Unable to download %s version information' % resolution)
                continue
            extract_format(webpage, resolution)

        self._sort_formats(formats)

        return info_dict
