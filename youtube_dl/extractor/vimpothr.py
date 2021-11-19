# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    get_element_by_class,
    urljoin
)


class VimpOTHRVideoIE(InfoExtractor):
    _VALID_URL = r'https?://vimp\.oth-regensburg\.de/video/(?P<title>[a-zA-Z0-9_-]+)/(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'https://vimp.oth-regensburg.de/video/VE2-Vorlesungsaufzeichnung-von-Fr-5November/ca47954b51baa0f0fb1481cc4df0558a',
        'md5': 'eabb43c7bcc884773b0b0d2e37ebae87',
        'info_dict': {
            'id': 'ca47954b51baa0f0fb1481cc4df0558a',
            'ext': 'mp4',
            'title': 'VE2-Vorlesungsaufzeichnung von Fr. 5.November',
            'description': 'Invarianzsatz, Rentenbarwerte',
            'thumbnail': 'https://vimp.oth-regensburg.de/cache/b56c79d598c594b117d769dc1731ed6a.jpg',
            'uploader_id': 'frm39711',
            'uploader_url': 'https://vimp.oth-regensburg.de/user/view/user/frm39711/uid/778'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        video_url = self._og_search_video_url(webpage)

        uploader_element = get_element_by_class('uploader', webpage)
        uploader_id = self._search_regex(r'alt="(?P<uploader_id>[a-z]{3}\d{5})"', uploader_element, 'uploader_id')
        uploader_url = self._search_regex(r'<a[^>]*href="(?P<uploader_url>[^"]+)', uploader_element, 'uploader_url')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': description,
            'uploader_id': uploader_id,
            'uploader_url': urljoin('https://vimp.oth-regensburg.de', uploader_url)
        }


class VimpOTHRMediaEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://vimp\.oth-regensburg\.de/media/embed\?key=(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'https://vimp.oth-regensburg.de/media/embed?key=adcacc06493f5e04cb927f13784aba2c',
        'md5': '5f9e19703bae38d463ea1a9a3c730f2b',
        'info_dict': {
            'id': 'adcacc06493f5e04cb927f13784aba2c',
            'ext': 'mp4',
            'title': 'Screencast der Vorlesung Betriebssysteme (OS) vom 12.10.2021',
            'thumbnail': 'https://vimp.oth-regensburg.de/cache/adcacc06493f5e04cb927f13784aba2c.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<video-js data-piwik-title="(.+?)"', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'url': 'https://vimp.oth-regensburg.de/getMedium/%(video_id)s.mp4' % locals(),
            'thumbnail': 'https://vimp.oth-regensburg.de/cache/%(video_id)s.jpg' % locals(),
        }


class VimpOTHRMediaPrivateIE(InfoExtractor):
    _VALID_URL = r'https?://vimp\.oth-regensburg\.de/m/(?P<id>[a-z0-9]{128})'
    _TEST = {
        'url': 'https://vimp.oth-regensburg.de/m/1a1c13511badaeb37546e9bfaefe9796b824153c0cdebee49dbc84c7a6aa52cd6fd55eaa45f8a35e45f9a4a4d8113d3f4ce166b3ac57c87a9d28f5735650d1e2',
        'md5': '086922d06b504f5a8f91c54c9198a6c6',
        'info_dict': {
            'id': '1a1c13511badaeb37546e9bfaefe9796b824153c0cdebee49dbc84c7a6aa52cd6fd55eaa45f8a35e45f9a4a4d8113d3f4ce166b3ac57c87a9d28f5735650d1e2',
            'ext': 'mp4',
            'title': 'AD IT3IT4 SoSe2021 Vorlesung 6',
            'description': '6. Vorlesung AD IT3IT4 SoSe 2021',
            'thumbnail': 'https://vimp.oth-regensburg.de/cache/45730408711783c78320ddfc81eb96f2.jpg',
            'display_id': '0b3bbf4a75f4c85b1b9a63c79e7054d3',
            'uploader_id': 'vok39696'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta(
            ['og:title', 'twitter:title', 'title'],
            webpage, 'title', default=None)

        description = self._html_search_meta(
            ['og:description', 'twitter:description'],
            webpage, 'description', default=None)

        thumbnail = self._html_search_meta(
            ['og:image', 'twitter:image'],
            webpage, 'thumbnail', default=None)

        video_url = self._og_search_video_url(webpage)

        # display_id = extract_attributes(get_element_by_id('sharekey', webpage)).get('value')
        display_id = self._search_regex(
            r'https?://vimp\.oth-regensburg\.de/getMedium/([a-z0-9]{32})\.mp4',
            video_url, 'display_id', fatal=False)

        uploader_element = get_element_by_class('uploader', webpage)
        uploader_id = self._search_regex(
            r'alt="([a-z]{3}[0-9]{5})"',
            uploader_element, 'uploader_id', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': description,
            'display_id': display_id,
            'uploader_id': uploader_id
        }
