# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor


class VierIE(InfoExtractor):
    IE_NAME = 'vier'
    _VALID_URL = r'https?://(?:www\.)?vier\.be/(?:[^/]+/videos/(?P<display_id>[^/]+)(?:/(?P<id>\d+))?|video/v3/embed/(?P<embed_id>\d+))'
    _TESTS = [{
        'url': 'http://www.vier.be/planb/videos/het-wordt-warm-de-moestuin/16129',
        'info_dict': {
            'id': '16129',
            'display_id': 'het-wordt-warm-de-moestuin',
            'ext': 'mp4',
            'title': 'Het wordt warm in De Moestuin',
            'description': 'De vele uren werk eisen hun tol. Wim droomt van assistentie...',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.vier.be/planb/videos/mieren-herders-van-de-bladluizen',
        'only_matching': True,
    }, {
        'url': 'http://www.vier.be/video/v3/embed/16129',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        embed_id = mobj.group('embed_id')
        display_id = mobj.group('display_id') or embed_id

        webpage = self._download_webpage(url, display_id)

        video_id = self._search_regex(
            [r'data-nid="(\d+)"', r'"nid"\s*:\s*"(\d+)"'],
            webpage, 'video id')
        application = self._search_regex(
            [r'data-application="([^"]+)"', r'"application"\s*:\s*"([^"]+)"'],
            webpage, 'application', default='vier_vod')
        filename = self._search_regex(
            [r'data-filename="([^"]+)"', r'"filename"\s*:\s*"([^"]+)"'],
            webpage, 'filename')

        playlist_url = 'http://vod.streamcloud.be/%s/_definst_/mp4:%s.mp4/playlist.m3u8' % (application, filename)
        formats = self._extract_wowza_formats(playlist_url, display_id, skip_protocols=['dash'])
        self._sort_formats(formats)

        title = self._og_search_title(webpage, default=display_id)
        description = self._og_search_description(webpage, default=None)
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class VierVideosIE(InfoExtractor):
    IE_NAME = 'vier:videos'
    _VALID_URL = r'https?://(?:www\.)?vier\.be/(?P<program>[^/]+)/videos(?:\?.*\bpage=(?P<page>\d+)|$)'
    _TESTS = [{
        'url': 'http://www.vier.be/demoestuin/videos',
        'info_dict': {
            'id': 'demoestuin',
        },
        'playlist_mincount': 153,
    }, {
        'url': 'http://www.vier.be/demoestuin/videos?page=6',
        'info_dict': {
            'id': 'demoestuin-page6',
        },
        'playlist_mincount': 20,
    }, {
        'url': 'http://www.vier.be/demoestuin/videos?page=7',
        'info_dict': {
            'id': 'demoestuin-page7',
        },
        'playlist_mincount': 13,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        program = mobj.group('program')

        page_id = mobj.group('page')
        if page_id:
            page_id = int(page_id)
            start_page = page_id
            playlist_id = '%s-page%d' % (program, page_id)
        else:
            start_page = 0
            playlist_id = program

        entries = []
        for current_page_id in itertools.count(start_page):
            current_page = self._download_webpage(
                'http://www.vier.be/%s/videos?page=%d' % (program, current_page_id),
                program,
                'Downloading page %d' % (current_page_id + 1))
            page_entries = [
                self.url_result('http://www.vier.be' + video_url, 'Vier')
                for video_url in re.findall(
                    r'<h3><a href="(/[^/]+/videos/[^/]+(?:/\d+)?)">', current_page)]
            entries.extend(page_entries)
            if page_id or '>Meer<' not in current_page:
                break

        return self.playlist_result(entries, playlist_id)
