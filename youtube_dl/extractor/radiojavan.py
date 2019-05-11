from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    parse_resolution,
    str_to_int,
    unified_strdate,
    urlencode_postdata,
    urljoin,
)


class RadioJavanIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?radiojavan\.com\/(?P<type>videos\/video|mp3s\/mp3|playlists\/playlist\/mp3|podcasts\/podcast)\/(?P<id>[^\/]+)\/?'
    _TESTS = [{
        'url': 'http://www.radiojavan.com/videos/video/chaartaar-ashoobam',
        'md5': 'e85208ffa3ca8b83534fca9fe19af95b',
        'info_dict': {
            'id': 'chaartaar-ashoobam',
            'ext': 'mp4',
            'title': 'Chaartaar - Ashoobam',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'upload_date': '20150215',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        }
    },
        {
        'url': 'https://www.radiojavan.com/podcasts/podcast/Mohsens-House-92',
        'md5': '6ccde3249f86ede1dcbde0a441a6dc91',
        'info_dict': {
            'upload_date': '20190421',
            'id': 'Mohsens-House-92',
            'title': "Mohsen's House Podcast (Episode 92)",
            'dislike_count': int,
            'like_count': int,
            'view_count': int,
            'ext': 'mp3',
            'thumbnail': r're:^https?://.*\.jpe?g$',
        }
    }, {
        'url': 'https://www.radiojavan.com/mp3s/mp3/Sirvan-Khosravi-Dorost-Nemisham',
        'md5': '3fe3d839617ab3d41348bd4f1af04e70',
        'info_dict': {
            'upload_date': '20190506',
            'dislike_count': int,
            'like_count': int,
            'view_count': int,
            'ext': 'mp3',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'title': 'Sirvan Khosravi - Dorost Nemisham',
            'id': 'Sirvan-Khosravi-Dorost-Nemisham'
        }
    }]

    def _real_extract(self, url):
        content_id = self._match_id(url)
        m = self._VALID_URL_RE.match(url)
        media_type = m.group('type')

        if media_type == "videos/video":
            return self.get_video_urls(url, content_id)
        elif media_type == "mp3s/mp3":
            return self.get_mp3_urls(url, content_id)
        elif media_type == "podcasts/podcast":
            return self.get_podcast_urls(url, content_id)
        elif media_type == "playlists/playlist/mp3":
            return self.get_playlist_urls(url, content_id)

    def get_download_host(self, url, host_url, content_id):
        download_host = self._download_json(
            host_url, content_id,
            data=urlencode_postdata({'id': content_id}),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url,
            }).get("host")
        return download_host

    def get_video_urls(self, url, content_id):
        download_host = self.get_download_host(url, 'https://www.radiojavan.com/videos/video_host', content_id)
        webpage = self._download_webpage(url, content_id)
        formats = []
        for format_id, _, media_path in re.findall(
                r'RJ\.video(?P<format_id>\d+[pPkK])\s*=\s*(["\'])(?P<url>(?:(?!\2).)+)\2',
                webpage):
            f = parse_resolution(format_id)
            f.update({
                'url': urljoin(download_host, media_path),
                'format_id': format_id,
            })
            formats.append(f)
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(self._search_regex(
            r'class="date_added">Date added: ([^<]+)<',
            webpage, 'upload date', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="views">Plays: ([\d,]+)',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) likes',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) dislikes',
            webpage, 'dislike count', fatal=False))

        url = {
            'id': content_id,
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }
        return url

    def get_mp3_urls(self, url, content_id):
        download_host = self.get_download_host(url, 'https://www.radiojavan.com/mp3s/mp3_host', content_id)
        webpage = self._download_webpage(url, content_id)
        formats = []
        for media_path in re.findall(
                r'RJ.currentMP3Url\s*=\s*[\"\'](?P<url>.+)[\"\'];',
                webpage):
            f = {
                'url': urljoin(download_host, "media/" + media_path + ".mp3"),
                'vcodec': 'none',
            }
            formats.append(f)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(self._search_regex(
            r'class="dateAdded">Date added: ([^<]+)<',
            webpage, 'upload date', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="views">Plays: ([\d,]+)',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) likes',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) dislikes',
            webpage, 'dislike count', fatal=False))

        url = {
            'id': content_id,
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }
        return url

    def get_playlist_urls(self, url, content_id):
        infopage = self._download_webpage("https://www.radiojavan.com/mp3s/playlist_start?id=" + content_id, content_id)
        urls = []
        mp3s = str(self._search_regex(
            r'RJ.relatedMP3\s*=\s*(?P<mp3s>\[.+\]);',
            infopage, 'mp3s', fatal=False))
        mp3s_info = json.loads(mp3s)
        for mp3_info in mp3s_info:
            url = self.get_mp3_urls("https://www.radiojavan.com/mp3s/mp3/" + mp3_info['next'], mp3_info['next'])
            urls.append(url)
        return urls

    def get_podcast_urls(self, url, content_id):
        download_host = self.get_download_host(url, 'https://www.radiojavan.com/podcasts/podcast_host', content_id)
        webpage = self._download_webpage(url, content_id)
        formats = []
        for media_path in re.findall(
                r'RJ.currentMP3Url\s*=\s*["\'](?P<url>.+)["\'];',
                webpage):
            f = {
                'url': urljoin(download_host, "media/" + media_path + ".mp3"),
                'vcodec': 'none',
            }
            formats.append(f)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(self._search_regex(
            r'class="dateAdded">Date added: ([^<]+)<',
            webpage, 'upload date', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="views">Plays: ([\d,]+)',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) likes',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) dislikes',
            webpage, 'dislike count', fatal=False))

        url = {
            'id': content_id,
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }
        return url
