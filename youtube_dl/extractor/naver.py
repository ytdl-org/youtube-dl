# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    ExtractorError,
    clean_html,
)


class NaverIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tvcast\.naver\.com/v/(?P<id>\d+)'

    _TEST = {
        'url': 'http://tvcast.naver.com/v/81652',
        'info_dict': {
            'id': '81652',
            'ext': 'mp4',
            'title': '[9월 모의고사 해설강의][수학_김상희] 수학 A형 16~20번',
            'description': '합격불변의 법칙 메가스터디 | 메가스터디 수학 김상희 선생님이 9월 모의고사 수학A형 16번에서 20번까지 해설강의를 공개합니다.',
            'upload_date': '20130903',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        m_id = re.search(r'var rmcPlayer = new nhn.rmcnmv.RMCVideoPlayer\("(.+?)", "(.+?)"',
                         webpage)
        if m_id is None:
            m_error = re.search(
                r'(?s)<div class="nation_error">\s*(?:<!--.*?-->)?\s*<p class="[^"]+">(?P<msg>.+?)</p>\s*</div>',
                webpage)
            if m_error:
                raise ExtractorError(clean_html(m_error.group('msg')), expected=True)
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
            f = {
                'url': domain + format_el.find('uri').text,
                'ext': 'mp4',
                'width': int(format_el.find('width').text),
                'height': int(format_el.find('height').text),
            }
            if domain.startswith('rtmp'):
                f.update({
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
