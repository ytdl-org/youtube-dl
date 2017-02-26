# coding: utf-8
from __future__ import unicode_literals

import re

from .adobepass import AdobePassIE
from ..utils import (
    int_or_none,
    determine_ext,
    parse_age_limit,
    urlencode_postdata,
    ExtractorError,
)


class GoIE(AdobePassIE):
    _SITE_INFO = {
        'abc': {
            'brand': '001',
            'requestor_id': 'ABC',
        },
        'freeform': {
            'brand': '002',
            'requestor_id': 'ABCFamily',
        },
        'watchdisneychannel': {
            'brand': '004',
            'requestor_id': 'Disney',
        },
        'watchdisneyjunior': {
            'brand': '008',
            'requestor_id': 'DisneyJunior',
        },
        'watchdisneyxd': {
            'brand': '009',
            'requestor_id': 'DisneyXD',
        }
    }
    _VALID_URL = r'https?://(?:(?P<sub_domain>%s)\.)?go\.com/(?:[^/]+/)*(?:vdka(?P<id>\w+)|season-\d+/\d+-(?P<display_id>[^/?#]+))' % '|'.join(_SITE_INFO.keys())
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
            video_id = self._search_regex(
                # There may be inner quotes, e.g. data-video-id="'VDKA3609139'"
                # from http://freeform.go.com/shows/shadowhunters/episodes/season-2/1-this-guilty-blood
                r'data-video-id=["\']*VDKA(\w+)', webpage, 'video id')
        site_info = self._SITE_INFO[sub_domain]
        brand = site_info['brand']
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
                data = {
                    'video_id': video_data['id'],
                    'video_type': video_type,
                    'brand': brand,
                    'device': '001',
                }
                if video_data.get('accesslevel') == '1':
                    requestor_id = site_info['requestor_id']
                    resource = self._get_mvpd_resource(
                        requestor_id, title, video_id, None)
                    auth = self._extract_mvpd_auth(
                        url, video_id, requestor_id, resource)
                    data.update({
                        'token': auth,
                        'token_type': 'ap',
                        'adobe_requestor_id': requestor_id,
                    })
                else:
                    self._initialize_geo_bypass(['US'])
                entitlement = self._download_json(
                    'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json',
                    video_id, data=urlencode_postdata(data), headers=self.geo_verification_headers())
                errors = entitlement.get('errors', {}).get('errors', [])
                if errors:
                    for error in errors:
                        if error.get('code') == 1002:
                            self.raise_geo_restricted(
                                error['message'], countries=['US'])
                    error_message = ', '.join([error['message'] for error in errors])
                    raise ExtractorError('%s said: %s' % (self.IE_NAME, error_message), expected=True)
                asset_url += '?' + entitlement['uplynkData']['sessionKey']
                formats.extend(self._extract_m3u8_formats(
                    asset_url, video_id, 'mp4', m3u8_id=format_id or 'hls', fatal=False))
            else:
                f = {
                    'format_id': format_id,
                    'url': asset_url,
                    'ext': ext,
                }
                if re.search(r'(?:/mp4/source/|_source\.mp4)', asset_url):
                    f.update({
                        'format_id': ('%s-' % format_id if format_id else '') + 'SOURCE',
                        'preference': 1,
                    })
                else:
                    mobj = re.search(r'/(\d+)x(\d+)/', asset_url)
                    if mobj:
                        height = int(mobj.group(2))
                        f.update({
                            'format_id': ('%s-' % format_id if format_id else '') + '%dP' % height,
                            'width': int(mobj.group(1)),
                            'height': height,
                        })
                formats.append(f)
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
