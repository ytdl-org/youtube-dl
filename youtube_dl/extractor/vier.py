# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urllib_parse,
)


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

        playlist_url = 'http://vod.streamcloud.be/%s/mp4:_definst_/%s.mp4/playlist.m3u8' % (application, filename)
        formats = self._extract_m3u8_formats(playlist_url, display_id, 'mp4')

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

    def extract_videos(self, webpage, page_id):
        entries = [
            self.url_result('http://www.vier.be%s' % video_url, 'Vier')
            for video_url in re.findall(
                r'<h3><a href="(/[^/]+/videos/[^/]+(?:/\d+)?)">', webpage)]
        return entries

    def extract_next_page_id(self, webpage):
        return self._html_search_regex(r'<a\s+href="(?:/[^/]+)+\?page=(\d+)">Meer</a>', webpage, 'page_id', None, False)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        program = mobj.group('program')
        page_id = mobj.group('page')

        webpage = self._download_webpage(url, program)

        views = self._parse_json(
            self._search_regex(
                'jQuery.extend\(\s*Drupal.settings\s*,\s*({.*})\);',
                webpage, 'Drupal.settings'),
                page_id
            ).get('views')
        ajax_path = views.get('ajax_path')
        ajaxViews = views.get('ajaxViews')
        ajaxView = ajaxViews.get(list(ajaxViews)[0])

        entries = self.extract_videos(webpage, program)
        if page_id:
            playlist_id = '%s-page%s' % (program, page_id)
        else:
            playlist_id = program
            page_id = self.extract_next_page_id(webpage)
            while page_id:
                ajaxView['page'] = page_id
                request = compat_urllib_request.Request(
                    'http://www.vier.be%s' % ajax_path,
                    compat_urllib_parse.urlencode(ajaxView),
                    {'Content-Type': 'application/x-www-form-urlencoded'}
                )
                json_data = self._download_json(
                    request,
                    program,
                    'Downloading page %s' % (page_id))
                data = json_data[1].get('data')
                entries.extend(self.extract_videos(data, page_id))
                page_id = self.extract_next_page_id(data)

        return self.playlist_result(entries, playlist_id)
