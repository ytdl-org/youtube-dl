# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
)


class NaverIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tvcast\.naver\.com/v/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://tvcast.naver.com/v/81652',
        'info_dict': {
            'id': '81652',
            'ext': 'mp4',
            'title': '[9월 모의고사 해설강의][수학_김상희] 수학 A형 16~20번',
            'description': '합격불변의 법칙 메가스터디 | 메가스터디 수학 김상희 선생님이 9월 모의고사 수학A형 16번에서 20번까지 해설강의를 공개합니다.',
            'upload_date': '20130903',
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
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        m_id = re.search(r'var rmcPlayer = new nhn.rmcnmv.RMCVideoPlayer\("(.+?)", "(.+?)"',
                         webpage)
        if m_id is None:
            error = self._html_search_regex(
                r'(?s)<div class="(?:nation_error|nation_box|error_box)">\s*(?:<!--.*?-->)?\s*<p class="[^"]+">(?P<msg>.+?)</p>\s*</div>',
                webpage, 'error', default=None)
            if error:
                raise ExtractorError(error, expected=True)
            raise ExtractorError('couldn\'t extract vid and key')
        vid = m_id.group(1)
        key = m_id.group(2)
        query = compat_urllib_parse.urlencode({'vid': vid, 'inKey': key, })
        query_urls = compat_urllib_parse.urlencode({
            'masterVid': vid,
            'protocol': 'p2p',
            'inKey': key,
        })
        info = self._download_xml(
            'http://serviceapi.rmcnmv.naver.com/flash/videoInfo.nhn?' + query,
            video_id, 'Downloading video info')
        urls = self._download_xml(
            'http://serviceapi.rmcnmv.naver.com/flash/playableEncodingOption.nhn?' + query_urls,
            video_id, 'Downloading video formats info')

        formats = []
        for format_el in urls.findall('EncodingOptions/EncodingOption'):
            domain = format_el.find('Domain').text
            uri = format_el.find('uri').text
            f = {
                'url': compat_urlparse.urljoin(domain, uri),
                'ext': 'mp4',
                'width': int(format_el.find('width').text),
                'height': int(format_el.find('height').text),
            }
            if domain.startswith('rtmp'):
                # urlparse does not support custom schemes
                # https://bugs.python.org/issue18828
                f.update({
                    'url': domain + uri,
                    'ext': 'flv',
                    'rtmp_protocol': '1',  # rtmpt
                })
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info.find('Subject').text,
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': info.find('WriteDate').text.replace('.', ''),
            'view_count': int(info.find('PlayCount').text),
        }
