# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import RegexNotFoundError

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
    }, {
        'url': 'http://larastonesbitch.tumblr.com/post/130035771559/honestlyiconic',
        'md5': 'f0c88985bd7e85d13603771a8647f270',
        'resolution': 'hd',
        'info_dict': {
            'id': '130035771559',
            'ext': 'mp4',
            'title': 'larastonesbitch',
            'description': 'md5:d9184c8b9396bb5b027b3d8658a43de0',
            'thumbnail': 're:http://.*\.jpg',
        },
        'params': {
            'format': 'sd',
        },
    }, {
        'url': 'http://larastonesbitch.tumblr.com/post/130035771559/honestlyiconic',
        'md5': 'a88dea4c03a9cc208cf44eb2dd12248b',
        'resolution': 'hd',
        'info_dict': {
            'id': '130035771559',
            'ext': 'mp4',
            'title': 'larastonesbitch',
            'description': 'md5:d9184c8b9396bb5b027b3d8658a43de0',
            'thumbnail': 're:http://.*\.jpg',
        },
        'params': {
            'format': 'hd',
        },
    }, {
        'url': 'http://naked-yogi.tumblr.com/post/118312946248/naked-smoking-stretching',
        'md5': 'de07e5211d60d4f3a2c3df757ea9f6ab',
        'info_dict': {
            'id': 'Wmur',
            'ext': 'mp4',
            'title': 'naked smoking & stretching',
            'upload_date': '20150506',
            'timestamp': 1430931613,
        },
        'add_ie': ['Vidme'],
    }, {
        'url': 'http://camdamage.tumblr.com/post/98846056295/',
        'md5': 'a9e0c8371ea1ca306d6554e3fecf50b6',
        'info_dict': {
            'id': '105463834',
            'ext': 'mp4',
            'title': 'Cam Damage-HD 720p',
            'uploader': 'John Moyer',
            'uploader_id': 'user32021558',
        },
        'add_ie': ['Vimeo'],
    }]

    def _real_extract(self, url):
        m_url = re.match(self._VALID_URL, url)
        video_id = m_url.group('id')
        blog = m_url.group('blog_name')

        video_urls = []

        url = 'http://%s.tumblr.com/post/%s/' % (blog, video_id)
        webpage, urlh = self._download_webpage_handle(url, video_id)

        iframe_url = self._search_regex(
            r'src=\'(https?://www\.tumblr\.com/video/[^\']+)\'',
            webpage, 'iframe url', default=None)
        if iframe_url is None:
            return self.url_result(urlh.geturl(), 'Generic')

        iframe = self._download_webpage(iframe_url, video_id,
                                        'Downloading iframe page')

        sd_video_url = self._search_regex(r'<source src="([^"]+)"',
                                          iframe, 'sd video url')
        format_id = sd_video_url.split("/")[-1] + 'p'
        if len(format_id) != 4:
            format_id = "480p"
        video_urls.append({
            'ext': 'mp4',
            'format_id': 'sd',
            'url': sd_video_url,
            'resolution': format_id,
        })

        try:
            hd_video_url = self._search_regex(r'hdUrl":"([^"]+)"',
                                              iframe, 'hd video url')
            hd_video_url = hd_video_url.replace("\\", "")
            format_id = hd_video_url.split("/")[-1] + 'p'
            if len(format_id) != 4:
                format_id = "720p"
            video_urls.append({
                'ext': 'mp4',
                'format_id': 'hd',
                'url': hd_video_url,
                'resolution': format_id,
            })
        except RegexNotFoundError:
            # Not all videos will have HD versions
            pass

        # The only place where you can get a title, it's not complete,
        # but searching in other places doesn't work for all videos
        video_title = self._html_search_regex(
            r'(?s)<title>(?P<title>.*?)(?: \| Tumblr)?</title>',
            webpage, 'title')

        return {
            'id': video_id,
            'formats': video_urls,
            'ext': 'mp4',
            'title': video_title,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
        }
