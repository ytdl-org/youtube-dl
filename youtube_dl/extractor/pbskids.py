# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    js_to_json,
    orderedSet,
    unified_strdate,
    US_RATINGS,
)


class PBSKIDSIE(InfoExtractor):
    IE_NAME = 'pbskids'
    IE_DESC = 'Public Broadcasting Service (PBS) for Kids'

    _VALID_URL = r'''(?x)https?://
        (?:
           # Article with embedded player
           pbskids\.org/video/[^/]+/(?P<episode_id>)
        )
    '''

    _GEO_COUNTRIES = ['US']

    _TESTS = [
        {
            'url': 'https://pbskids.org/video/super-why/2206965769',
            'md5': '173dc391afd361fa72eab5d3d918968d',
            'info_dict': {
                'id': '2206965769',
                'ext': 'mp4',
                'title': 'Jasper\'s Cowboy Wish',
                'duration': 1510,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
    ]
    _ERRORS = {
        101: 'We\'re sorry, but this video is not yet available.',
        403: 'We\'re sorry, but this video is not available in your region due to right restrictions.',
        404: 'We are experiencing technical difficulties that are preventing us from playing the video at this time. Please check back again soon.',
        410: 'This video has expired and is no longer available for online streaming.',
    }

    def _real_initialize(self):
        cookie = (self._download_json(
            'http://localization.services.pbs.org/localize/auto/cookie/',
            None, headers=self.geo_verification_headers(), fatal=False) or {}).get('cookie')
        if cookie:
            station = self._search_regex(r'#?s=\["([^"]+)"', cookie, 'station')
            if station:
                self._set_cookie('.pbs.org', 'pbsol.station', station)

    def _extract_webpage(self, url):
        mobj = re.match(self._VALID_URL, url)

        description = None

        video_id = None
        display_id = None
        info = None
        episode_id = mobj.group('episode_id')

        if episode_id:
            webpage = self._download_webpage(url, episode_id)
            description = self._html_search_meta(
                'description', webpage, default=None)
            upload_date = unified_strdate(self._search_regex(
                r'air_date"\:"([^"]+)"',
                webpage, 'upload date', default=None))
            # m3u8 url
            MULTI_PART_REGEXES = (
                r'URI"\:"https?\:.?/.?/urs\.pbs\.org.?/redirect.?/([\d\w]+)',
            )
            for p in MULTI_PART_REGEXES:
                tabbed_videos = orderedSet(re.findall(p, webpage))
                if tabbed_videos:
                    return tabbed_videos, episode_id, upload_date, description

        if not video_id:
            page = self._download_webpage(url, 0)
            data = self._extract_video_data(page, 'video data', 0)
            info = data.get('video_obj')
            video_id = info.get('URI').replace('https://urs.pbs.org/redirect/', '').replace('/', '')
            display_id = data.get('video_id')

        return video_id, display_id, None, description, info

    def _extract_video_data(self, string, name, video_id, fatal=True):
        return self._parse_json(
            self._search_regex(
                [r'window\._PBS_KIDS_DEEPLINK\s*=\s*({.+?});'],
                string, name, default='{}'),
            video_id, transform_source=js_to_json, fatal=fatal)

    def _real_extract(self, url):
        video_id, display_id, upload_date, description, info = self._extract_webpage(url)

        if isinstance(video_id, list):
            entries = [self.url_result(
                'https://urs.pbs.org/redirect/%s/?format=json' % vid_id, 'PBSKIDS', vid_id)
                for vid_id in video_id]
            return self.playlist_result(entries, display_id)

        redirects = []
        redirects.append({"url": 'https://urs.pbs.org/redirect/%s/' % video_id, 'eeid': display_id})
        if upload_date is None:
            upload_date = unified_strdate(info.get('air_date'))

        formats = []
        http_url = None
        for num, redirect in enumerate(redirects):
            redirect_id = redirect.get('eeid')

            redirect_info = self._download_json(
                '%s?format=json' % redirect['url'], display_id,
                'Downloading %s video url info' % (redirect_id or num),
                headers=self.geo_verification_headers())

            if redirect_info['status'] == 'error':
                message = self._ERRORS.get(
                    redirect_info['http_code'], redirect_info['message'])
                if redirect_info['http_code'] == 403:
                    self.raise_geo_restricted(
                        msg=message, countries=self._GEO_COUNTRIES)
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, message), expected=True)

            format_url = redirect_info.get('url')
            if not format_url:
                continue

            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, display_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': redirect_id,
                })
                if re.search(r'^https?://.*(?:\d+k|baseline)', format_url):
                    http_url = format_url
        self._remove_duplicate_formats(formats)
        m3u8_formats = list(filter(
            lambda f: f.get('protocol') == 'm3u8' and f.get('vcodec') != 'none',
            formats))
        if http_url:
            for m3u8_format in m3u8_formats:
                bitrate = self._search_regex(r'(\d+)k', m3u8_format['url'], 'bitrate', default=None)
                # Lower qualities (150k and 192k) are not available as HTTP formats (see [1]),
                # we won't try extracting them.
                # Since summer 2016 higher quality formats (4500k and 6500k) are also available
                # albeit they are not documented in [2].
                # 1. https://github.com/ytdl-org/youtube-dl/commit/cbc032c8b70a038a69259378c92b4ba97b42d491#commitcomment-17313656
                # 2. https://projects.pbs.org/confluence/display/coveapi/COVE+Video+Specifications
                if not bitrate or int(bitrate) < 400:
                    continue
                f_url = re.sub(r'\d+k|baseline', bitrate + 'k', http_url)
                # This may produce invalid links sometimes (e.g.
                # http://www.pbs.org/wgbh/frontline/film/suicide-plan)
                if not self._is_valid_url(f_url, display_id, 'http-%sk video' % bitrate):
                    continue
                f = m3u8_format.copy()
                f.update({
                    'url': f_url,
                    'format_id': m3u8_format['format_id'].replace('hls', 'http'),
                    'protocol': 'http',
                })
                formats.append(f)
        self._sort_formats(formats)

        rating_str = info.get('rating')
        if rating_str is not None:
            rating_str = rating_str.rpartition('-')[2]
        age_limit = US_RATINGS.get(rating_str)

        subtitles = {}
        closed_captions_url = info.get('closed_captions')[0].get('URI').replace('\\', '')
        if closed_captions_url:
            subtitles['en'] = [{
                'ext': 'ttml',
                'url': closed_captions_url,
            }]
            mobj = re.search(r'/(\d+)_Encoded\.dfxp', closed_captions_url)
            if mobj:
                ttml_caption_suffix, ttml_caption_id = mobj.group(0, 1)
                ttml_caption_id = int(ttml_caption_id)
                subtitles['en'].extend([{
                    'url': closed_captions_url.replace(
                        ttml_caption_suffix, '/%d_Encoded.srt' % (ttml_caption_id + 1)),
                    'ext': 'srt',
                }, {
                    'url': closed_captions_url.replace(
                        ttml_caption_suffix, '/%d_Encoded.vtt' % (ttml_caption_id + 2)),
                    'ext': 'vtt',
                }])

        # info['title'] is often incomplete (e.g. 'Full Episode', 'Episode 5', etc)
        # Try turning it to 'program - title' naming scheme if possible
        alt_title = info.get('program', {}).get('title')
        if alt_title:
            info['title'] = alt_title + ' - ' + re.sub(r'^' + alt_title + r'[\s\-:]+', '', info['title'])

        description = info.get('description') or info.get(
            'program', {}).get('description') or description

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'description': description,
            'thumbnail': info.get('mezzanine'),
            'duration': int_or_none(info.get('duration')),
            'age_limit': age_limit,
            'upload_date': upload_date,
            'formats': formats,
            'subtitles': subtitles,
        }
