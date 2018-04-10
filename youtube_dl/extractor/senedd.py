# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import parse_duration
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)


class SeneddIE(InfoExtractor):
    _VALID_URL = r'http://senedd\.tv/Meeting/(?:Archive|Clip)/(?P<id>[0-9a-f\-]+)'
    # TODO: some old links which redirect: http://www.senedd.tv/cy/4251?startPos=6&amp;l=cy
    _TEST = {
        'url': 'http://senedd.tv/Meeting/Clip/f2a274d3-a15a-4dec-b92b-be233eed9601?inPoint=00:50:35&outPoint=02:39:16',
        'md5': '673307fe76d3c885bf02d8b146f10a2f',
        'info_dict': {
            'id': 'f2a274d3-a15a-4dec-b92b-be233eed9601',
            'ext': 'mp4',
            'title': 'Plenary',
            'thumbnail': r're:^http://.*\.jpg$',
            'language': 'en',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        inverted_language = self._html_search_regex(r'<a class="language-selector" data-language-code="(..)"', webpage, u'language selector')

        m3u8 = None
        language = None
        if inverted_language == 'cy':
            language = 'en'
            m3u8 = 'http://nafw-live.hls.adaptive.level3.net/c/%s/interpretation/interpretation.isml/interpretation.m3u8' % video_id
        else:
            language = 'cy'
            m3u8 = 'http://nafw-live.hls.adaptive.level3.net/c/%s/verbatim/verbatim.isml/verbatim.m3u8' % video_id

        formats = self._extract_m3u8_formats(m3u8, video_id, 'mp4', entry_protocol='m3u8_native')
        self._sort_formats(formats)

        start_time = None
        end_time = None
        parsed_url = compat_urllib_parse_urlparse(url)
        query = compat_parse_qs(parsed_url.query)
        if 'inPoint' in query:
            start_time = parse_duration(query['inPoint'][0])
        if 'outPoint' in query:
            end_time = parse_duration(query['outPoint'][0])

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'language': language,
            'thumbnail': 'http://static.content.nafw.vualto.com/meeting/%s/thumb/default.jpg' % video_id,
            'start_time': start_time,
            'end_time': end_time,
        }
