# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class TumblrIE(InfoExtractor):
    _VALID_URL = r'http://(?P<blog_name>.*?)\.tumblr\.com/(?:post|video)/(?P<id>[0-9]+)(?:$|[/?#])'
    _TESTS = [{
        'url': 'http://tatianamaslanydaily.tumblr.com/post/54196191430/orphan-black-dvd-extra-behind-the-scenes',
        'md5': '479bb068e5b16462f5176a6828829767',
        'info_dict': {
            'id': '54196191430',
            'ext': 'mp4',
            'title': 'tatiana maslany news, Orphan Black || DVD extra - behind the scenes ↳...',
            'description': 'md5:37db8211e40b50c7c44e95da14f630b7',
            'thumbnail': 're:http://.*\.jpg',
        }
    }, {
        'url': 'http://5sostrum.tumblr.com/post/90208453769/yall-forgetting-the-greatest-keek-of-them-all',
        'md5': 'bf348ef8c0ef84fbf1cbd6fa6e000359',
        'info_dict': {
            'id': '90208453769',
            'ext': 'mp4',
            'title': '5SOS STRUM ;]',
            'description': 'md5:dba62ac8639482759c8eb10ce474586a',
            'thumbnail': 're:http://.*\.jpg',
        }
    }]

    def _real_extract(self, url):
        m_url = re.match(self._VALID_URL, url)
        video_id = m_url.group('id')
        blog = m_url.group('blog_name')

        url = 'http://%s.tumblr.com/post/%s/' % (blog, video_id)
        webpage = self._download_webpage(url, video_id)

        iframe_url = self._search_regex(
            r'src=\'(https?://www\.tumblr\.com/video/[^\']+)\'',
            webpage, 'iframe url')
        iframe = self._download_webpage(iframe_url, video_id)
        video_url = self._search_regex(r'<source src="([^"]+)"',
                                       iframe, 'video url')

        # The only place where you can get a title, it's not complete,
        # but searching in other places doesn't work for all videos
        video_title = self._html_search_regex(
            r'(?s)<title>(?P<title>.*?)(?: \| Tumblr)?</title>',
            webpage, 'title')

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': video_title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
