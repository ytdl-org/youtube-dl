# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import parse_iso8601


class CamdemyIE(InfoExtractor):
    _VALID_URL = r'http://www.camdemy.com/media/(?P<id>\d+).*'
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

        srcFrom = self._html_search_regex(
            r"<div class='srcFrom'>Source: <a title='([^']+)'", page,
            'external source', default=None)

        if srcFrom:
            return self.url_result(srcFrom)

        oembed_obj = self._download_json(
            'http://www.camdemy.com/oembed/?format=json&url=' + url, video_id)

        thumb_url = oembed_obj['thumbnail_url']
        video_folder = compat_urlparse.urljoin(thumb_url, 'video/')
        fileListXML = self._download_xml(
            compat_urlparse.urljoin(video_folder, 'fileList.xml'),
            video_id, 'Filelist XML')
        fileName = fileListXML.find('./video/item/fileName').text

        creation_time = self._html_search_regex(
            r"<div class='title'>Posted :</div>.*<div class='value'>([0-9:\- ]+)<",
            page, 'creation time', flags=re.MULTILINE | re.DOTALL) + '+08:00'
        creation_timestamp = parse_iso8601(creation_time, delimiter=' ')

        view_count_str = self._html_search_regex(
            r"<div class='title'>Views :</div>.*<div class='value'>([0-9,]+)<",
            page, 'view count', flags=re.MULTILINE | re.DOTALL)
        views = int(view_count_str.replace(',', ''))

        return {
            'id': video_id,
            'url': compat_urlparse.urljoin(video_folder, fileName),
            'title': oembed_obj['title'],
            'thumbnail': thumb_url,
            'description': self._html_search_meta('description', page),
            'creator': oembed_obj['author_name'],
            'duration': oembed_obj['duration'],
            'timestamp': creation_timestamp,
            'view_count': views,
        }
