# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    update_url_query,
)


class NaverIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tv(?:cast)?\.naver\.com/v/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://tv.naver.com/v/81652',
        'info_dict': {
            'id': '81652',
            'ext': 'mp4',
            'title': '[9월 모의고사 해설강의][수학_김상희] 수학 A형 16~20번',
            'description': '합격불변의 법칙 메가스터디 | 메가스터디 수학 김상희 선생님이 9월 모의고사 수학A형 16번에서 20번까지 해설강의를 공개합니다.',
            'upload_date': '20130903',
        },
    }, {
        'url': 'http://tv.naver.com/v/395837',
        'md5': '638ed4c12012c458fefcddfd01f173cd',
        'info_dict': {
            'id': '395837',
            'ext': 'mp4',
            'title': '9년이 지나도 아픈 기억, 전효성의 아버지',
            'description': 'md5:5bf200dcbf4b66eb1b350d1eb9c753f7',
            'upload_date': '20150519',
        },
        'skip': 'Georestricted',
    }, {
        'url': 'http://tvcast.naver.com/v/81652',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vid = self._search_regex(
            r'videoId["\']\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'video id', fatal=None, group='value')
        in_key = self._search_regex(
            r'inKey["\']\s*:\s*(["\'])(?P<value>(?:(?!\1).)+)\1', webpage,
            'key', default=None, group='value')

        if not vid or not in_key:
            error = self._html_search_regex(
                r'(?s)<div class="(?:nation_error|nation_box|error_box)">\s*(?:<!--.*?-->)?\s*<p class="[^"]+">(?P<msg>.+?)</p>\s*</div>',
                webpage, 'error', default=None)
            if error:
                raise ExtractorError(error, expected=True)
            raise ExtractorError('couldn\'t extract vid and key')
        video_data = self._download_json(
            'http://play.rmcnmv.naver.com/vod/play/v2.0/' + vid,
            video_id, query={
                'key': in_key,
            })
        meta = video_data['meta']
        title = meta['subject']
        formats = []

        def extract_formats(streams, stream_type, query={}):
            for stream in streams:
                stream_url = stream.get('source')
                if not stream_url:
                    continue
                stream_url = update_url_query(stream_url, query)
                encoding_option = stream.get('encodingOption', {})
                bitrate = stream.get('bitrate', {})
                formats.append({
                    'format_id': '%s_%s' % (stream.get('type') or stream_type, encoding_option.get('id') or encoding_option.get('name')),
                    'url': stream_url,
                    'width': int_or_none(encoding_option.get('width')),
                    'height': int_or_none(encoding_option.get('height')),
                    'vbr': int_or_none(bitrate.get('video')),
                    'abr': int_or_none(bitrate.get('audio')),
                    'filesize': int_or_none(stream.get('size')),
                    'protocol': 'm3u8_native' if stream_type == 'HLS' else None,
                })

        extract_formats(video_data.get('videos', {}).get('list', []), 'H264')
        for stream_set in video_data.get('streams', []):
            query = {}
            for param in stream_set.get('keys', []):
                query[param['name']] = param['value']
            stream_type = stream_set.get('type')
            videos = stream_set.get('videos')
            if videos:
                extract_formats(videos, stream_type, query)
            elif stream_type == 'HLS':
                stream_url = stream_set.get('source')
                if not stream_url:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    update_url_query(stream_url, query), video_id,
                    'mp4', 'm3u8_native', m3u8_id=stream_type, fatal=False))
        self._sort_formats(formats)

        subtitles = {}
        for caption in video_data.get('captions', {}).get('list', []):
            caption_url = caption.get('source')
            if not caption_url:
                continue
            subtitles.setdefault(caption.get('language') or caption.get('locale'), []).append({
                'url': caption_url,
            })

        upload_date = self._search_regex(
            r'<span[^>]+class="date".*?(\d{4}\.\d{2}\.\d{2})',
            webpage, 'upload date', fatal=False)
        if upload_date:
            upload_date = upload_date.replace('.', '')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'description': self._og_search_description(webpage),
            'thumbnail': meta.get('cover', {}).get('source') or self._og_search_thumbnail(webpage),
            'view_count': int_or_none(meta.get('count')),
            'upload_date': upload_date,
        }
