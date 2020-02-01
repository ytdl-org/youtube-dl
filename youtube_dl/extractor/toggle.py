# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    sanitized_Request,
)


class ToggleIE(InfoExtractor):
    IE_NAME = 'toggle'
    _VALID_URL = r'https?://video\.toggle\.sg/(?:en|zh)/(?:[^/]+/){2,}(?P<id>[0-9]+)'
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
        # this also tests correct video id extraction
        'note': 'm3u8 links are geo-restricted, but Android/mp4 is okay',
        'url': 'http://video.toggle.sg/en/series/28th-sea-games-5-show/28th-sea-games-5-show-ep11/332861',
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
    }, {
        'url': 'https://video.toggle.sg/en/tv-show/news/may-2017-cna-singapore-tonight/fri-19-may-2017/512456',
        'only_matching': True,
    }, {
        'url': 'http://video.toggle.sg/en/channels/eleven-plus/401585',
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

        webpage = self._download_webpage(
            url, video_id, note='Downloading video page')

        api_user = self._search_regex(
            r'apiUser\s*:\s*(["\'])(?P<user>.+?)\1', webpage, 'apiUser',
            default=self._API_USER, group='user')
        api_pass = self._search_regex(
            r'apiPass\s*:\s*(["\'])(?P<pass>.+?)\1', webpage, 'apiPass',
            default=self._API_PASS, group='pass')

        params = {
            'initObj': {
                'Locale': {
                    'LocaleLanguage': '',
                    'LocaleCountry': '',
                    'LocaleDevice': '',
                    'LocaleUserState': 0
                },
                'Platform': 0,
                'SiteGuid': 0,
                'DomainID': '0',
                'UDID': '',
                'ApiUser': api_user,
                'ApiPass': api_pass
            },
            'MediaID': video_id,
            'mediaType': 0,
        }

        req = sanitized_Request(
            'http://tvpapi.as.tvinci.com/v2_9/gateways/jsonpostgw.aspx?m=GetMediaInfo',
            json.dumps(params).encode('utf-8'))
        info = self._download_json(req, video_id, 'Downloading video info json')

        title = info['MediaName']

        formats = []
        for video_file in info.get('Files', []):
            video_url, vid_format = video_file.get('URL'), video_file.get('Format')
            if not video_url or video_url == 'NA' or not vid_format:
                continue
            ext = determine_ext(video_url)
            vid_format = vid_format.replace(' ', '')
            # if geo-restricted, m3u8 is inaccessible, but mp4 is okay
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, ext='mp4', m3u8_id=vid_format,
                    note='Downloading %s m3u8 information' % vid_format,
                    errnote='Failed to download %s m3u8 information' % vid_format,
                    fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, mpd_id=vid_format,
                    note='Downloading %s MPD manifest' % vid_format,
                    errnote='Failed to download %s MPD manifest' % vid_format,
                    fatal=False))
            elif ext == 'ism':
                formats.extend(self._extract_ism_formats(
                    video_url, video_id, ism_id=vid_format,
                    note='Downloading %s ISM manifest' % vid_format,
                    errnote='Failed to download %s ISM manifest' % vid_format,
                    fatal=False))
            elif ext in ('mp4', 'wvm'):
                # wvm are drm-protected files
                formats.append({
                    'ext': ext,
                    'url': video_url,
                    'format_id': vid_format,
                    'preference': self._FORMAT_PREFERENCES.get(ext + '-' + vid_format) or -1,
                    'format_note': 'DRM-protected video' if ext == 'wvm' else None
                })
        if not formats:
            # Most likely because geo-blocked
            raise ExtractorError('No downloadable videos found', expected=True)
        self._sort_formats(formats)

        duration = int_or_none(info.get('Duration'))
        description = info.get('Description')
        created_at = parse_iso8601(info.get('CreationDate') or None)

        average_rating = float_or_none(info.get('Rating'))
        view_count = int_or_none(info.get('ViewCounter') or info.get('view_counter'))
        like_count = int_or_none(info.get('LikeCounter') or info.get('like_counter'))

        thumbnails = []
        for picture in info.get('Pictures', []):
            if not isinstance(picture, dict):
                continue
            pic_url = picture.get('URL')
            if not pic_url:
                continue
            thumbnail = {
                'url': pic_url,
            }
            pic_size = picture.get('PicSize', '')
            m = re.search(r'(?P<width>\d+)[xX](?P<height>\d+)', pic_size)
            if m:
                thumbnail.update({
                    'width': int(m.group('width')),
                    'height': int(m.group('height')),
                })
            thumbnails.append(thumbnail)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': created_at,
            'average_rating': average_rating,
            'view_count': view_count,
            'like_count': like_count,
            'thumbnails': thumbnails,
            'formats': formats,
        }
