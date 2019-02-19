# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (js_to_json)


class NxLoadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?nxload\.com/(?:embed-)?(?P<id>\w+)'

    _TESTS = [
        {
            'url': 'https://nxload.com/embed-w9uwujpk2na7.html',
            'md5': '955afd4f8f2c019bc4f116897346e3f9',
            'info_dict': {
                'id': 'w9uwujpk2na7',
                'ext': 'mp4',
                'title': 'pso firstman web 1080p mkv',
                'thumbnail': 're:^https://\w+.nxload.com/i/\d{2}/\d{5}/\w+.jpg$',
                'url': 're:^https://\w+.nxload.com/[,\w]+/v.mp4$'
            }
        },
        {
            'url': 'https://nxload.com/qhwxcxj5ah56.html',
            'md5': '983814ba610cd26ddd0819cd6d26ab68',
            'info_dict': {
                'id': 'qhwxcxj5ah56',
                'ext': 'mp4',
                'title': 'pso kkk 1080p mkv',
                'thumbnail': 're:^https://\w+.nxload.com/i/\d{2}/\d{5}/\w+.jpg',
                'url': 're:^https://\w+.nxload.com/[,\w]+/v.mp4$'
            }
        },
        {
            'url': 'https://nxload.com/embed-ig0ud2p3h57l.html',
            'md5': 'ab3a79c831fccfd8a34c77775082c694',
            'info_dict': {
                'id': 'ig0ud2p3h57l',
                'ext': 'mp4',
                'title': 'streams org Noragami S1E01 German DTS 1080p Blu Ray x264 mkv',
                'thumbnail': 're:^https://\w+.nxload.com/i/\d{2}/\d{5}/\w+.jpg',
                'url': 're:^https://\w+.nxload.com/[,\w]+/v.mp4$'
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('https://nxload.com/' + video_id, video_id)

        title = self._html_search_regex(r'<title>Watch ([^<]+)</title>', webpage, 'title', '')
        alt_title = self._html_search_regex(r'<div class="filename">([^<]+)', webpage, 'title', video_id)
        title = title or alt_title

        json = self._search_regex(r'new Clappr\.Player\(((?:.|\s)+?})\);', webpage, 'json').replace('function() {  }', '0').replace('3*1024*1024', '3145728')
        jsonObj = self._parse_json(json, video_id, transform_source=js_to_json)

        self.report_extraction(video_id)

        sources = jsonObj.get('sources')
        labels = jsonObj.get('levelSelectorConfig').get('labels')
        manifest_url = sources[0]
        formats = [
            {
                'url': sources[1],
                'format_id': labels.get('1'),
                'width': 1920,
                'height': 1080
            },
            {
                'url': sources[2],
                'format_id': labels.get('0'),
                'width': 1280,
                'height': 720,
                'quality': -2
            }
        ]
        self._sort_formats(formats)

        thumbnail = jsonObj.get('poster')
        subtitles = {}
        for subtitle in jsonObj.get('playback').get('externalTracks'):
            label = subtitle.get('label')
            url = subtitle.get('src')
            if label != 'Upload SRT':
                subtitles[label] = [{'url': url}]

            return {
                'id': video_id,
                'formats': formats,
                'manifest_url': manifest_url,
                'title': title,
                'alt_title': alt_title,
                'thumbnail': thumbnail,
                'subtitles': subtitles
            }
