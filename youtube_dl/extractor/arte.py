# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
    qualities,
    try_get,
    unified_strdate,
    url_or_none,
)

# There are different sources of video in arte.tv, the extraction process
# is different for each one. The videos usually expire in 7 days, so we can't
# add tests.


class ArteTVBaseIE(InfoExtractor):
    def _extract_from_json_url(self, json_url, video_id, lang, title=None):
        info = self._download_json(json_url, video_id)
        player_info = info['videoJsonPlayer']

        vsr = try_get(player_info, lambda x: x['VSR'], dict)
        if not vsr:
            error = None
            if try_get(player_info, lambda x: x['custom_msg']['type']) == 'error':
                error = try_get(
                    player_info, lambda x: x['custom_msg']['msg'], compat_str)
            if not error:
                error = 'Video %s is not available' % player_info.get('VID') or video_id
            raise ExtractorError(error, expected=True)

        upload_date_str = player_info.get('shootingDate')
        if not upload_date_str:
            upload_date_str = (player_info.get('VRA') or player_info.get('VDA') or '').split(' ')[0]

        title = (player_info.get('VTI') or title or player_info['VID']).strip()
        subtitle = player_info.get('VSU', '').strip()
        if subtitle:
            title += ' - %s' % subtitle

        info_dict = {
            'id': player_info['VID'],
            'title': title,
            'description': player_info.get('VDE'),
            'upload_date': unified_strdate(upload_date_str),
            'thumbnail': player_info.get('programImage') or player_info.get('VTU', {}).get('IUR'),
        }
        qfunc = qualities(['MQ', 'HQ', 'EQ', 'SQ'])

        LANGS = {
            'fr': 'F',
            'de': 'A',
            'en': 'E[ANG]',
            'es': 'E[ESP]',
            'it': 'E[ITA]',
            'pl': 'E[POL]',
        }

        langcode = LANGS.get(lang, lang)

        formats = []
        m3u8_formats = []
        for format_id, format_dict in vsr.items():
            f = dict(format_dict)
            format_url = url_or_none(f.get('url'))
            streamer = f.get('streamer')
            if not format_url and not streamer:
                continue
            versionCode = f.get('versionCode')
            l = re.escape(langcode)

            # Language preference from most to least priority
            # Reference: section 6.8 of
            # https://www.arte.tv/sites/en/corporate/files/complete-technical-guidelines-arte-geie-v1-07-1.pdf
            PREFERENCES = (
                # original version in requested language, without subtitles
                r'VO{0}$'.format(l),
                # original version in requested language, with partial subtitles in requested language
                r'VO{0}-ST{0}$'.format(l),
                # original version in requested language, with subtitles for the deaf and hard-of-hearing in requested language
                r'VO{0}-STM{0}$'.format(l),
                # non-original (dubbed) version in requested language, without subtitles
                r'V{0}$'.format(l),
                # non-original (dubbed) version in requested language, with subtitles partial subtitles in requested language
                r'V{0}-ST{0}$'.format(l),
                # non-original (dubbed) version in requested language, with subtitles for the deaf and hard-of-hearing in requested language
                r'V{0}-STM{0}$'.format(l),
                # original version in requested language, with partial subtitles in different language
                r'VO{0}-ST(?!{0}).+?$'.format(l),
                # original version in requested language, with subtitles for the deaf and hard-of-hearing in different language
                r'VO{0}-STM(?!{0}).+?$'.format(l),
                # original version in different language, with partial subtitles in requested language
                r'VO(?:(?!{0}).+?)?-ST{0}$'.format(l),
                # original version in different language, with subtitles for the deaf and hard-of-hearing in requested language
                r'VO(?:(?!{0}).+?)?-STM{0}$'.format(l),
                # original version in different language, without subtitles
                r'VO(?:(?!{0}))?$'.format(l),
                # original version in different language, with partial subtitles in different language
                r'VO(?:(?!{0}).+?)?-ST(?!{0}).+?$'.format(l),
                # original version in different language, with subtitles for the deaf and hard-of-hearing in different language
                r'VO(?:(?!{0}).+?)?-STM(?!{0}).+?$'.format(l),
            )

            for pref, p in enumerate(PREFERENCES):
                if re.match(p, versionCode):
                    lang_pref = len(PREFERENCES) - pref
                    break
            else:
                lang_pref = -1

            media_type = f.get('mediaType')
            if media_type == 'hls':
                m3u8_formats = self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=format_id, fatal=False)
                for m3u8_format in m3u8_formats:
                    m3u8_format['language_preference'] = lang_pref
                continue

            format = {
                'format_id': format_id,
                'preference': -10 if f.get('videoFormat') == 'M3U8' else None,
                'language_preference': lang_pref,
                'format_note': '%s, %s' % (f.get('versionCode'), f.get('versionLibelle')),
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'tbr': int_or_none(f.get('bitrate')),
                'quality': qfunc(f.get('quality')),
            }

            if media_type == 'rtmp':
                format['url'] = f['streamer']
                format['play_path'] = 'mp4:' + f['url']
                format['ext'] = 'flv'
            else:
                format['url'] = f['url']

            formats.append(format)

        self._check_formats(formats, video_id)

        formats.extend(m3u8_formats)
        self._sort_formats(formats)

        info_dict['formats'] = formats
        return info_dict


