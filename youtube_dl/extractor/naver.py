# encoding: utf-8
import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    ExtractorError,
)


class NaverIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tvcast\.naver\.com/v/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://tvcast.naver.com/v/81652',
        u'file': u'81652.mp4',
        u'info_dict': {
            u'title': u'[9월 모의고사 해설강의][수학_김상희] 수학 A형 16~20번',
            u'description': u'합격불변의 법칙 메가스터디 | 메가스터디 수학 김상희 선생님이 9월 모의고사 수학A형 16번에서 20번까지 해설강의를 공개합니다.',
            u'upload_date': u'20130903',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)
        m_id = re.search(r'var rmcPlayer = new nhn.rmcnmv.RMCVideoPlayer\("(.+?)", "(.+?)"',
            webpage)
        if m_id is None:
            raise ExtractorError(u'couldn\'t extract vid and key')
        vid = m_id.group(1)
        key = m_id.group(2)
        query = compat_urllib_parse.urlencode({'vid': vid, 'inKey': key,})
        query_urls = compat_urllib_parse.urlencode({
            'masterVid': vid,
            'protocol': 'p2p',
            'inKey': key,
        })
        info = self._download_xml(
            'http://serviceapi.rmcnmv.naver.com/flash/videoInfo.nhn?' + query,
            video_id, u'Downloading video info')
        urls = self._download_xml(
            'http://serviceapi.rmcnmv.naver.com/flash/playableEncodingOption.nhn?' + query_urls,
            video_id, u'Downloading video formats info')

        formats = []
        for format_el in urls.findall('EncodingOptions/EncodingOption'):
            domain = format_el.find('Domain').text
            if domain.startswith('rtmp'):
                continue
            formats.append({
                'url': domain + format_el.find('uri').text,
                'ext': 'mp4',
                'width': int(format_el.find('width').text),
                'height': int(format_el.find('height').text),
            })

        return {
            'id': video_id,
            'title': info.find('Subject').text,
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'upload_date': info.find('WriteDate').text.replace('.', ''),
            'view_count': int(info.find('PlayCount').text),
        }
