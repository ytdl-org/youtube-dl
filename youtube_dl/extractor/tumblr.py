# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TumblrIE(InfoExtractor):
    _VALID_URL = r'http://(?P<blog_name>.*?)\.tumblr\.com/((post)|(video))/(?P<id>\d*)($|/)'
    _TESTS = [
        {
        'url': 'http://tatianamaslanydaily.tumblr.com/post/54196191430/orphan-black-dvd-extra-behind-the-scenes',
        'md5': '479bb068e5b16462f5176a6828829767',
        'info_dict': {
            'id': '54196191430',
            'ext': 'mp4',
            'title': 'tatiana maslany news, Orphan Black || DVD extra - behind the scenes ↳...',
            'description': 'md5:dfac39636969fe6bf1caa2d50405f069',
            'thumbnail': 're:http://.*\.jpg',
        }
    }, {
        'url': 'http://5sostrum.tumblr.com/post/90208453769/yall-forgetting-the-greatest-keek-of-them-all',
        'md5': 'bf348ef8c0ef84fbf1cbd6fa6e000359',
        'info_dict': {
            'id': '90208453769',
            'ext': 'mp4',
            'title': '5SOS STRUM ;)',
            'description': 'md5:dba62ac8639482759c8eb10ce474586a',
            'thumbnail': 're:http://.*\.jpg',
        }
    }, {
        'url': 'http://anotherkindofhorse.tumblr.com/post/96805380497',
        'md5': '84a5c3c1cb2325a9a9e900d1726e956a',
        'info_dict': {
            'id': '96805380497',
            'ext': 'mp4',
            'title': 'Tumblr',
            'description': 'md5:06e250cb873c721abee97e543f9997d3',
            'thumbnail': 're:http://.*\.jpg',
        }
    }
    ]

    def _real_extract(self, url):
        m_url = re.match(self._VALID_URL, url)
        video_id = m_url.group('id')
        blog = m_url.group('blog_name')

        video_thumbnails = []

        # try "old" way first
        purl = 'http://%s.tumblr.com/post/%s/' % (blog, video_id)
        webpage = self._download_webpage(purl, video_id)

        re_video = r'src=\\x22(?P<video_url>http://%s\.tumblr\.com/video_file/%s/(.*?))\\x22 type=\\x22video/(?P<ext>.*?)\\x22' % (blog, video_id)
        video = re.search(re_video, webpage)

        video_thumbnail = self._search_regex(
            r'posters.*?\[\\x22(.*?)\\x22',
            webpage, 'thumbnail', default="", fatal=False)  # We pick the first poster

        if video_thumbnail:
            video_thumbnail = video_thumbnail.replace('\\\\/', '/')

        if video is None:
            # This did not work - search for iframe
            iframe_m = re.search(r'<div class="videoWrapper">.+?<iframe src="(.+?)"',webpage,re.S)
            if iframe_m is not None:
                iframe_url = iframe_m.group(1)
                webpage = self._download_webpage(iframe_url, video_id)
                video = re.search(r'source src="(?P<video_url>.+?/video_file/.+?)" type="video/(?P<ext>.+?)"', webpage)

                thumbs_match = re.search(r'posters.*?\[(.+?)]', webpage)
                if thumbs_match is not None:
                    thumbs = [ w[1:-1].replace(r'\/',r'/') for w in thumbs_match.group(1).split(',') ]
                    if len(thumbs) > 0:
                        video_thumbnail = thumbs[0]
                    video_thumbnails = [ {"url": ele} for ele in thumbs ]

        if video is None:
            raise ExtractorError('Unable to extract video')

        video_url = video.group('video_url')
        ext = video.group('ext')

        # The only place where you can get a title, it's not complete,
        # but searching in other places doesn't work for all videos
        video_title = self._html_search_regex(r'<title>(?P<title>.*?)(?: \| Tumblr)?</title>',
            webpage, 'title', flags=re.DOTALL)

        return [{'id': video_id,
                 'url': video_url,
                 'title': video_title,
                 'description': self._html_search_meta('description', webpage),
                 'thumbnail': video_thumbnail,
                 'thumbnails': video_thumbnails,
                 'ext': ext
                 }]
