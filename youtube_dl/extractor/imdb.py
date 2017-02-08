from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    mimetype2ext,
    qualities,
    remove_end,
)


class ImdbIE(InfoExtractor):
    IE_NAME = 'imdb'
    IE_DESC = 'Internet Movie Database trailers'
    _VALID_URL = r'https?://(?:www|m)\.imdb\.com/(?:video/[^/]+/|title/tt\d+.*?#lb-|videoplayer/)vi(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.imdb.com/video/imdb/vi2524815897',
        'info_dict': {
            'id': '2524815897',
            'ext': 'mp4',
            'title': 'Ice Age: Continental Drift Trailer (No. 2)',
            'description': 'md5:9061c2219254e5d14e03c25c98e96a81',
        }
    }, {
        'url': 'http://www.imdb.com/video/_/vi2524815897',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/title/tt1667889/?ref_=ext_shr_eml_vi#lb-vi2524815897',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/title/tt1667889/#lb-vi2524815897',
        'only_matching': True,
    }, {
        'url': 'http://www.imdb.com/videoplayer/vi1562949145',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('http://www.imdb.com/video/imdb/vi%s' % video_id, video_id)
        descr = self._html_search_regex(
            r'(?s)<span itemprop="description">(.*?)</span>',
            webpage, 'description', fatal=False)
        player_url = 'http://www.imdb.com/video/imdb/vi%s/imdb/single' % video_id
        player_page = self._download_webpage(
            player_url, video_id, 'Downloading player page')
        # the player page contains the info for the default format, we have to
        # fetch other pages for the rest of the formats
        extra_formats = re.findall(r'href="(?P<url>%s.*?)".*?>(?P<name>.*?)<' % re.escape(player_url), player_page)
        format_pages = [
            self._download_webpage(
                f_url, video_id, 'Downloading info for %s format' % f_name)
            for f_url, f_name in extra_formats]
        format_pages.append(player_page)

        quality = qualities(('SD', '480p', '720p', '1080p'))
        formats = []
        for format_page in format_pages:
            json_data = self._search_regex(
                r'<script[^>]+class="imdb-player-data"[^>]*?>(.*?)</script>',
                format_page, 'json data', flags=re.DOTALL)
            info = self._parse_json(json_data, video_id, fatal=False)
            if not info:
                continue
            format_info = info.get('videoPlayerObject', {}).get('video', {})
            if not format_info:
                continue
            video_info_list = format_info.get('videoInfoList')
            if not video_info_list or not isinstance(video_info_list, list):
                continue
            video_info = video_info_list[0]
            if not video_info or not isinstance(video_info, dict):
                continue
            video_url = video_info.get('videoUrl')
            if not video_url:
                continue
            format_id = format_info.get('ffname')
            formats.append({
                'format_id': format_id,
                'url': video_url,
                'ext': mimetype2ext(video_info.get('videoMimeType')),
                'quality': quality(format_id),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': remove_end(self._og_search_title(webpage), ' - IMDb'),
            'formats': formats,
            'description': descr,
            'thumbnail': format_info.get('slate'),
        }


class ImdbListIE(InfoExtractor):
    IE_NAME = 'imdb:list'
    IE_DESC = 'Internet Movie Database lists'
    _VALID_URL = r'https?://(?:www\.)?imdb\.com/list/(?P<id>[\da-zA-Z_-]{11})'
    _TEST = {
        'url': 'http://www.imdb.com/list/JFs9NWw6XI0',
        'info_dict': {
            'id': 'JFs9NWw6XI0',
            'title': 'March 23, 2012 Releases',
        },
        'playlist_count': 7,
    }

    def _real_extract(self, url):
        list_id = self._match_id(url)
        webpage = self._download_webpage(url, list_id)
        entries = [
            self.url_result('http://www.imdb.com' + m, 'Imdb')
            for m in re.findall(r'href="(/video/imdb/vi[^"]+)"\s+data-type="playlist"', webpage)]

        list_title = self._html_search_regex(
            r'<h1 class="header">(.*?)</h1>', webpage, 'list title')

        return self.playlist_result(entries, list_id, list_title)
