# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    float_or_none,
)


class VRTIE(InfoExtractor):
    _VALID_URL = r'https?://(?:deredactie|sporza|cobra(?:\.canvas)?)\.be/cm/(?:[^/]+/)+(?P<id>[^/]+)/*'
    _TESTS = [
        # deredactie.be
        {
            'url': 'http://deredactie.be/cm/vrtnieuws/videozone/programmas/journaal/EP_141025_JOL',
            'md5': '4cebde1eb60a53782d4f3992cbd46ec8',
            'info_dict': {
                'id': '2129880',
                'ext': 'flv',
                'title': 'Het journaal L - 25/10/14',
                'description': None,
                'timestamp': 1414271750.949,
                'upload_date': '20141025',
                'duration': 929,
            }
        },
        # sporza.be
        {
            'url': 'http://sporza.be/cm/sporza/videozone/programmas/extratime/EP_141020_Extra_time',
            'md5': '11f53088da9bf8e7cfc42456697953ff',
            'info_dict': {
                'id': '2124639',
                'ext': 'flv',
                'title': 'Bekijk Extra Time van 20 oktober',
                'description': 'md5:83ac5415a4f1816c6a93f8138aef2426',
                'timestamp': 1413835980.560,
                'upload_date': '20141020',
                'duration': 3238,
            }
        },
        # cobra.be
        {
            'url': 'http://cobra.be/cm/cobra/videozone/rubriek/film-videozone/141022-mv-ellis-cafecorsari',
            'md5': '78a2b060a5083c4f055449a72477409d',
            'info_dict': {
                'id': '2126050',
                'ext': 'flv',
                'title': 'Bret Easton Ellis in Café Corsari',
                'description': 'md5:f699986e823f32fd6036c1855a724ee9',
                'timestamp': 1413967500.494,
                'upload_date': '20141022',
                'duration': 661,
            }
        },
        {
            # YouTube video
            'url': 'http://deredactie.be/cm/vrtnieuws/videozone/nieuws/cultuurenmedia/1.2622957',
            'only_matching': True,
        },
        {
            'url': 'http://cobra.canvas.be/cm/cobra/videozone/rubriek/film-videozone/1.2377055',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'data-video-id="([^"]+)_[^"]+"', webpage, 'video id', fatal=False)

        src = self._search_regex(
            r'data-video-src="([^"]+)"', webpage, 'video src', default=None)

        video_type = self._search_regex(
            r'data-video-type="([^"]+)"', webpage, 'video type', default=None)

        if video_type == 'YouTubeVideo':
            return self.url_result(src, 'Youtube')

        formats = []

        mobj = re.search(
            r'data-video-iphone-server="(?P<server>[^"]+)"\s+data-video-iphone-path="(?P<path>[^"]+)"',
            webpage)
        if mobj:
            formats.extend(self._extract_m3u8_formats(
                '%s/%s' % (mobj.group('server'), mobj.group('path')),
                video_id, 'mp4', m3u8_id='hls', fatal=False))

        if src:
            if determine_ext(src) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
            else:
                formats.extend(self._extract_f4m_formats(
                    '%s/manifest.f4m' % src, video_id, f4m_id='hds', fatal=False))

        if not formats and 'data-video-geoblocking="true"' in webpage:
            self.raise_geo_restricted('This video is only available in Belgium')

        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(webpage)
        timestamp = float_or_none(self._search_regex(
            r'data-video-sitestat-pubdate="(\d+)"', webpage, 'timestamp', fatal=False), 1000)
        duration = float_or_none(self._search_regex(
            r'data-video-duration="(\d+)"', webpage, 'duration', fatal=False), 1000)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'formats': formats,
        }
