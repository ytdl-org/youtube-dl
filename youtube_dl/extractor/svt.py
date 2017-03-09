# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    dict_get,
    int_or_none,
    try_get,
)


class SVTBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ['SE']

    def _extract_video(self, video_info, video_id):
        formats = []
        for vr in video_info['videoReferences']:
            player_type = vr.get('playerType') or vr.get('format')
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
        if not formats and video_info.get('rights', {}).get('geoBlockedSweden'):
            self.raise_geo_restricted(
                'This video is only available in Sweden',
                countries=self._GEO_COUNTRIES)
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

        title = video_info.get('title')

        series = video_info.get('programTitle')
        season_number = int_or_none(video_info.get('season'))
        episode = video_info.get('episodeTitle')
        episode_number = int_or_none(video_info.get('episodeNumber'))

        duration = int_or_none(dict_get(video_info, ('materialLength', 'contentDuration')))
        age_limit = None
        adult = dict_get(
            video_info, ('inappropriateForChildren', 'blockedForChildren'),
            skip_false_values=False)
        if adult is not None:
            age_limit = 18 if adult else 0

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'duration': duration,
            'age_limit': age_limit,
            'series': series,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        widget_id = mobj.group('widget_id')
        article_id = mobj.group('id')

        info = self._download_json(
            'http://www.svt.se/wd?widgetId=%s&articleId=%s&format=json&type=embed&output=json' % (widget_id, article_id),
            article_id)

        info_dict = self._extract_video(info['video'], article_id)
        info_dict['title'] = info['context']['title']
        return info_dict


class SVTPlayIE(SVTBaseIE):
    IE_DESC = 'SVT Play and Öppet arkiv'
    _VALID_URL = r'https?://(?:www\.)?(?:svtplay|oppetarkiv)\.se/(?:video|klipp)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.svtplay.se/video/5996901/flygplan-till-haile-selassie/flygplan-till-haile-selassie-2',
        'md5': '2b6704fe4a28801e1a098bbf3c5ac611',
        'info_dict': {
            'id': '5996901',
            'ext': 'mp4',
            'title': 'Flygplan till Haile Selassie',
            'duration': 3527,
            'thumbnail': r're:^https?://.*[\.-]jpg$',
            'age_limit': 0,
            'subtitles': {
                'sv': [{
                    'ext': 'wsrt',
                }]
            },
        },
    }, {
        # geo restricted to Sweden
        'url': 'http://www.oppetarkiv.se/video/5219710/trollflojten',
        'only_matching': True,
    }, {
        'url': 'http://www.svtplay.se/klipp/9023742/stopptid-om-bjorn-borg',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(
            self._search_regex(
                r'root\["__svtplay"\]\s*=\s*([^;]+);',
                webpage, 'embedded data', default='{}'),
            video_id, fatal=False)

        thumbnail = self._og_search_thumbnail(webpage)

        if data:
            video_info = try_get(
                data, lambda x: x['context']['dispatcher']['stores']['VideoTitlePageStore']['data']['video'],
                dict)
            if video_info:
                info_dict = self._extract_video(video_info, video_id)
                info_dict.update({
                    'title': data['context']['dispatcher']['stores']['MetaStore']['title'],
                    'thumbnail': thumbnail,
                })
                return info_dict

        video_id = self._search_regex(
            r'<video[^>]+data-video-id=["\']([\da-zA-Z-]+)',
            webpage, 'video id', default=None)

        if video_id:
            data = self._download_json(
                'http://www.svt.se/videoplayer-api/video/%s' % video_id, video_id)
            info_dict = self._extract_video(data, video_id)
            if not info_dict.get('title'):
                info_dict['title'] = re.sub(
                    r'\s*\|\s*.+?$', '',
                    info_dict.get('episode') or self._og_search_title(webpage))
            return info_dict
