# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    orderedSet,
    url_or_none,
    determine_ext,
    try_get,
    compat_str
)


class MarkizaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?videoarchiv\.markiza\.sk/(?:video/(?:[^/]+/)*|embed/)\S+/(?P<id>\d+)(?:[_/-]|$)'

    _TESTS = [{
        'url': 'http://videoarchiv.markiza.sk/video/oteckovia/\
            84723_oteckovia-109',
        'md5': 'ada4e9fad038abeed971843aa028c7b0',
        'info_dict': {
            'id': '139078',
            'ext': 'mp4',
            'title': 'Oteckovia 109',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2760,
        },
    }, {
        'url': 'https://videoarchiv.markiza.sk/video/laska-na-prenajom/epizoda/58779-seria-1-epizoda-14',
        'info_dict': {
            'id': '85430',
            'title': 'Televízne noviny',
        },
        'playlist_count': 23,
    }, {
        'url': 'https://videoarchiv.markiza.sk/video/oteckovia/84723',
        'only_matching': True,
    }, {
        'url': 'https://videoarchiv.markiza.sk/video/84723',
        'only_matching': True,
    }, {
        'url': 'https://videoarchiv.markiza.sk/video/filmy/85190_kamenak',
        'only_matching': True,
    }, {
        'url': 'https://videoarchiv.markiza.sk/video/reflex/zo-zakulisia/84651_pribeh-alzbetky',
        'only_matching': True,
    }, {
        'url': 'https://videoarchiv.markiza.sk/embed/85295',
        'only_matching': True,
    }]

    def _real_extract(self, url):

        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        embed = self._search_regex(
            r'<iframe src="(https:\/\/media.*?)" style="',
            webpage, 'embed', fatal=False)

        webpage = self._download_webpage(embed, video_id)
        data = self._search_regex(
            r'processAdTagModifier\s*\(\s*(\{.*)\)\s*,\s*\{\s*"video"\s*:',
            webpage, 'embed', default='')
        data2 = self._search_regex(
            r'processAdTagModifier\s*\(\s*\{.*\)\s*,\s*(\{\s*"video"\s*:.*)\s*\);',
            webpage, 'embed', default='')
        data = re.sub('\\\\/', '/', data)
        data2 = re.sub('\\\\/', '/', data2)
        info = self._parse_json(data, video_id)
        info2 = self._parse_json(data2, video_id)

        formats = []
        for format_id, format_list in (
                try_get(info, lambda x: x['tracks'], dict) or {}).items():
            for format_dict in format_list:
                if not isinstance(format_dict, dict):
                    continue
                format_url = try_get(
                    format_dict, lambda x: url_or_none(x['src']))
                if not format_url:
                    continue
                format_type = format_dict.get('type')
                ext = determine_ext(format_url)
                if (format_type == 'application/x-mpegURL'
                        or format_id == 'HLS' or ext == 'm3u8'):
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls',
                        fatal=False))
                elif (format_type == 'application/dash+xml'
                      or format_id == 'DASH' or ext == 'mpd'):
                    formats.extend(self._extract_mpd_formats(
                        format_url, video_id, mpd_id='dash', fatal=False))
                else:
                    formats.append({
                        'url': format_url,
                    })
        # thumbnail = info.get('plugins').get('thumbnails').get('url')
        thumbnail = try_get(
                info, lambda x: x['plugins']['thumbnails']['url'], compat_str)
        thumbnail = re.sub('$Num$', '001', thumbnail)
        duration = info.get('duration')
        # title2 = info2.get('video').get('title')
        # title = info2.get('video').get('custom').get('show_title')
        title2 = try_get(info2, lambda x: x['video']['title'], compat_str)
        title = try_get(
            info2, lambda x: x['video']['custom']['show_title'], compat_str)
        title = ' - '.join(x for x in (title, title2, ) if x)
        # if not title:
        #     continue

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats
        }


class MarkizaPageIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:(?:[^/]+\.)?markiza|tvnoviny)\.sk/(?:[^/]+/)*(?P<id>\d+)_'
    _TESTS = [{
        'url': 'https://www.markiza.sk/soubiz/zahranicny/1923705_oteckovia-maju-svoj-den-ti-slavni-nie-su-o-nic-menej-rozkosni',
        'md5': 'ada4e9fad038abeed971843aa028c7b0',
        'info_dict': {
            'id': '139355',
            'ext': 'mp4',
            'title': 'Oteckovia 110',
            'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2604,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://dajto.markiza.sk/filmy-a-serialy/1774695_frajeri-vo-vegas',
        'only_matching': True,
    }, {
        'url': 'https://superstar.markiza.sk/aktualne/1923870_to-je-ale-telo-spevacka-ukazala-sexy-postavicku-v-bikinach',
        'only_matching': True,
    }, {
        'url': 'https://hybsa.markiza.sk/aktualne/1923790_uzasna-atmosfera-na-hybsa-v-poprade-superstaristi-si-prve-koncerty-pred-davom-ludi-poriadne-uzili',
        'only_matching': True,
    }, {
        'url': 'https://doma.markiza.sk/filmy/1885250_moja-vysnivana-svadba',
        'only_matching': True,
    }, {
        'url': 'https://www.tvnoviny.sk/domace/1923887_po-smrti-manzela-ju-cakalo-poriadne-prekvapenie',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return (
            False if MarkizaIE.suitable(url)
            else super(MarkizaPageIE, cls).suitable(url)
        )

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(
            # Downloading for some hosts (e.g. dajto, doma) fails with 500
            # although everything seems to be OK, so considering 500
            # status code to be expected.
            url, playlist_id, expected_status=500)

        entries = [
            self.url_result(
                'http://videoarchiv.markiza.sk/video/%s' % video_id)
            for video_id in orderedSet(re.findall(
                r'(?:initPlayer_|data-entity=["\']|id=["\']player_)(\d+)',
                webpage))]

        return self.playlist_result(entries, playlist_id)
