from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class RtlluIE(InfoExtractor):
    IE_NAME = 'rtl.lu'

    _VALID_URL = r'https?://(www|tele|radio|5minutes)\.rtl\.lu\/.*?\/(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://tele.rtl.lu/emissiounen/documentaire-routwaissgro/lu/890363.html',
        'md5': '38a2d2286ff4b8ccc300e847294cb90a',
        'info_dict': {
            'id': '599319',
            'ext': 'mp4',
            'title': '"Vënz de Prënz" (18.03.2016)',
        },
    }

    def _real_extract(self, url):
        match = self._VALID_URL_RE.match(url)
        id = match.group('id')

        webpage = self._download_webpage(url, id)

        javascript_regex = r'<script language="Javascript">((\n*?.*?)*?)</script>'
        javascript = self._html_search_regex(javascript_regex, webpage, 'javascript')

        try:
            javascript_sources_regex = r'object.*\.sources = \'(?P<value>.*?)\';'
            sources = json.loads(re.search(javascript_sources_regex, javascript).group('value'))

            javascript_videoid_regex = r'object.*\.videoid = \'(?P<value>.*?)\';'
            javascript_videoid = re.search(javascript_videoid_regex, javascript).group('value')

            javascript_publicdate_regex = r'object.*\.publicdate = \'(?P<value>.*?)\';'
            javascript_publicdate = re.search(javascript_publicdate_regex, javascript).group('value')

            javascript_thumbnail_regex = r'object.*\.thumbnail = \'(?P<value>.*?)\';'
            javascript_thumbnail = re.search(javascript_thumbnail_regex, javascript).group('value')

            formats = [
                {
                    'url': sources['rtmp']['src'],
                    'format': 'RTMP Stream',
                    'format_id': 'rtmp',
                    'protocol': 'rtmp',
                },

                {
                    'url': sources['httplq']['src'],
                    'format': 'Low Quality',
                    'format_id': 'lq',
                    'protocol': 'http',
                },
                {
                    'url': sources['http']['src'],
                    'format': 'Standard Quality',
                    'format_id': 'sd',
                    'protocol': 'http',
                },
                {
                    'url': sources['httphq']['src'],
                    'format': 'High Quality',
                    'format_id': 'hq',
                    'protocol': 'http',
                },
            ]

            return {
                'id': javascript_videoid or id,
                'title': self.get_video_title(webpage, javascript),
                'formats': formats,
                'thumbnail': javascript_thumbnail,
                'upload_date': javascript_publicdate,
            }
        except AttributeError:
            javascript_mp3_regex = r'play_mp3\("object[0-9]*", "(?P<value>.*?)",'
            javascript_mp3 = re.search(javascript_mp3_regex, javascript).group('value')

            return {
                'id': id,
                'title': self.get_audio_title(webpage),
                'url': javascript_mp3,
            }

    def get_video_title(self, webpage, javascript):

        title_regex = r'</div>.*<h1>(?P<title>.*?)</h1>.*?<p class="sub">'
        title = re.findall(title_regex, webpage, flags=re.S)

        if title:
            title = title[-1]

        javascript_title_regex = r'object.*\.title = \'(?P<value>.*?)\';'
        javascript_title = re.search(javascript_title_regex, javascript).group('value')
        return javascript_title or title or self._og_search_title(webpage)

    def get_audio_title(self, webpage):

        title_regex = r'<header><h1><span>(?P<span>.*?)</span>(?P<title>.*?)</h1>'
        title = self._html_search_regex(title_regex, webpage, 'title', group='title', fatal=False)
        span = self._html_search_regex(title_regex, webpage, 'span', group='span', fatal=False)

        if title or span:
            title = ' - '.join([span, title])

        h5_title_regex = r'<h5>(?P<title>.*?)</h5>'
        h5_title = self._html_search_regex(h5_title_regex, webpage, 'title', group='title', fatal=False)

        return title or h5_title or self._og_search_title(webpage)