class ArteTVPlus7IE(ArteTVBaseIE):
    IE_NAME = 'arte.tv:+7'
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/(?P<lang>fr|de|en|es|it|pl)/videos/(?P<id>\d{6}-\d{3}-[AF])'

    _TESTS = [{
        'url': 'https://www.arte.tv/en/videos/088501-000-A/mexico-stealing-petrol-to-survive/',
        'info_dict': {
            'id': '088501-000-A',
            'ext': 'mp4',
            'title': 'Mexico: Stealing Petrol to Survive',
            'upload_date': '20190628',
        },
    }]

    def _real_extract(self, url):
        lang, video_id = re.match(self._VALID_URL, url).groups()
        return self._extract_from_json_url(
            'https://api.arte.tv/api/player/v1/config/%s/%s' % (lang, video_id),
            video_id, lang)


class ArteTVEmbedIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:embed'
    _VALID_URL = r'''(?x)
        https://www\.arte\.tv
        /player/v3/index\.php\?json_url=
        (?P<json_url>
            https?://api\.arte\.tv/api/player/v1/config/
            (?P<lang>[^/]+)/(?P<id>\d{6}-\d{3}-[AF])
        )
    '''

    _TESTS = []

    def _real_extract(self, url):
        json_url, lang, video_id = re.match(self._VALID_URL, url).groups()
        return self._extract_from_json_url(json_url, video_id, lang)


class ArteTVPlaylistIE(ArteTVBaseIE):
    IE_NAME = 'arte.tv:playlist'
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/(?P<lang>fr|de|en|es|it|pl)/videos/(?P<id>RC-\d{6})'

    _TESTS = [{
        'url': 'https://www.arte.tv/en/videos/RC-016954/earn-a-living/',
        'info_dict': {
            'id': 'RC-016954',
            'title': 'Earn a Living',
            'description': 'md5:d322c55011514b3a7241f7fb80d494c2',
        },
        'playlist_mincount': 6,
    }]

    def _real_extract(self, url):
        lang, playlist_id = re.match(self._VALID_URL, url).groups()
        collection = self._download_json(
            'https://api.arte.tv/api/player/v1/collectionData/%s/%s?source=videos'
            % (lang, playlist_id), playlist_id)
        title = collection.get('title')
        description = collection.get('shortDescription') or collection.get('teaserText')
        entries = [
            self._extract_from_json_url(
                video['jsonUrl'], video.get('programId') or playlist_id, lang)
            for video in collection['videos'] if video.get('jsonUrl')]
        return self.playlist_result(entries, playlist_id, title, description)
