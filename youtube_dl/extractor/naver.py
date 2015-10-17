# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    determine_ext,
    unescapeHTML,
)


class NaverIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?(?:tvcast\.naver\.com/v/|news\.naver\.com/main/read\.nhn?.*aid=|sports\.news\.naver.com/(?:videoCenter|sports)/(?:index|video)\.nhn?.*id=|movie\.naver.com/movie/bi/mi/mediaView\.nhn?.*mid=|music\.naver\.com/artist/videoPlayer\.nhn?.*videoId=)(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://tvcast.naver.com/v/81652',
        'md5': '0fe25e226a0ec388cd75679981bd2a1a',
        'info_dict': {
            'id': '4B40C2B7F4BC7C7BBA5237C5E3CED1ADEAF5',
            'ext': 'mp4',
            'title': '[9월 모의고사 해설강의][수학_김상희] 수학 A형 16~20번',
            'uploader_id': 'megastudy',
            'uploader': '합격불변의 법칙 메가스터디',
        },
    }, {
        'url': 'http://tvcast.naver.com/v/395837',
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
        'url': 'http://news.naver.com/main/read.nhn?mode=LSD&mid=tvh&oid=056&aid=0010235712&sid1=293',
        'md5': 'ea02b7943173553618f49de08d6bd36e',
        'info_dict': {
            'id': '3C026B64F022C136ED9057AA820458275CD7',
            'ext': 'mp4',
            'title': '한미 정상 “북핵 문제 최우선”…공동성명 첫 채택',
            'uploader_id': 'muploader_o',
            'uploader': '',
        },
    }, {
        'url': 'http://sports.news.naver.com/videoCenter/index.nhn?uCategory=esports&category=lol&id=158508',
        'md5': '436254dbbb7dde42053c731039f6f14d',
        'info_dict': {
            'id': '3CD20A3B7B15044056189B09557FB349DE0B',
            'ext': 'mp4',
            'title': '\'전승 가도\' 절대강자 Faker의 인터뷰',
            'uploader_id': 'muploader_n',
            'uploader': '',
        },
    }, {
        'url': 'http://movie.naver.com/movie/bi/mi/mediaView.nhn?code=115622&mid=27362',
        'md5': 'ad9623ff5a23d6e9c0c7f451b063912f',
        'info_dict': {
            'id': '1132280440B9037B8E48DB0F569208440008',
            'ext': 'mp4',
            'title': '<인사이드 아웃> 메인 예고편',
            'uploader_id': 'navermovie',
            'uploader': '네이버 영화',
        },
    }, {
        'url': 'http://music.naver.com/artist/videoPlayer.nhn?videoId=99476',
        'md5': '4378409358f457bdce12e90f40ba33e2',
        'info_dict': {
            'id': 'E2651FBE1723D209C17AB611C296C57EA0A1',
            'ext': 'mp4',
            'title': '디아크 인사말',
            'uploader_id': 'muploader_c',
            'uploader': '',
        },
    }]

    def _extract_video_formats(self, formats_list):
        formats = []
        for format_el in formats_list:
            url = format_el.get('source')
            if url:
                encoding_option = format_el.get('encodingOption')
                bitrate = format_el.get('bitrate')
                formats.append({
                    'format_id': encoding_option.get('id') or encoding_option.get('name'),
                    'url': format_el['source'],
                    'width': int_or_none(encoding_option.get('width')),
                    'height': int_or_none(encoding_option.get('height')),
                    'vbr': float_or_none(bitrate.get('video')),
                    'abr': float_or_none(bitrate.get('audio')),
                    'filesize': int_or_none(format_el.get('size')),
                    'vcodec': format_el.get('type'),
                    'ext': determine_ext(url, 'mp4'),
                })
        if formats:
            self._sort_formats(formats)
        return formats

    def _extract_video_info(self, vid, key):
        play_data = self._download_json(
            'http://global.apis.naver.com/linetv/rmcnmv/vod_play_videoInfo.json?' + compat_urllib_parse.urlencode({'videoId': vid, 'key': key}),
            vid, 'Downloading video info')
        meta = play_data.get('meta')
        user = meta.get('user')

        thumbnails = []
        for thumbnail in play_data['thumbnails']['list']:
            thumbnails.append({'url': thumbnail['source']})

        formats = self._extract_video_formats(play_data['videos']['list'])
        if not formats:
            video_info = self._download_json(
                'http://serviceapi.rmcnmv.naver.com/mobile/getVideoInfo.nhn?' + compat_urllib_parse.urlencode({'videoId': vid, 'inKey': key, 'protocol': 'http'}),
                vid, 'Downloading video info')
            formats = self._extract_video_formats(video_info['videos']['list'])

        return {
            'id': vid,
            'title': meta['subject'],
            'formats': formats,
            'thumbnail': meta.get('cover', {}).get('source'),
            'thumbnails': thumbnails,
            'view_count': int_or_none(meta.get('count')),
            'uploader_id': user.get('id'),
            'uploader': user.get('name'),
        }

    def _extract_id_and_key(self, webpage):
        m_id = re.search(r'(?s)new\s+nhn.rmcnmv.RMCVideoPlayer\(\s*["\']([^"\']+)["\']\s*,\s*(?:{[^}]*?value[^:]*?:\s*?)?["\']([^"\']+)["\']', webpage)
        if not m_id:
            m_id = re.search(r'(?s)_sVid\s*=\s*["\']([^"\']+)["\'];\s*var\s+_sInkey\s*=\s*["\']([^"\']+)["\'];', webpage)
        return m_id

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        m_id = self._extract_id_and_key(webpage)
        if not m_id:
            iframe_urls = re.findall(r'<(?:iframe|IFRAME)[^>]+src="((?:/main/readVod|/movie/bi/mi/videoPlayer|http://serviceapi\.rmcnmv\.naver\.com/flash/outKeyPlayer)\.nhn[^"]+)"', webpage)
            if iframe_urls:
                entries = []
                for iframe_url in iframe_urls:
                    iframe_url = unescapeHTML(iframe_url)
                    if iframe_url.startswith('/'):
                        iframe_url = compat_urlparse.urljoin(url, iframe_url)
                    request = compat_urllib_request.Request(iframe_url, headers={'Referer': url})
                    iframe_webpage = self._download_webpage(request, video_id, 'Downloading iframe webpage')
                    m_id = self._extract_id_and_key(iframe_webpage)
                    if m_id:
                        vid, key = m_id.groups()
                        entries.append(self._extract_video_info(vid, key))
                return entries[0] if len(entries) == 1 else self.playlist_result(entries)
            else:
                error = self._html_search_regex(
                    r'(?s)<div class="(?:nation_error|nation_box|error_box)">\s*(?:<!--.*?-->)?\s*<p class="[^"]+">(?P<msg>.+?)</p>\s*</div>',
                    webpage, 'error', default=None)
                if error:
                    raise ExtractorError(error, expected=True)
                raise ExtractorError('couldn\'t extract vid and key')
        vid, key = m_id.groups()
        return self._extract_video_info(vid, key)
