# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


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
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)
        video_url = self._og_search_video_url(webpage)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'description': description,
        }


class VimpOTHRMediaEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://vimp\.oth-regensburg\.de/media/embed\?key=(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'https://vimp.oth-regensburg.de/media/embed?key=adcacc06493f5e04cb927f13784aba2c&width=1280&height=720',
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
