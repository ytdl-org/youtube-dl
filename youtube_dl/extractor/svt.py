# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class SVTBaseIE(InfoExtractor):
    def _extract_video(self, url, video_id):
        info = self._download_json(url, video_id)

        title = info['context']['title']
        thumbnail = info['context'].get('thumbnailImage')

        video_info = info['video']
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
        subtitle_references = video_info.get('subtitleReferences')
        if isinstance(subtitle_references, list):
            for sr in subtitle_references:
                subtitle_url = sr.get('url')
                if subtitle_url:
                    subtitles.setdefault('sv', []).append({'url': subtitle_url})

        duration = video_info.get('materialLength')
        age_limit = 18 if video_info.get('inappropriateForChildren') else 0

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
        }


class SVTIE(SVTBaseIE):
    _VALID_URL = r'https?://(?:www\.)?svt\.se/wd\?(?:.*?&)?widgetId=(?P<widget_id>\d+)&.*?\barticleId=(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.svt.se/wd?widgetId=23991&sectionId=541&articleId=2900353&type=embed&contextSectionId=123&autostart=false',
        'md5': '9648197555fc1b49e3dc22db4af51d46',
        'info_dict': {
            'id': '2900353',
            'ext': 'flv',
            'title': 'Här trycker Jagr till Giroux (under SVT-intervjun)',
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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        widget_id = mobj.group('widget_id')
        article_id = mobj.group('id')
        return self._extract_video(
            'http://www.svt.se/wd?widgetId=%s&articleId=%s&format=json&type=embed&output=json' % (widget_id, article_id),
            article_id)


class SVTPlayIE(SVTBaseIE):
    IE_DESC = 'SVT Play and Öppet arkiv'
    _VALID_URL = r'https?://(?:www\.)?(?P<host>svtplay|oppetarkiv)\.se/video/(?P<id>[0-9]+)'
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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')
        return self._extract_video(
            'http://www.%s.se/video/%s?output=json' % (host, video_id),
            video_id)
