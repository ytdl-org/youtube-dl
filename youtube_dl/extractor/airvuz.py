# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class AirVuzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?airvuz\.com/video/(?P<display_id>.+)\?id=(?P<id>.+)'
    _TEST = {
        'url': 'https://www.airvuz.com/video/An-Imaginary-World?id=599e85c49282a717c50f2f7a',
        'info_dict': {
            'id': '599e85c49282a717c50f2f7a',
            'display_id': 'An-Imaginary-World',
            'title': 'md5:7fc56270e7a70fa81a5935b72eacbe29',
            'ext': 'mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        groups = re.match(self._VALID_URL, url)
        video_id = groups.group('id')
        display_id = groups.group('display_id')

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage)
        uploader = self._html_search_regex(r'class=(?:\'img-circle\'|"img-circle"|img-circle)[^>]+?alt=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'uploader', fatal=False) or self._html_search_regex(r'https?://(?:www\.)?airvuz\.com/user/([^>]*)', webpage, 'uploader', fatal=False)

        formats = []

        meta = self._download_json('https://www.airvuz.com/api/videos/%s?type=dynamic' % video_id, video_id, fatal=False)
        if meta:
            info_res = meta.get('data')

            for res in reversed(info_res.get('resolutions')):
                video_url = res.get('src')
                if not video_url:
                    continue
                # URL is a relative path
                video_url = 'https://www.airvuz.com/%s' % video_url

                formats.append({
                    'url': video_url,
                    'format_id': res.get('label'),
                    'height': res.get('res')
                })
        else:
            self.report_extraction(video_id)

            video_url = self._html_search_regex(r'<meta[^>]+?(?:name|property)=(?:\'og:video:url\'|"og:video:url"|og:video:url)[^>]+?content=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'video_url')

            if video_url:
                format_id = video_url.split("-")[-1].split(".")[0]
                if len(format_id) <= 2:
                    format_id = None

                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'description': description,
            'uploader': uploader,
        }
