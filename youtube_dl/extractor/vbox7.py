# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    int_or_none,
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
    _GEO_COUNTRIES = ['BG']
    _TESTS = [{
        'url': 'http://vbox7.com/play:0946fff23c',
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
        'expected_warnings': ['Failed to parse MPD manifest.*'],
        # direct connection should work
        # 'params': {
        #     'proxy': '127.0.0.1:8118',
        # },
    }, {
        'url': 'http://vbox7.com/play:249bb972c2',
        'md5': '99f65c0c9ef9b682b97313e052734c3f',
        'info_dict': {
            'id': '249bb972c2',
            'ext': 'mp4',
            'title': 'Смях! Чудо - чист за секунди - Скрита камера',
        },
        'skip': 'georestricted',
    }, {
        'url': 'http://vbox7.com/emb/external.php?vid=a240d20f9c&autoplay=1',
        'only_matching': True,
    }, {
        'url': 'http://i49.vbox7.com/player/ext.swf?vid=0946fff23c&autoplay=1',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(?P<q>["\'])(?P<url>(?:https?:)?//vbox7\.com/emb/external\.php.+?)(?P=q)',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Download webpage first. It should be more natural than download json first,
        # though crucial video information is not extracted from it
        webpage = self._download_webpage(
            'https://www.vbox7.com/play:%s' % video_id, video_id, fatal=None)

        response = self._download_json(
            'https://www.vbox7.com/ajax/video/nextvideo.php?vid=%s' % video_id,
            video_id)

        if 'error' in response:
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, response['error']), expected=True)
        elif response.get('success') is False:
            raise ExtractorError(
                'Unable to get video information. Please make sure that the URL is alive and playable in a browser.', expected=True)

        video = response['options']

        title = video['title']
        video_url = video['src']

        if '/na.mp4' in video_url:
            self.raise_geo_restricted(countries=self._GEO_COUNTRIES)

        uploader = video.get('uploader')

        formats = []
        if re.search(r'\.mpd\b', video_url):
            # youtube-dl cannot parse GPAC generated MPD used here, but try anyway,
            # and use mp4 formats (usually provided to Safari, iOS and old Win's) on failure
            try:
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, 'dash', fatal=False))
            except KeyError:
                self.report_warning('Failed to parse MPD manifest. Use alternate mp4 formats')
                highest_res = video.get('highestRes') or 1080
                resolutions = video.get('resolutions') or (1080, 720, 480, 240, 144)
                for res in resolutions:
                    if not res or res > highest_res:
                        continue
                    formats.append({
                        'url': video_url.replace('.mpd', '_%s.mp4' % res),
                        'format_id': compat_str(res),
                        'height': res,
                    })
        else:
            formats.append({
                'url': video_url,
            })

        self._sort_formats(formats)

        info = {}
        thumbnail = None

        if webpage:
            def transform_source(src):
                # fix malformed JSON-LD. replace raw CRLFs with escaped LFs
                return re.sub(
                    r'"[^"]+"', lambda m: re.sub(r'\r?\n', r'\\n', m.group(0)), src)

            info = self._search_json_ld(
                webpage.replace('"/*@context"', '"@context"'), video_id,
                transform_source=transform_source,
                default={})
            if not info:
                description = self._html_search_meta(
                    ['description', 'og:description'], webpage, default=None)
                if description:
                    description = description.replace('\r ', '\n')
                info.update({
                    'description': description,
                    'duration': int_or_none(video.get('duration')),
                })
            thumbnail = info.get('thumbnail') or self._og_search_thumbnail(webpage)

        info.update({
            'id': video_id,
            'title': title,
            'formats': formats,
            'uploader': uploader,
            'thumbnail': self._proto_relative_url(thumbnail, 'https:'),
        })
        return info
