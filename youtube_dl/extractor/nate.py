# coding: utf-8
from __future__ import unicode_literals

import itertools

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    int_or_none,
    merge_dicts,
    T,
    traverse_obj,
    txt_or_none,
    unified_strdate,
    url_or_none,
)


class NateBaseIE(InfoExtractor):
    _API_BASE = 'https://tv.nate.com/api/v1/'

    def _download_webpage_handle(self, url_or_request, video_id, *args, **kwargs):
        fatal = kwargs.get('fatal', True)
        kwargs['fatal'] = False
        res = super(NateBaseIE, self)._download_webpage_handle(
            url_or_request, video_id, *args, **kwargs)
        if not res:
            if fatal:
                raise ExtractorError('Failed to download webpage')
            return res
        status = res[1].getcode()
        if 200 <= status < 400:
            new_url = res[1].geturl()
            if url_or_request != new_url and '/Error.html' in new_url:
                raise ExtractorError(
                    'Download redirected to Error.html: expired?',
                    expected=True)
        else:
            msg = 'Failed to download webpage: HTTP code %d' % status
            if fatal:
                raise ExtractorError(msg)
            else:
                self.report_warning(msg)
        return res


class NateIE(NateBaseIE):
    _VALID_URL = r'https?://(?:m\.)?tv\.nate\.com/clip/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://tv.nate.com/clip/1848976',
        'info_dict': {
            'id': '1848976',
            'ext': 'mp4',
            'title': '[결승 오프닝 타이틀] 2018 LCK 서머 스플릿 결승전 kt Rolster VS Griffin',
            'description': 'md5:e1b79a7dcf0d8d586443f11366f50e6f',
            'thumbnail': r're:^http?://.*\.jpg$',
            'upload_date': '20180908',
            'age_limit': 15,
            'duration': 73,
            'uploader': '2018 LCK 서머 스플릿(롤챔스)',
            'channel': '2018 LCK 서머 스플릿(롤챔스)',
            'channel_id': '3606',
            'uploader_id': '3606',
            'tags': 'count:59',
        },
        'skip': 'Redirect to Error.html',
    }, {
        'url': 'https://tv.nate.com/clip/4300566',
        # 'md5': '02D3CAB3907B60C58043761F8B5BF2B3',
        'info_dict': {
            'id': '4300566',
            'ext': 'mp4',
            'title': '[심쿵엔딩] 이준호x이세영, 서로를 기억하며 끌어안는 두 사람!💕, MBC 211204 방송',
            'description': 'md5:edf489c54ea2682c7973154b2089aa0e',
            'thumbnail': r're:^http?://.*\.jpg$',
            'upload_date': '20211204',
            'age_limit': 15,
            'duration': 201,
            'uploader': '옷소매 붉은 끝동',
            'channel': '옷소매 붉은 끝동',
            'channel_id': '27987',
            'uploader_id': '27987',
            'tags': 'count:20',
        },
        'params': {'skip_download': True},
    }, {
        'url': 'https://tv.nate.com/clip/4764792',
        'info_dict': {
            'id': '4764792',
            'ext': 'mp4',
            'title': '흥을 돋우는 가야금 연주와 트롯의 만남⬈ ‘열두줄’♪ TV CHOSUN 230625 방송',
            'description': 'md5:85734d3f9daebe4aa4f20cc73bdcc90c',
            'upload_date': '20230625',
            'uploader_id': '29116',
            'uploader': '쇼퀸',
            'age_limit': 15,
            'thumbnail': r're:^http?://.*\.jpg$',
            'duration': 182,
            'channel': '쇼퀸',
            'channel_id': '29116',
            'tags': 'count:25',
        },
        'params': {'skip_download': True},
    }]

    _QUALITY = {
        '36': 2160,
        '35': 1080,
        '34': 720,
        '33': 480,
        '32': 360,
        '31': 270,
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_data, urlh = self._download_json_handle(
            '{0}clip/{1}'.format(self._API_BASE, video_id), video_id,
            fatal=False)
        if not video_data:
            raise ExtractorError('Empty programme JSON')

        title = video_data['clipTitle']
        formats = []
        for f_url in traverse_obj(video_data, ('smcUriList', Ellipsis, T(url_or_none))):
            fmt_id = f_url[-2:]
            formats.append({
                'format_id': fmt_id,
                'url': f_url,
                'height': self._QUALITY.get(fmt_id),
                'quality': int_or_none(fmt_id),
            })
        self._sort_formats(formats)

        info = traverse_obj(video_data, {
            'uploader': ('programTitle', T(txt_or_none)),
            'uploader_id': ('programSeq', T(txt_or_none)),
        })
        for up, ch in (('uploader', 'channel'), ('uploader_id', 'channel_id')):
            info[ch] = info.get(up)

        return merge_dicts({
            'id': video_id,
            'title': title,
            'formats': formats,
        }, info, traverse_obj(video_data, {
            'description': ('synopsis', T(txt_or_none)),
            'thumbnail': ('contentImg', T(url_or_none)),
            'upload_date': (('broadDate', 'regDate'), T(unified_strdate)),
            'age_limit': ('targetAge', T(int_or_none)),
            'duration': ('playTime', T(int_or_none)),
            'tags': ('hashTag', T(lambda s: s.split(',') or None)),
        }, get_all=False))


class NateProgramIE(NateBaseIE):
    _VALID_URL = r'https?://tv\.nate\.com/program/clips/(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'https://tv.nate.com/program/clips/27987',
        'playlist_mincount': 191,
        'info_dict': {
            'id': '27987',
        },
    }, {
        'url': 'https://tv.nate.com/program/clips/3606',
        'playlist_mincount': 15,
        'info_dict': {
            'id': '3606',
        },
        'skip': 'Redirect to Error.html',
    }]

    def _entries(self, pl_id):
        for page_num in itertools.count(1):
            program_data, urlh = self._download_json_handle(
                '{0}program/{1}/clip/ranking'.format(self._API_BASE, pl_id),
                pl_id, query={'size': 20, 'page': page_num},
                note='Downloading page {0}'.format(page_num), fatal=False)

            empty = True
            for clip_id in traverse_obj(program_data, ('content', Ellipsis, 'clipSeq', T(txt_or_none))):
                yield self.url_result(
                    'https://tv.nate.com/clip/%s' % clip_id,
                    ie=NateIE.ie_key(), video_id=clip_id)
                empty = False
            if traverse_obj(program_data, 'last') or (program_data and empty):
                break

    def _real_extract(self, url):
        pl_id = self._match_id(url)
        return self.playlist_result(self._entries(pl_id), playlist_id=pl_id)
