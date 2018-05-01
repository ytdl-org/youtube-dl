# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    determine_ext,
    dict_get,
    int_or_none,
    try_get,
    urljoin,
    compat_str,
)


class SVTBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ['SE']

    def _extract_video(self, video_info, video_id):
        is_live = dict_get(video_info, ('live', 'simulcast'), default=False)
        m3u8_protocol = 'm3u8' if is_live else 'm3u8_native'
        formats = []
        for vr in video_info['videoReferences']:
            player_type = vr.get('playerType') or vr.get('format')
            vurl = vr['url']
            ext = determine_ext(vurl)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    vurl, video_id,
                    ext='mp4', entry_protocol=m3u8_protocol,
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
            'is_live': is_live,
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


class SVTPlayBaseIE(SVTBaseIE):
    _SVTPLAY_RE = r'root\s*\[\s*(["\'])_*svtplay\1\s*\]\s*=\s*(?P<json>{.+?})\s*;\s*\n'


class SVTPlayIE(SVTPlayBaseIE):
    IE_DESC = 'SVT Play and Öppet arkiv'
    _VALID_URL = r'https?://(?:www\.)?(?:svtplay|oppetarkiv)\.se/(?:video|klipp|kanaler)/(?P<id>[^/?#&]+)'
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
    }, {
        'url': 'https://www.svtplay.se/kanaler/svt1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(
            self._search_regex(
                self._SVTPLAY_RE, webpage, 'embedded data', default='{}',
                group='json'),
            video_id, fatal=False)

        thumbnail = self._og_search_thumbnail(webpage)

        def adjust_title(info):
            if info['is_live']:
                info['title'] = self._live_title(info['title'])

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
                adjust_title(info_dict)
                return info_dict

        video_id = self._search_regex(
            r'<video[^>]+data-video-id=["\']([\da-zA-Z-]+)',
            webpage, 'video id', default=None)

        if video_id:
            data = self._download_json(
                'https://api.svt.se/videoplayer-api/video/%s' % video_id,
                video_id, headers=self.geo_verification_headers())
            info_dict = self._extract_video(data, video_id)
            if not info_dict.get('title'):
                info_dict['title'] = re.sub(
                    r'\s*\|\s*.+?$', '',
                    info_dict.get('episode') or self._og_search_title(webpage))
            adjust_title(info_dict)
            return info_dict


class SVTSeriesIE(SVTPlayBaseIE):
    _VALID_URL = r'https?://(?:www\.)?svtplay\.se/(?P<id>[^/?&#]+)'
    _TESTS = [{
        'url': 'https://www.svtplay.se/rederiet',
        'info_dict': {
            'id': 'rederiet',
            'title': 'Rederiet',
            'description': 'md5:505d491a58f4fcf6eb418ecab947e69e',
        },
        'playlist_mincount': 318,
    }, {
        'url': 'https://www.svtplay.se/rederiet?tab=sasong2',
        'info_dict': {
            'id': 'rederiet-sasong2',
            'title': 'Rederiet - Säsong 2',
            'description': 'md5:505d491a58f4fcf6eb418ecab947e69e',
        },
        'playlist_count': 12,
    }]

    @classmethod
    def suitable(cls, url):
        return False if SVTIE.suitable(url) or SVTPlayIE.suitable(url) else super(SVTSeriesIE, cls).suitable(url)

    def _real_extract(self, url):
        series_id = self._match_id(url)

        qs = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        season_slug = qs.get('tab', [None])[0]

        if season_slug:
            series_id += '-%s' % season_slug

        webpage = self._download_webpage(
            url, series_id, 'Downloading series page')

        root = self._parse_json(
            self._search_regex(
                self._SVTPLAY_RE, webpage, 'content', group='json'),
            series_id)

        season_name = None

        entries = []
        for season in root['relatedVideoContent']['relatedVideosAccordion']:
            if not isinstance(season, dict):
                continue
            if season_slug:
                if season.get('slug') != season_slug:
                    continue
                season_name = season.get('name')
            videos = season.get('videos')
            if not isinstance(videos, list):
                continue
            for video in videos:
                content_url = video.get('contentUrl')
                if not content_url or not isinstance(content_url, compat_str):
                    continue
                entries.append(
                    self.url_result(
                        urljoin(url, content_url),
                        ie=SVTPlayIE.ie_key(),
                        video_title=video.get('title')
                    ))

        metadata = root.get('metaData')
        if not isinstance(metadata, dict):
            metadata = {}

        title = metadata.get('title')
        season_name = season_name or season_slug

        if title and season_name:
            title = '%s - %s' % (title, season_name)
        elif season_slug:
            title = season_slug

        return self.playlist_result(
            entries, series_id, title, metadata.get('description'))
