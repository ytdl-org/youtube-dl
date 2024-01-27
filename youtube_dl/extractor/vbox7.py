# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    merge_dicts,
    T,
    traverse_obj,
    txt_or_none,
    url_or_none,
)


class Vbox7IE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[^/]+\.)?vbox7\.com/
                        (?:
                            play:|
                            (?:
                                emb/external\.php|
                                player/ext\.swf
                            )\?.*?\bvid=
                        )
                        (?P<id>[\da-fA-F]+)
                    '''
    _EMBED_REGEX = [r'<iframe[^>]+src=(?P<q>["\'])(?P<url>(?:https?:)?//vbox7\.com/emb/external\.php.+?)(?P=q)']
    _GEO_COUNTRIES = ['BG']
    _GEO_BYPASS = False
    _TESTS = [{
        'url': 'https://vbox7.com/play:0946fff23c',
        'md5': '50ca1f78345a9c15391af47d8062d074',
        'info_dict': {
            'id': '0946fff23c',
            'ext': 'mp4',
            'title': 'Борисов: Притеснен съм за бъдещето на България',
            'description': 'По думите му е опасно страната ни да бъде обявена за "сигурна"',
            'thumbnail': r're:^https?://.*\.jpg$',
            'timestamp': 1470982814,
            'upload_date': '20160812',
            'uploader': 'zdraveibulgaria',
        },
        'expected_warnings': [
            'Unable to download webpage',
        ],
    }, {
        'url': 'http://vbox7.com/play:249bb972c2',
        'md5': 'aaf19465e37ec0b30b918df83ec32c50',
        'info_dict': {
            'id': '249bb972c2',
            'ext': 'mp4',
            'title': 'Смях! Чудо - чист за секунди - Скрита камера',
            'description': 'Смях! Чудо - чист за секунди - Скрита камера',
            'timestamp': 1360215023,
            'upload_date': '20130207',
            'uploader': 'svideteliat_ot_varshava',
        },
    }, {
        'url': 'http://vbox7.com/emb/external.php?vid=a240d20f9c&autoplay=1',
        'only_matching': True,
    }, {
        'url': 'http://i49.vbox7.com/player/ext.swf?vid=0946fff23c&autoplay=1',
        'only_matching': True,
    }]

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(cls._EMBED_REGEX[0], webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://vbox7.com/play:%s' % (video_id,)

        now = time.time()
        response = self._download_json(
            'https://www.vbox7.com/aj/player/item/options?vid=%s' % (video_id,),
            video_id, headers={'Referer': url})
        # estimate time to which possible `ago` member is relative
        now = now + 0.5 * (time.time() - now)

        if 'error' in response:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, response['error']), expected=True)

        video_url = traverse_obj(response, ('options', 'src', T(url_or_none)))

        if '/na.mp4' in video_url or '':
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        ext = determine_ext(video_url)
        if ext == 'mpd':
            # In case MPD cannot be parsed, or anyway, get mp4 combined
            # formats usually provided to Safari, iOS, and old Windows
            try:
                formats, subtitles = self._extract_mpd_formats_and_subtitles(
                    video_url, video_id, 'dash', fatal=False)
            except KeyError:
                self.report_warning('Failed to parse MPD manifest')
                formats, subtitles = [], {}

            video = response['options']
            resolutions = (1080, 720, 480, 240, 144)
            highest_res = traverse_obj(video, ('highestRes', T(int))) or resolutions[0]
            for res in traverse_obj(video, ('resolutions', lambda _, r: int(r) > 0)) or resolutions:
                if res > highest_res:
                    continue
                formats.append({
                    'url': video_url.replace('.mpd', '_%d.mp4' % res),
                    'format_id': '%dp' % res,
                    'height': res,
                })
            # if above formats are flaky, enable the line below
            # self._check_formats(formats, video_id)
        else:
            formats = [{
                'url': video_url,
            }]
            subtitles = {}
        self._sort_formats(formats)

        webpage = self._download_webpage(url, video_id, fatal=False) or ''

        info = self._search_json_ld(
            webpage.replace('"/*@context"', '"@context"'), video_id,
            fatal=False) if webpage else {}

        if not info.get('title'):
            info['title'] = traverse_obj(response, (
                'options', 'title', T(txt_or_none))) or self._og_search_title(webpage)

        def if_missing(k):
            return lambda x: None if k in info else x

        info = merge_dicts(info, {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles or None,
        }, info, traverse_obj(response, ('options', {
            'uploader': ('uploader', T(txt_or_none)),
            'timestamp': ('ago', T(if_missing('timestamp')), T(lambda t: int(round((now - t) / 60.0)) * 60)),
            'duration': ('duration', T(if_missing('duration')), T(float_or_none)),
        })))
        if 'thumbnail' not in info:
            info['thumbnail'] = self._proto_relative_url(
                info.get('thumbnail') or self._og_search_thumbnail(webpage),
                'https:'),

        return info
