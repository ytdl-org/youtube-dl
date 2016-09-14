# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    determine_ext,
    parse_age_limit,
    urlencode_postdata,
    ExtractorError,
)


class GoIE(InfoExtractor):
    _BRANDS = {
        'abc': '001',
        'freeform': '002',
        'watchdisneychannel': '004',
        'watchdisneyjunior': '008',
        'watchdisneyxd': '009',
    }
    _VALID_URL = r'https?://(?:(?P<sub_domain>%s)\.)?go\.com/(?:[^/]+/)*(?:vdka(?P<id>\w+)|season-\d+/\d+-(?P<display_id>[^/?#]+))' % '|'.join(_BRANDS.keys())
    _TESTS = [{
        'url': 'http://abc.go.com/shows/castle/video/most-recent/vdka0_g86w5onx',
        'info_dict': {
            'id': '0_g86w5onx',
            'ext': 'mp4',
            'title': 'Sneak Peek: Language Arts',
            'description': 'md5:7dcdab3b2d17e5217c953256af964e9c',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://abc.go.com/shows/after-paradise/video/most-recent/vdka3335601',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        sub_domain, video_id, display_id = re.match(self._VALID_URL, url).groups()
        if not video_id:
            webpage = self._download_webpage(url, display_id)
            video_id = self._search_regex(r'data-video-id=["\']VDKA(\w+)', webpage, 'video id')
        brand = self._BRANDS[sub_domain]
        video_data = self._download_json(
            'http://api.contents.watchabc.go.com/vp2/ws/contents/3000/videos/%s/001/-1/-1/-1/%s/-1/-1.json' % (brand, video_id),
            video_id)['video'][0]
        title = video_data['title']

        formats = []
        for asset in video_data.get('assets', {}).get('asset', []):
            asset_url = asset.get('value')
            if not asset_url:
                continue
            format_id = asset.get('format')
            ext = determine_ext(asset_url)
            if ext == 'm3u8':
                video_type = video_data.get('type')
                if video_type == 'lf':
                    entitlement = self._download_json(
                        'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json',
                        video_id, data=urlencode_postdata({
                            'video_id': video_data['id'],
                            'video_type': video_type,
                            'brand': brand,
                            'device': '001',
                        }))
                    errors = entitlement.get('errors', {}).get('errors', [])
                    if errors:
                        error_message = ', '.join([error['message'] for error in errors])
                        raise ExtractorError('%s said: %s' % (self.IE_NAME, error_message), expected=True)
                    asset_url += '?' + entitlement['uplynkData']['sessionKey']
                formats.extend(self._extract_m3u8_formats(
                    asset_url, video_id, 'mp4', m3u8_id=format_id or 'hls', fatal=False))
            else:
                formats.append({
                    'format_id': format_id,
                    'url': asset_url,
                    'ext': ext,
                })
        self._sort_formats(formats)

        subtitles = {}
        for cc in video_data.get('closedcaption', {}).get('src', []):
            cc_url = cc.get('value')
            if not cc_url:
                continue
            ext = determine_ext(cc_url)
            if ext == 'xml':
                ext = 'ttml'
            subtitles.setdefault(cc.get('lang'), []).append({
                'url': cc_url,
                'ext': ext,
            })

        thumbnails = []
        for thumbnail in video_data.get('thumbnails', {}).get('thumbnail', []):
            thumbnail_url = thumbnail.get('value')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(thumbnail.get('width')),
                'height': int_or_none(thumbnail.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('longdescription') or video_data.get('description'),
            'duration': int_or_none(video_data.get('duration', {}).get('value'), 1000),
            'age_limit': parse_age_limit(video_data.get('tvrating', {}).get('rating')),
            'episode_number': int_or_none(video_data.get('episodenumber')),
            'series': video_data.get('show', {}).get('title'),
            'season_number': int_or_none(video_data.get('season', {}).get('num')),
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
        }
