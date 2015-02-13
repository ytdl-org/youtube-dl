# coding: utf-8
from __future__ import unicode_literals

import datetime
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
)
from ..utils import (
    parse_iso8601,
    str_to_int,
)


class CamdemyIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?camdemy\.com/media/(?P<id>\d+)'
    _TESTS = [{
        # single file
        'url': 'http://www.camdemy.com/media/5181/',
        'md5': '5a5562b6a98b37873119102e052e311b',
        'info_dict': {
            'id': '5181',
            'ext': 'mp4',
            'title': 'Ch1-1 Introduction, Signals (02-23-2012)',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': '',
            'creator': 'ss11spring',
            'upload_date': '20130114',
            'timestamp': 1358154556,
            'view_count': int,
        }
    }, {
        # With non-empty description
        'url': 'http://www.camdemy.com/media/13885',
        'md5': '4576a3bb2581f86c61044822adbd1249',
        'info_dict': {
            'id': '13885',
            'ext': 'mp4',
            'title': 'EverCam + Camdemy QuickStart',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'md5:050b62f71ed62928f8a35f1a41e186c9',
            'creator': 'evercam',
            'upload_date': '20140620',
            'timestamp': 1403271569,
        }
    }, {
        # External source
        'url': 'http://www.camdemy.com/media/14842',
        'md5': '50e1c3c3aa233d3d7b7daa2fa10b1cf7',
        'info_dict': {
            'id': '2vsYQzNIsJo',
            'ext': 'mp4',
            'upload_date': '20130211',
            'uploader': 'Hun Kim',
            'description': 'Excel 2013 Tutorial for Beginners - How to add Password Protection',
            'uploader_id': 'hunkimtutorials',
            'title': 'Excel 2013 Tutorial - How to add Password Protection',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        page = self._download_webpage(url, video_id)

        src_from = self._html_search_regex(
            r"<div class='srcFrom'>Source: <a title='([^']+)'", page,
            'external source', default=None)
        if src_from:
            return self.url_result(src_from)

        oembed_obj = self._download_json(
            'http://www.camdemy.com/oembed/?format=json&url=' + url, video_id)

        thumb_url = oembed_obj['thumbnail_url']
        video_folder = compat_urlparse.urljoin(thumb_url, 'video/')
        file_list_doc = self._download_xml(
            compat_urlparse.urljoin(video_folder, 'fileList.xml'),
            video_id, 'Filelist XML')
        file_name = file_list_doc.find('./video/item/fileName').text
        video_url = compat_urlparse.urljoin(video_folder, file_name)

        timestamp = parse_iso8601(self._html_search_regex(
            r"<div class='title'>Posted\s*:</div>\s*<div class='value'>([^<>]+)<",
            page, 'creation time', fatal=False),
            delimiter=' ', timezone=datetime.timedelta(hours=8))
        view_count = str_to_int(self._html_search_regex(
            r"<div class='title'>Views\s*:</div>\s*<div class='value'>([^<>]+)<",
            page, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': oembed_obj['title'],
            'thumbnail': thumb_url,
            'description': self._html_search_meta('description', page),
            'creator': oembed_obj['author_name'],
            'duration': oembed_obj['duration'],
            'timestamp': timestamp,
            'view_count': view_count,
        }


class CamdemyFolderIE(InfoExtractor):
    _VALID_URL = r'http://www.camdemy.com/folder/(?P<id>\d+)'
    _TESTS = [{
        # links with trailing slash
        'url': 'http://www.camdemy.com/folder/450',
        'info_dict': {
            'id': '450',
            'title': '信號與系統 2012 & 2011 (Signals and Systems)',
        },
        'playlist_mincount': 145
    }, {
        # links without trailing slash
        # and multi-page
        'url': 'http://www.camdemy.com/folder/853',
        'info_dict': {
            'id': '853',
            'title': '科學計算 - 使用 Matlab'
        },
        'playlist_mincount': 20
    }, {
        # with displayMode parameter. For testing the codes to add parameters
        'url': 'http://www.camdemy.com/folder/853/?displayMode=defaultOrderByOrg',
        'info_dict': {
            'id': '853',
            'title': '科學計算 - 使用 Matlab'
        },
        'playlist_mincount': 20
    }]

    def _real_extract(self, url):
        folder_id = self._match_id(url)

        # Add displayMode=list so that all links are displayed in a single page
        parsed_url = list(compat_urlparse.urlparse(url))
        query = dict(compat_urlparse.parse_qsl(parsed_url[4]))
        query.update({'displayMode': 'list'})
        parsed_url[4] = compat_urllib_parse.urlencode(query)
        final_url = compat_urlparse.urlunparse(parsed_url)

        page = self._download_webpage(final_url, folder_id)
        matches = re.findall(r"href='(/media/\d+/?)'", page)

        entries = [self.url_result('http://www.camdemy.com' + media_path)
                   for media_path in matches]

        folder_title = self._html_search_meta('keywords', page)

        return self.playlist_result(entries, folder_id, folder_title)
