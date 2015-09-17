# coding: utf-8
from __future__ import unicode_literals

import json
import re
import itertools

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    determine_ext,
    parse_iso8601,
    remove_end
)
from ..compat import compat_urllib_request


class ToggleSgIE(InfoExtractor):
    IE_NAME = 'togglesg'
    _VALID_URL = r'https?://video\.toggle\.sg/(?:(en|zh))/(?:(series|clips|movies))/.+?/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://video.toggle.sg/en/series/lion-moms-tif/trailers/lion-moms-premier/343115',
        'info_dict': {
            'id': '343115',
            'ext': 'mp4',
            'title': 'Lion Moms Premiere',
            'description': 'md5:aea1149404bff4d7f7b6da11fafd8e6b',
            'upload_date': '20150910',
            'timestamp': 1441858274,
        },
        'params': {
            'skip_download': 'm3u8 download',
        }
    }, {
        'note': 'DRM-protected video',
        'url': 'http://video.toggle.sg/en/movies/dug-s-special-mission/341413',
        'info_dict': {
            'id': '341413',
            'ext': 'wvm',
            'title': 'Dug\'s Special Mission',
            'description': 'md5:e86c6f4458214905c1772398fabc93e0',
            'upload_date': '20150827',
            'timestamp': 1440644006,
        },
        'params': {
            'skip_download': 'DRM-protected wvm download',
        }
    }, {
        'note': 'm3u8 links are geo-restricted, but Android/mp4 is okay',
        'url': 'http://video.toggle.sg/en/series/28th-sea-games-5-show/ep11/332861',
        'info_dict': {
            'id': '332861',
            'ext': 'mp4',
            'title': '28th SEA Games (5 Show) -  Episode  11',
            'description': 'md5:3cd4f5f56c7c3b1340c50a863f896faa',
            'upload_date': '20150605',
            'timestamp': 1433480166,
        },
        'params': {
            'skip_download': 'DRM-protected wvm download',
        },
        'skip': 'm3u8 links are geo-restricted'
    }, {
        'url': 'http://video.toggle.sg/en/clips/seraph-sun-aloysius-will-suddenly-sing-some-old-songs-in-high-pitch-on-set/343331',
        'only_matching': True,
    }, {
        'url': 'http://video.toggle.sg/zh/series/zero-calling-s2-hd/ep13/336367',
        'only_matching': True,
    }, {
        'url': 'http://video.toggle.sg/en/series/vetri-s2/webisodes/jeeva-is-an-orphan-vetri-s2-webisode-7/342302',
        'only_matching': True,
    }, {
        'url': 'http://video.toggle.sg/en/movies/seven-days/321936',
        'only_matching': True,
    }]

    _FORMAT_PREFERENCES = {
        'wvm-STBMain': -10,
        'wvm-iPadMain': -20,
        'wvm-iPhoneMain': -30,
        'wvm-Android': -40,
    }
    _API_USER = 'tvpapi_147'
    _API_PASS = '11111'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id, note='Downloading video page')

        api_user = self._search_regex(
            r'apiUser:\s*"([^"]+)"', webpage, 'apiUser', default=self._API_USER, fatal=False)
        api_pass = self._search_regex(
            r'apiPass:\s*"([^"]+)"', webpage, 'apiPass', default=self._API_PASS, fatal=False)

        params = {
            'initObj': {
                'Locale': {
                    'LocaleLanguage': '', 'LocaleCountry': '',
                    'LocaleDevice': '', 'LocaleUserState': 0
                },
                'Platform': 0, 'SiteGuid': 0, 'DomainID': '0', 'UDID': '',
                'ApiUser': api_user, 'ApiPass': api_pass
            },
            'MediaID': video_id,
            'mediaType': 0,
        }

        req = compat_urllib_request.Request(
            'http://tvpapi.as.tvinci.com/v2_9/gateways/jsonpostgw.aspx?m=GetMediaInfo',
            json.dumps(params).encode('utf-8'))
        info = self._download_json(req, video_id, 'Downloading video info json')

        title = info['MediaName']
        duration = int_or_none(info.get('Duration'))
        thumbnail = info.get('PicURL')
        description = info.get('Description')
        created_at = parse_iso8601(info.get('CreationDate') or None)
        formats = []

        for video_file in info.get('Files', []):
            ext = determine_ext(video_file['URL'])
            vid_format = video_file['Format'].replace(' ', '')
            # if geo-restricted, m3u8 is inaccessible, but mp4 is okay
            if ext == 'm3u8':
                m3u8_formats = self._extract_m3u8_formats(
                    video_file['URL'], video_id, ext='mp4', m3u8_id=vid_format,
                    note='Downloading %s m3u8 information' % vid_format,
                    errnote='Failed to download %s m3u8 information' % vid_format,
                    fatal=False
                )
                if m3u8_formats:
                    formats.extend(m3u8_formats)
            if ext in ['mp4', 'wvm']:
                # wvm are drm-protected files
                formats.append({
                    'ext': ext,
                    'url': video_file['URL'],
                    'format_id': vid_format,
                    'preference': self._FORMAT_PREFERENCES.get(ext + '-' + vid_format) or -1,
                    'format_note': 'DRM-protected video' if ext == 'wvm' else None
                })

        if not formats:
            # Most likely because geo-blocked
            raise ExtractorError('No downloadable videos found', expected=True)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': created_at,
            'thumbnail': thumbnail,
            'formats': formats,
        }
