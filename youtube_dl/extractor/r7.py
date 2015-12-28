# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    unescapeHTML,
    int_or_none,
)


class R7IE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
                        (?:
                            (?:[a-zA-Z]+)\.r7\.com(?:/[^/]+)+/idmedia/|
                            noticias\.r7\.com(?:/[^/]+)+/[^/]+-|
                            player\.r7\.com/video/i/
                        )
                        (?P<id>[\da-f]{24})
                        '''
    _TESTS = [{
        'url': 'http://videos.r7.com/policiais-humilham-suspeito-a-beira-da-morte-morre-com-dignidade-/idmedia/54e7050b0cf2ff57e0279389.html',
        'md5': '403c4e393617e8e8ddc748978ee8efde',
        'info_dict': {
            'id': '54e7050b0cf2ff57e0279389',
            'ext': 'mp4',
            'title': 'Policiais humilham suspeito à beira da morte: "Morre com dignidade"',
            'thumbnail': 're:^https?://.*\.jpg$',
            'duration': 98,
            'like_count': int,
            'view_count': int,
        },
    }, {
        'url': 'http://esportes.r7.com/videos/cigano-manda-recado-aos-fas/idmedia/4e176727b51a048ee6646a1b.html',
        'only_matching': True,
    }, {
        'url': 'http://noticias.r7.com/record-news/video/representante-do-instituto-sou-da-paz-fala-sobre-fim-do-estatuto-do-desarmamento-5480fc580cf2285b117f438d/',
        'only_matching': True,
    }, {
        'url': 'http://player.r7.com/video/i/54e7050b0cf2ff57e0279389?play=true&video=http://vsh.r7.com/54e7050b0cf2ff57e0279389/ER7_RE_BG_MORTE_JOVENS_570kbps_2015-02-2009f17818-cc82-4c8f-86dc-89a66934e633-ATOS_copy.mp4&linkCallback=http://videos.r7.com/policiais-humilham-suspeito-a-beira-da-morte-morre-com-dignidade-/idmedia/54e7050b0cf2ff57e0279389.html&thumbnail=http://vtb.r7.com/ER7_RE_BG_MORTE_JOVENS_570kbps_2015-02-2009f17818-cc82-4c8f-86dc-89a66934e633-thumb.jpg&idCategory=192&share=true&layout=full&full=true',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://player.r7.com/video/i/%s' % video_id, video_id)

        item = self._parse_json(js_to_json(self._search_regex(
            r'(?s)var\s+item\s*=\s*({.+?});', webpage, 'player')), video_id)

        title = unescapeHTML(item['title'])
        thumbnail = item.get('init', {}).get('thumbUri')
        duration = None

        statistics = item.get('statistics', {})
        like_count = int_or_none(statistics.get('likes'))
        view_count = int_or_none(statistics.get('views'))

        formats = []
        for format_key, format_dict in item['playlist'][0].items():
            src = format_dict.get('src')
            if not src:
                continue
            format_id = format_dict.get('format') or format_key
            if duration is None:
                duration = format_dict.get('duration')
            if '.f4m' in src:
                formats.extend(self._extract_f4m_formats(src, video_id, preference=-1))
            elif src.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(src, video_id, 'mp4', preference=-2))
            else:
                formats.append({
                    'url': src,
                    'format_id': format_id,
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'like_count': like_count,
            'view_count': view_count,
            'formats': formats,
        }
