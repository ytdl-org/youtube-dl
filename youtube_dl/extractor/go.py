# coding: utf-8
from __future__ import unicode_literals

import re

from .adobepass import AdobePassIE
from ..compat import compat_str
from ..utils import (
    int_or_none,
    determine_ext,
    parse_age_limit,
    try_get,
    urlencode_postdata,
    ExtractorError,
)


class GoIE(AdobePassIE):
    _SITE_INFO = {
        'abc': {
            'brand': '001',
            'requestor_id': 'ABC',
            'go': True,
        },
        'freeform': {
            'brand': '002',
            'requestor_id': 'ABCFamily',
            'go': True,
        },
        'watchdisneychannel': {
            'brand': '004',
            'resource_id': 'Disney',
        },
        'watchdisneyjunior': {
            'brand': '008',
            'resource_id': 'DisneyJunior',
        },
        'watchdisneyxd': {
            'brand': '009',
            'resource_id': 'DisneyXD',
        },
        'disneynow': {
            'brand': '011',
            'resource_id': 'Disney',
            'go': True,
        },
        'fxnow.fxnetworks': {
            'brand': '025',
            'requestor_id': 'dtci',
        },
    }
    _VALID_URL = r'''(?x)
                    https?://
                        (?P<sub_domain>
                            (?:(?:%(sites)s)\.)?go|fxnow\.fxnetworks|
                            (?:www\.)?(?:%(sites)s)
                        )\.com/
                        (?:
                            (?:[^/]+/)*(?P<id>[Vv][Dd][Kk][Aa]\w+)|
                            (?:[^/]+/)*(?P<display_id>[^/?\#]+)
                        )
                    ''' % {
        'sites':
            # keep _SITE_INFO in scope
            (lambda s: '|'.join(re.escape(k) for k in s.keys() if s[k].get('go')))(_SITE_INFO),
    }
    _TESTS = [{
        'url': 'http://abc.go.com/shows/designated-survivor/video/most-recent/VDKA3807643',
        'info_dict': {
            'id': 'VDKA3807643',
            'ext': 'mp4',
            'title': 'The Traitor in the White House',
            'description': 'md5:05b009d2d145a1e85d25111bd37222e8',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'skip': 'This content is no longer available.',
    },
        # Disney XD app withdrawn 2018: 'http://watchdisneyxd.go.com/doraemon',
        {
        'url': 'http://freeform.go.com/shows/shadowhunters/episodes/season-2/1-this-guilty-blood',
        'info_dict': {
            'id': 'VDKA3609139',
            'ext': 'mp4',
            'title': 'This Guilty Blood',
            'description': 'md5:f18e79ad1c613798d95fdabfe96cd292',
            'age_limit': 14,
            'duration': 2544,
            'episode': 'Episode 1',
            'thumbnail': r're:https?://.*?\.jpg',
            'season_number': 2,
            'episode_number': 1,
            'season': 'Season 2',
            'series': 'Shadowhunters',
        },
        'params': {
            'geo_bypass_ip_block': '6.48.97.0/24',
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://abc.com/shows/the-rookie/episode-guide/season-04/13-fight-or-flight',
        'info_dict': {
            'id': 'VDKA26139487',
            'ext': 'mp4',
            'title': 'Fight or Flight',
            'episode': 'Episode 13',
            'thumbnail': r're:https?://.*?\.jpg',
            'series': 'The Rookie',
            'description': 'md5:8caf91de9806a1c5f79823059fe80267',
            'duration': 2575,
            'episode_number': 13,
            'season_number': 4,
            'season': 'Season 4',
            'age_limit': 14,
        },
        'params': {
            'geo_bypass_ip_block': '6.48.97.0/24',
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://fxnow.fxnetworks.com/shows/better-things/video/vdka12782841',
        'info_dict': {
            'id': 'VDKA12782841',
            'ext': 'mp4',
            'title': 'First Look: Better Things - Season 2',
            'description': 'md5:fa73584a95761c605d9d54904e35b407',
            'duration': 161,
            'series': 'Better Things',
            'age_limit': 14,
            'thumbnail': r're:https?://.*?\.jpg',
        },
        'params': {
            'geo_bypass_ip_block': '6.48.97.0/24',
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://abc.com/shows/modern-family/episode-guide/season-01/101-pilot',
        'info_dict': {
            'id': 'VDKA22600213',
            'ext': 'mp4',
            'title': 'Pilot',
            'description': 'md5:74306df917cfc199d76d061d66bebdb4',
            'season': 'Season 1',
            'episode': 'Episode 1',
            'series': 'Modern Family',
            'season_number': 1,
            'duration': 1301,
            'episode_number': 1,
            'age_limit': 0,
            'thumbnail': r're:https?://.*?\.jpg',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'skip': 'The content you’re looking for is not available',
    }, {
        'url': 'http://abc.go.com/shows/the-catch/episode-guide/season-01/10-the-wedding',
        'only_matching': True,
    }, {
        'url': 'http://abc.go.com/shows/world-news-tonight/episode-guide/2017-02/17-021717-intense-stand-off-between-man-with-rifle-and-police-in-oakland',
        'only_matching': True,
    }, {
        # brand 004
        'url': 'http://disneynow.go.com/shows/big-hero-6-the-series/season-01/episode-10-mr-sparkles-loses-his-sparkle/vdka4637915',
        'only_matching': True,
    }, {
        # brand 008
        'url': 'http://disneynow.go.com/shows/minnies-bow-toons/video/happy-campers/vdka4872013',
        'only_matching': True,
    }, {
        'url': 'https://disneynow.com/shows/minnies-bow-toons/video/happy-campers/vdka4872013',
        'only_matching': True,
    }, {
        'url': 'https://www.freeform.com/shows/cruel-summer/episode-guide/season-01/01-happy-birthday-jeanette-turner',
        'only_matching': True,
    }, {
        # will expire and need to be replaced by a newer episode
        'url': 'https://disneynow.com/shows/ducktales-disney-channel/season-03/episode-22-the-last-adventure/vdka22464554',
        'info_dict': {
            'id': 'VDKA22464554',
            'ext': 'mp4',
            'title': 'The Last Adventure!',
            'description': 'The Duck Family uncovers earth-shattering secrets in a final standoff with FOWL, with the future of adventure hanging in the balance.',
            'season_number': 3,
            'episode': 'Episode 22',
            'season': 'Season 3',
            'episode_number': 22,
            'age_limit': 7,
            'series': 'DuckTales',
            'thumbnail': r're:https?://.*?\.jpg',
        },
        'params': {
            # AES-128: ffmpeg
            'skip_download': True,
        },
    }, {
        'url': 'https://disneynow.com/shows/ducktales-disney-channel',
        'info_dict': {
            'title': 'DuckTales TV Show',
            'id': 'SH553923438',
        },
        'playlist_mincount': 30,
        'expected_warnings': ['Ignoring subtitle tracks', ],
    }]

    def _extract_videos(self, brand, video_id='-1', show_id='-1'):
        display_id = video_id if video_id != '-1' else show_id
        data = self._download_json(
            'http://api.contents.watchabc.go.com/vp2/ws/contents/4000/videos/%s/001/-1/%s/-1/%s/-1/-1.json' % (brand, show_id, video_id),
            display_id, fatal=False)
        return try_get(data, lambda x: x['video'], list)

    def _raise_extractor_error(self, video_id, msg, expected=True):
        raise ExtractorError('%s said: %s: %s' % (self.IE_NAME, video_id, msg), expected=expected)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        sub_domain = re.sub(r'^(?:www\.)?(.+?)(?:\.go)?$', r'\1', mobj.group('sub_domain') or '')
        video_id, display_id = mobj.group('id', 'display_id')
        display_id = display_id or video_id
        site_info = self._SITE_INFO.get(sub_domain, {})
        brand = site_info.get('brand')
        if not video_id or not site_info:
            webpage = self._download_webpage(url, display_id, expected_status=[404])
            if re.search(r'(?:>|=\s*")Page not found\s', webpage):
                self._raise_extractor_error(display_id, 'Page not found')
            data = self._parse_json(
                self._search_regex(
                    r'["\']__abc_com__["\']\s*\]\s*=\s*({.+?})\s*;', webpage,
                    'data', default='{}'),
                display_id, fatal=False)
            # https://abc.com/shows/ExtractorErrmodern-family/episode-guide/season-01/101-pilot
            layout = try_get(data, lambda x: x['page']['content']['video']['layout'], dict)
            video_id = None
            if layout:
                video_id = try_get(
                    layout,
                    (lambda x: x['videoid'], lambda x: x['video']['id']),
                    compat_str)
            if not video_id:
                video_id = self._search_regex(
                    (
                        # There may be inner quotes, e.g. data-video-id="'VDKA3609139'"
                        # from http://freeform.go.com/shows/shadowhunters/episodes/season-2/1-this-guilty-blood
                        r'data-video-id\s*=\s*["\']{,2}(VDKA\w+)',
                        # page.analytics.videoIdCode
                        r'\bvideoIdCode["\']\s*:\s*["\']((?:vdka|VDKA)\w+)',
                        # This obsolete pattern, if matched, overrides detection of DisneyNow show pages
                        # https://abc.com/shows/the-rookie/episode-guide/season-02/03-the-bet
                        # r'\b(?:video)?id["\']\s*:\s*["\'](VDKA\w+)'
                    ), webpage, 'video id', default=video_id)
            if not site_info:
                brand = self._search_regex(
                    (r'data-brand=\s*["\']\s*(\d+)',
                     r'data-page-brand=\s*["\']\s*(\d+)',
                     r'"brand"\s*:\s*"(\d+)"'), webpage, 'brand',
                    # default to a brand that has an active domain
                    default='011')
                site_info = next(
                    si for si in self._SITE_INFO.values()
                    if si.get('brand') == brand)
            if not video_id:
                # show extraction works for Disney, DisneyJunior and DisneyXD
                # ABC and Freeform has different layout
                show_id = self._search_regex(r'data-show-id=["\']*(SH\d+)', webpage, 'show id')
                videos = self._extract_videos(brand, show_id=show_id)
                show_title = (
                    self._search_regex(r'data-show-title="([^"]+)"', webpage, 'show title', default=None)
                    or self._og_search_title(webpage, fatal=False))
                if show_title:
                    show_title = re.sub(r'^(?:Watch\s+)?(.+?)(?:\s*\|\s*Disney.*)?$', r'\1', show_title)
                entries = []
                for video in videos:
                    entries.append(self.url_result(
                        video['url'], 'Go', video.get('id'), video.get('title')))
                entries.reverse()
                return self.playlist_result(entries, show_id, show_title)
        video_data = self._extract_videos(brand, video_id)
        if not video_data:
            self._raise_extractor_error(video_id, 'No video found')
        video_id = try_get(video_data, lambda x: x[0]['id'], compat_str)
        if not video_id:
            self._raise_extractor_error(video_id, 'No video data', expected=False)
        video_data = video_data[0]
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
                    requestor_id = site_info.get('requestor_id', 'DisneyChannels')
                    resource = site_info.get('resource_id') or self._get_mvpd_resource(
                        requestor_id, title, video_id, None)
                    auth = self._extract_mvpd_auth(
                        url, video_id, requestor_id, resource)
                    data.update({
                        'token': auth,
                        'token_type': 'ap',
                        'adobe_requestor_id': requestor_id,
                    })
                else:
                    self._initialize_geo_bypass({'countries': ['US']})
                entitlement = self._download_json(
                    'https://api.entitlement.watchabc.go.com/vp2/ws-secure/entitlement/2020/authorize.json',
                    video_id, data=urlencode_postdata(data))
                errors = entitlement.get('errors', {}).get('errors', [])
                if errors:
                    for error in errors:
                        if error.get('code') == 1002:
                            self.raise_geo_restricted(
                                error['message'], countries=['US'])
                    error_message = ', '.join([error['message'] for error in errors])
                    self._raise_extractor_error(video_id, error_message)
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
                        'quality': 1,
                        # 'preference': 1,
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
