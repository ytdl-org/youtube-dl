# coding: utf-8
from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from ..utils import int_or_none


class BoundHubIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?boundhub\.com/videos/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.boundhub.com/videos/205969/tamina-in-species-appropriate-cage-system-housing/',
        'md5': '6381e2491e6a42cc8e95c529b6da50a8',
        'info_dict': {
            'id': '205969',
            'title': 'Tamina in species-appropriate cage system housing',
            'description': 'Tamina in Straitjacket gagged an locked into a small cage for the afternoon.',
            'display_id': 'tamina-in-species-appropriate-cage-system-housing',
            'duration': 314,
            'ext': 'mp4',
            'thumbnail': 'https://cnt.boundhub.com/contents/videos_screenshots/205000/205969/preview.mp4.jpg',
            'uploader': 'Tamina',
            'uploader_id': 39278,
            'uploader_url': 'https://www.boundhub.com/members/39278/',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Parse duration
        duration_text = self._search_regex(r'<span>\s*Duration:\s*<em>([\w ]*)</em>', webpage, 'duration_text', fatal=False)
        minutes = self._html_search_regex(r'(\d*)min', duration_text, 'minutes', fatal=False)
        seconds = self._html_search_regex(r'(\d*)sec', duration_text, 'seconds', fatal=False)
        duration = (int(minutes) * 60) + int(seconds)

        # Parse views
        views_text = self._search_regex(r'<span>\s*Views:\s*<em>([\w ]*)</em>', webpage, 'views_text', fatal=False)
        views = int_or_none(views_text.replace(' ', ''))

        # Get uploader url and id
        uploader_url = self._search_regex(r'<div\s*class=[\"\']username[\"\']>\s*<a href=[\"\']([^\"\']*)[\"\']', webpage, 'uploader_url', fatal=False)
        uploader_id = self._html_search_regex(r'https?://(?:www\.)?boundhub\.com/members/(\d+)', uploader_url, 'uploader_id', fatal=False)
        uploader_id = int_or_none(uploader_id)

        # Get screenshots
        html_screenshots = self._search_regex(r'<div\s*class=[\"\']block-screenshots[\"\']>([\s\S]+?)</div>', webpage, 'html_screenshots', fatal=False)
        regex_screenshots = r'<a href=[\"\']([^\"\']*)[\"\']'

        thumbnails = list()

        for match in re.findall(regex_screenshots, html_screenshots):
            img = dict()
            img['url'] = match.rstrip('/')
            img['id'] = int_or_none(os.path.splitext(os.path.basename(img['url']))[0])
            thumbnails.append(img)

        return {
            'id': video_id,
            'title': self._search_regex(r'<div\s*class=[\"\']headline[\"\']>\s*<h2>(.*)</h2>', webpage, 'title', default=None) or self._og_search_title(webpage),
            'url': self._search_regex(r'video_url: [\"\']([^\"\']*)[\"\']', webpage, 'url'),
            'description': self._search_regex(r'<div\s*class=[\"\']item[\"\']>\s*Description:\s*<em>(.*)<\/em>', webpage, 'description', fatal=False),
            'display_id': self._html_search_regex(r'https?://(?:www\.)?boundhub\.com/videos/[0-9]+/([\w-]*)', url, 'display_id', fatal=False),
            'duration': duration,
            'ext': self._html_search_regex(r'postfix:\s*[\"\']\.([^\"\']*)[\"\']', webpage, 'ext', fatal=False),
            'thumbnail': self._html_search_regex(r'preview_url:\s*[\"\']([^\"\']*)[\"\']', webpage, 'thumbnail', fatal=False),
            'thumbnails': thumbnails,
            'uploader': self._search_regex(r'<div\s*class=[\"\']username[\"\']>\s*<a.*>\s*(.*)\s*</a>', webpage, 'uploader', fatal=False),
            'uploader_id': uploader_id,
            'uploader_url': uploader_url,
            'views': views,
        }
