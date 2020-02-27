# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote

import re


class AirVuzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?airvuz\.com/video/(?P<display_id>.+)\?id=(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://www.airvuz.com/video/An-Imaginary-World?id=599e85c49282a717c50f2f7a',
            'info_dict': {
                'id': '599e85c49282a717c50f2f7a',
                'display_id': 'An-Imaginary-World',
                'title': 'An Imaginary World',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg',
                'uploader': 'Tobias Hägg',
                'description': 'md5:176b43a79a0a19d592c0261d9c0a48c7',
            }
        },
        # Emojis in the URL, title and description
        {
            'url': 'https://www.airvuz.com/video/Cinematic-FPV-Flying-at-a-Cove-%F0%9F%8C%8A%F0%9F%8C%8A%F0%9F%8C%8A-The-rocks-waves-and-seaweed%F0%9F%98%8D?id=5d3db133ec63bf7e65c2226e',
            'info_dict': {
                'id': '5d3db133ec63bf7e65c2226e',
                'display_id': 'Cinematic-FPV-Flying-at-a-Cove-🌊🌊🌊-The-rocks-waves-and-seaweed😍',
                'title': 'Cinematic FPV Flying at a Cove! 🌊🌊🌊 The rocks, waves, and seaweed😍!',
                'ext': 'mp4',
                'thumbnail': r're:^https?://.*\.jpg',
                'uploader': 'Mako Reactra',
                'description': 'md5:ac91310ff7c2de26a0f1e8e8caae2ee6'
            },
        },
    ]

    def _real_extract(self, url):
        groups = re.match(self._VALID_URL, url)
        video_id = groups.group('id')
        display_id = compat_urllib_parse_unquote(groups.group('display_id'))

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
                })
        else:
            self.report_extraction(video_id)

            video_url = self._html_search_regex(r'<meta[^>]+?(?:name|property)=(?:\'og:video:url\'|"og:video:url"|og:video:url)[^>]+?content=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'video_url')

            if video_url:
                format_id = video_url.split("-")[-1].split(".")[0]
                if len(format_id) <= 2:
                    # Format can't be induced from the filename
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
