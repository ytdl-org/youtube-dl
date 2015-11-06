# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    strip_jsonp,
    unified_strdate,
    US_RATINGS,
)


class PBSIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:
           # Direct video URL
           video\.pbs\.org/(?:viralplayer|video)/(?P<id>[0-9]+)/? |
           # Article with embedded player (or direct video)
           (?:www\.)?pbs\.org/(?:[^/]+/){2,5}(?P<presumptive_id>[^/]+?)(?:\.html)?/?(?:$|[?\#]) |
           # Player
           video\.pbs\.org/(?:widget/)?partnerplayer/(?P<player_id>[^/]+)/
        )
    '''

    _TESTS = [
        {
            'url': 'http://www.pbs.org/tpt/constitution-usa-peter-sagal/watch/a-more-perfect-union/',
            'md5': 'ce1888486f0908d555a8093cac9a7362',
            'info_dict': {
                'id': '2365006249',
                'ext': 'mp4',
                'title': 'Constitution USA with Peter Sagal - A More Perfect Union',
                'description': 'md5:ba0c207295339c8d6eced00b7c363c6a',
                'duration': 3190,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://www.pbs.org/wgbh/pages/frontline/losing-iraq/',
            'md5': '143c98aa54a346738a3d78f54c925321',
            'info_dict': {
                'id': '2365297690',
                'ext': 'mp4',
                'title': 'FRONTLINE - Losing Iraq',
                'description': 'md5:f5bfbefadf421e8bb8647602011caf8e',
                'duration': 5050,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            }
        },
        {
            'url': 'http://www.pbs.org/newshour/bb/education-jan-june12-cyberschools_02-23/',
            'md5': 'b19856d7f5351b17a5ab1dc6a64be633',
            'info_dict': {
                'id': '2201174722',
                'ext': 'mp4',
                'title': 'PBS NewsHour - Cyber Schools Gain Popularity, but Quality Questions Persist',
                'description': 'md5:5871c15cba347c1b3d28ac47a73c7c28',
                'duration': 801,
            },
        },
        {
            'url': 'http://www.pbs.org/wnet/gperf/dudamel-conducts-verdi-requiem-hollywood-bowl-full-episode/3374/',
            'md5': 'c62859342be2a0358d6c9eb306595978',
            'info_dict': {
                'id': '2365297708',
                'ext': 'mp4',
                'description': 'md5:68d87ef760660eb564455eb30ca464fe',
                'title': 'Great Performances - Dudamel Conducts Verdi Requiem at the Hollywood Bowl - Full',
                'duration': 6559,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://www.pbs.org/wgbh/nova/earth/killer-typhoon.html',
            'md5': '908f3e5473a693b266b84e25e1cf9703',
            'info_dict': {
                'id': '2365160389',
                'display_id': 'killer-typhoon',
                'ext': 'mp4',
                'description': 'md5:c741d14e979fc53228c575894094f157',
                'title': 'NOVA - Killer Typhoon',
                'duration': 3172,
                'thumbnail': 're:^https?://.*\.jpg$',
                'upload_date': '20140122',
                'age_limit': 10,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://www.pbs.org/wgbh/pages/frontline/united-states-of-secrets/',
            'info_dict': {
                'id': 'united-states-of-secrets',
            },
            'playlist_count': 2,
        },
        {
            'url': 'http://www.pbs.org/wgbh/americanexperience/films/death/player/',
            'info_dict': {
                'id': '2276541483',
                'display_id': 'player',
                'ext': 'mp4',
                'title': 'American Experience - Death and the Civil War, Chapter 1',
                'description': 'American Experience, TV’s most-watched history series, brings to life the compelling stories from our past that inform our understanding of the world today.',
                'duration': 682,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://video.pbs.org/video/2365367186/',
            'info_dict': {
                'id': '2365367186',
                'display_id': '2365367186',
                'ext': 'mp4',
                'title': 'To Catch A Comet - Full Episode',
                'description': 'On November 12, 2014, billions of kilometers from Earth, spacecraft orbiter Rosetta and lander Philae did what no other had dared to attempt \u2014 land on the volatile surface of a comet as it zooms around the sun at 67,000 km/hr. The European Space Agency hopes this mission can help peer into our past and unlock secrets of our origins.',
                'duration': 3342,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
            'skip': 'Expired',
        },
        {
            # Video embedded in iframe containing angle brackets as attribute's value (e.g.
            # "<iframe style='position: absolute;<br />\ntop: 0; left: 0;' ...", see
            # https://github.com/rg3/youtube-dl/issues/7059)
            'url': 'http://www.pbs.org/food/features/a-chefs-life-season-3-episode-5-prickly-business/',
            'info_dict': {
                'id': '2365546844',
                'display_id': 'a-chefs-life-season-3-episode-5-prickly-business',
                'ext': 'mp4',
                'title': "A Chef's Life - Season 3, Ep. 5: Prickly Business",
                'description': 'md5:61db2ddf27c9912f09c241014b118ed1',
                'duration': 1480,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            # Frontline video embedded via flp2012.js
            'url': 'http://www.pbs.org/wgbh/pages/frontline/the-atomic-artists',
            'info_dict': {
                'id': '2070868960',
                'display_id': 'the-atomic-artists',
                'ext': 'mp4',
                'title': 'FRONTLINE - The Atomic Artists',
                'description': 'md5:f5bfbefadf421e8bb8647602011caf8e',
                'duration': 723,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        }
    ]
    _ERRORS = {
        101: 'We\'re sorry, but this video is not yet available.',
        403: 'We\'re sorry, but this video is not available in your region due to right restrictions.',
        404: 'We are experiencing technical difficulties that are preventing us from playing the video at this time. Please check back again soon.',
        410: 'This video has expired and is no longer available for online streaming.',
    }

    def _extract_webpage(self, url):
        mobj = re.match(self._VALID_URL, url)

        presumptive_id = mobj.group('presumptive_id')
        display_id = presumptive_id
        if presumptive_id:
            webpage = self._download_webpage(url, display_id)

            upload_date = unified_strdate(self._search_regex(
                r'<input type="hidden" id="air_date_[0-9]+" value="([^"]+)"',
                webpage, 'upload date', default=None))

            # tabbed frontline videos
            tabbed_videos = re.findall(
                r'<div[^>]+class="videotab[^"]*"[^>]+vid="(\d+)"', webpage)
            if tabbed_videos:
                return tabbed_videos, presumptive_id, upload_date

            MEDIA_ID_REGEXES = [
                r"div\s*:\s*'videoembed'\s*,\s*mediaid\s*:\s*'(\d+)'",  # frontline video embed
                r'class="coveplayerid">([^<]+)<',                       # coveplayer
                r'<input type="hidden" id="pbs_video_id_[0-9]+" value="([0-9]+)"/>',  # jwplayer
            ]

            media_id = self._search_regex(
                MEDIA_ID_REGEXES, webpage, 'media ID', fatal=False, default=None)
            if media_id:
                return media_id, presumptive_id, upload_date

            # Fronline video embedded via flp
            video_id = self._search_regex(
                r'videoid\s*:\s*"([\d+a-z]{7,})"', webpage, 'videoid', default=None)
            if video_id:
                # pkg_id calculation is reverse engineered from
                # http://www.pbs.org/wgbh/pages/frontline/js/flp2012.js
                prg_id = self._search_regex(
                    r'videoid\s*:\s*"([\d+a-z]{7,})"', webpage, 'videoid')[7:]
                if 'q' in prg_id:
                    prg_id = prg_id.split('q')[1]
                prg_id = int(prg_id, 16)
                getdir = self._download_json(
                    'http://www.pbs.org/wgbh/pages/frontline/.json/getdir/getdir%d.json' % prg_id,
                    presumptive_id, 'Downloading getdir JSON',
                    transform_source=strip_jsonp)
                return getdir['mid'], presumptive_id, upload_date

            for iframe in re.findall(r'(?s)<iframe(.+?)></iframe>', webpage):
                url = self._search_regex(
                    r'src=(["\'])(?P<url>.+?partnerplayer.+?)\1', iframe,
                    'player URL', default=None, group='url')
                if url:
                    break

            mobj = re.match(self._VALID_URL, url)

        player_id = mobj.group('player_id')
        if not display_id:
            display_id = player_id
        if player_id:
            player_page = self._download_webpage(
                url, display_id, note='Downloading player page',
                errnote='Could not download player page')
            video_id = self._search_regex(
                r'<div\s+id="video_([0-9]+)"', player_page, 'video ID')
        else:
            video_id = mobj.group('id')
            display_id = video_id

        return video_id, display_id, None

    def _real_extract(self, url):
        video_id, display_id, upload_date = self._extract_webpage(url)

        if isinstance(video_id, list):
            entries = [self.url_result(
                'http://video.pbs.org/video/%s' % vid_id, 'PBS', vid_id)
                for vid_id in video_id]
            return self.playlist_result(entries, display_id)

        info = self._download_json(
            'http://video.pbs.org/videoInfo/%s?format=json&type=partner' % video_id,
            display_id)

        formats = []
        for encoding_name in ('recommended_encoding', 'alternate_encoding'):
            redirect = info.get(encoding_name)
            if not redirect:
                continue
            redirect_url = redirect.get('url')
            if not redirect_url:
                continue

            redirect_info = self._download_json(
                redirect_url + '?format=json', display_id,
                'Downloading %s video url info' % encoding_name)

            if redirect_info['status'] == 'error':
                raise ExtractorError(
                    '%s said: %s' % (
                        self.IE_NAME,
                        self._ERRORS.get(redirect_info['http_code'], redirect_info['message'])),
                    expected=True)

            format_url = redirect_info.get('url')
            if not format_url:
                continue

            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, display_id, 'mp4', preference=1, m3u8_id='hls'))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': redirect.get('eeid'),
                })
        self._sort_formats(formats)

        rating_str = info.get('rating')
        if rating_str is not None:
            rating_str = rating_str.rpartition('-')[2]
        age_limit = US_RATINGS.get(rating_str)

        subtitles = {}
        closed_captions_url = info.get('closed_captions_url')
        if closed_captions_url:
            subtitles['en'] = [{
                'ext': 'ttml',
                'url': closed_captions_url,
            }]

        # info['title'] is often incomplete (e.g. 'Full Episode', 'Episode 5', etc)
        # Try turning it to 'program - title' naming scheme if possible
        alt_title = info.get('program', {}).get('title')
        if alt_title:
            info['title'] = alt_title + ' - ' + re.sub(r'^' + alt_title + '[\s\-:]+', '', info['title'])

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'description': info['program'].get('description'),
            'thumbnail': info.get('image_url'),
            'duration': int_or_none(info.get('duration')),
            'age_limit': age_limit,
            'upload_date': upload_date,
            'formats': formats,
            'subtitles': subtitles,
        }
