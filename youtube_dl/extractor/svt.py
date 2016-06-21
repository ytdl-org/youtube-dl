# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    dict_get,
)


class SVTBaseIE(InfoExtractor):
    def _extract_video(self, info, video_id):
        video_info = self._get_video_info(info)

        formats = []
        for vr in video_info['videoReferences']:
            player_type = vr.get('playerType')
            vurl = vr['url']
            ext = determine_ext(vurl)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    vurl, video_id,
                    ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id=player_type, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    vurl + '?hdcore=3.3.0', video_id,
                    f4m_id=player_type, fatal=False))
            elif ext == 'mpd':
                if player_type == 'dashhbbtv':
                    formats.extend(self._extract_mpd_formats(
                        vurl, video_id, mpd_id=player_type, fatal=False))
            else:
                formats.append({
                    'format_id': player_type,
                    'url': vurl,
                })
        self._sort_formats(formats)

        subtitles = {}
        subtitle_references = dict_get(video_info, ('subtitles', 'subtitleReferences'))
        if isinstance(subtitle_references, list):
            for sr in subtitle_references:
                subtitle_url = sr.get('url')
                subtitle_lang = sr.get('language', 'sv')
                if subtitle_url:
                    if determine_ext(subtitle_url) == 'm3u8':
                        # TODO(yan12125): handle WebVTT in m3u8 manifests
                        continue

                    subtitles.setdefault(subtitle_lang, []).append({'url': subtitle_url})

        duration = video_info.get('materialLength')
        age_limit = 18 if video_info.get('inappropriateForChildren') else 0

        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
            'duration': duration,
            'age_limit': age_limit,
        }


class SVTIE(SVTBaseIE):
    _VALID_URL = r'https?://(?:www\.)?svt\.se/wd\?(?:.*?&)?widgetId=(?P<widget_id>\d+)&.*?\barticleId=(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.svt.se/wd?widgetId=23991&sectionId=541&articleId=2900353&type=embed&contextSectionId=123&autostart=false',
        'md5': '33e9a5d8f646523ce0868ecfb0eed77d',
        'info_dict': {
            'id': '2900353',
            'ext': 'mp4',
            'title': 'Stjärnorna skojar till det - under SVT-intervjun',
            'duration': 27,
            'age_limit': 0,
        },
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'(?:<iframe src|href)="(?P<url>%s[^"]*)"' % SVTIE._VALID_URL, webpage)
        if mobj:
            return mobj.group('url')

    def _get_video_info(self, info):
        return info['video']

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        widget_id = mobj.group('widget_id')
        article_id = mobj.group('id')

        info = self._download_json(
            'http://www.svt.se/wd?widgetId=%s&articleId=%s&format=json&type=embed&output=json' % (widget_id, article_id),
            article_id)

        info_dict = self._extract_video(info, article_id)
        info_dict['title'] = info['context']['title']
        return info_dict


class SVTPlayIE(SVTBaseIE):
    IE_DESC = 'SVT Play and Öppet arkiv'
    _VALID_URL = r'https?://(?:www\.)?(?:svtplay|oppetarkiv)\.se/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.svtplay.se/video/5996901/flygplan-till-haile-selassie/flygplan-till-haile-selassie-2',
        'md5': '2b6704fe4a28801e1a098bbf3c5ac611',
        'info_dict': {
            'id': '5996901',
            'ext': 'mp4',
            'title': 'Flygplan till Haile Selassie',
            'duration': 3527,
            'thumbnail': 're:^https?://.*[\.-]jpg$',
            'age_limit': 0,
            'subtitles': {
                'sv': [{
                    'ext': 'wsrt',
                }]
            },
        },
    }

    def _get_video_info(self, info):
        return info['context']['dispatcher']['stores']['VideoTitlePageStore']['data']['video']

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(self._search_regex(
            r'root\["__svtplay"\]\s*=\s*([^;]+);', webpage, 'embedded data'), video_id)

        thumbnail = self._og_search_thumbnail(webpage)

        info_dict = self._extract_video(data, video_id)
        info_dict.update({
            'title': data['context']['dispatcher']['stores']['MetaStore']['title'],
            'thumbnail': thumbnail,
        })

        return info_dict
