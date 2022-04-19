# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
)
from ..utils import (
    clean_html,
    extract_attributes,
    get_elements_by_class,
    parse_duration,
    ExtractorError,
    str_to_int,
    strip_or_none,
    unified_strdate,
)


class Porn91IE(InfoExtractor):
    IE_NAME = '91porn'
    _VALID_URL = r'(?:https?://)(?:www\.|)91porn\.com/.+?\?viewkey=(?P<id>[\w\d]+)'

    _TEST = {
        'url': 'http://91porn.com/view_video.php?viewkey=7e42283b4f5ab36da134',
        'md5': 'd869db281402e0ef4ddef3c38b866f86',
        'info_dict': {
            'id': '7e42283b4f5ab36da134',
            'title': '18岁大一漂亮学妹，水嫩性感，再爽一次！',
            'ext': 'mp4',
            'duration': 431,
            'age_limit': 18,
            'upload_date': '20150520',
            'uploader': '千岁九王爷',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # set language for page to be extracted
        self._set_cookie('91porn.com', 'language', 'cn_CN')

        webpage = self._download_webpage(
            'http://91porn.com/view_video.php?viewkey=%s' % video_id, video_id)

        if '作为游客，你每天只可观看10个视频' in webpage:
            raise ExtractorError('91 Porn says: Daily limit 10 videos exceeded', expected=True)

        title = self._html_search_regex(
            r'(?s)<title\b[^>]*>\s*(.+?)\s*(?:Chinese\s+homemade\s+video\s*)?</title', webpage, 'title')

        video_link_url = self._search_regex(
            r'''document\s*\.\s*write\s*\(\s*strencode2\s*\((?P<q>"|')(?P<enc_str>[%\da-fA-F]+)(?P=q)\s*\)''',
            webpage, 'video link', group='enc_str')
        video_link_url = compat_urllib_parse_unquote(video_link_url)

        info_dict = self._parse_html5_media_entries(url, '<video>%s</video>' % (video_link_url, ), video_id)[0]

        # extract various fields in <tag class=info>Name: value</tag>
        FIELD_MAP = {
            # cn_CN name: (yt-dl key, value parser, en name)
            '时长': ('duration', parse_duration, 'Runtime', ),
            '查看': ('view_count', str_to_int, 'Views', ),
            '留言': ('comment_count', str_to_int, 'Comments', ),
            '收藏': ('like_count', str_to_int, 'Favorites', ),
            '添加时间': ('upload_date', unified_strdate, 'Added', ),
            # same as title for en, not description for cn_CN
            '__ignore__': ('description', strip_or_none, 'Description', ),
            '作者': ('uploader', strip_or_none, 'From', ),
        }
        # yt-dl's original implementation of get_elements_by_class() uses regex
        # yt-dlp uses an actual HTML parser, and can be confused by bad HTML fragments
        for elt in get_elements_by_class(
                'info',
                # concatenate <span>s ...
                re.sub(r'(?i)</span>\s*<span\b[^>]*?>', '',
                       # ... and strip out possibly unbalanced <font> for yt-dlp
                       re.sub(r'(?i)(?:<font\b[^>]*?>|</font\s*>)', '', webpage))) or []:
            elt = re.split(r':\s*', clean_html(elt), 1)
            if len(elt) != 2 or elt[1] == '':
                continue
            parm = FIELD_MAP.get(elt[0].strip())
            if parm and elt[1] is not None:
                info_dict[parm[0]] = parm[1](elt[1]) if parm[1] else elt[1]

        thumbnail = extract_attributes(
            self._search_regex(
                r'''(<video\b[^>]*\bid\s*=\s*(?P<q>"|')player_one(?P=q)[^>]*>)''',
                webpage, 'poster', default='')).get('poster')

        info_dict.update({
            'id': video_id,
            'title': title,
            'age_limit': self._rta_search(webpage),
            'thumbnail': thumbnail,
        })

        return info_dict
