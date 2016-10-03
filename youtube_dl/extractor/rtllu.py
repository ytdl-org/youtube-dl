# coding: utf-8
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
        id = self._match_id(url)
        webpage = self._download_webpage(url, id)

        javascript_regex = r'<script language="Javascript">((\n*?.*?)*?)</script>'
        javascript = self._html_search_regex(javascript_regex, webpage, 'javascript')

        try:
            javascript_sources_regex = r'object.*\.sources = \'(?P<value>.*?)\';'
            sources = self._search_regex(javascript_sources_regex, javascript, 'sources')
            sources = json.loads(sources)

            videoid_regex = r'object.*\.videoid = \'(?P<value>.*?)\';'
            videoid = self._search_regex(videoid_regex, javascript, 'videoid', fatal=False, default=id)

            publicdate_regex = r'object.*\.publicdate = \'(?P<value>.*?)\';'
            publicdate = self._search_regex(publicdate_regex, javascript, 'publicdate', fatal=False)

            thumbnail_regex = r'object.*\.thumbnail = \'(?P<value>.*?)\';'
            thumbnail = self._search_regex(thumbnail_regex, javascript, 'thumbnail', fatal=False)

            formats = []

            rtmp_source = sources.get('rtmp')
            if rtmp_source is not None:
                rtmp_url = rtmp_source.get('src')

                if rtmp_url is not None:
                    formats.append(
                        {
                            'url': rtmp_url,
                            'format': 'RTMP Stream',
                            'format_id': 'rtmp',
                            'protocol': 'rtmp'
                        }
                    )

            httplq_source = sources.get('httplq')
            if httplq_source is not None:
                httplq_url = httplq_source.get('src')

                if httplq_url is not None:
                    formats.append(
                        {
                            'url': httplq_url,
                            'format': 'Low Quality',
                            'format_id': 'lq',
                            'protocol': 'http',
                        }
                    )

            http_source = sources.get('http')
            if http_source is not None:
                http_url = http_source.get('src')

                if http_url is not None:
                    formats.append(
                        {
                            'url': http_url,
                            'format': 'Standard Quality',
                            'format_id': 'sd',
                            'protocol': 'http',
                        }
                    )

            httphq_source = sources.get('httphq')
            if httphq_source is not None:
                httphq_url = httphq_source.get('src')

                if httphq_url is not None:
                    formats.append(
                        {
                            'url': httphq_url,
                            'format': 'High Quality',
                            'format_id': 'hq',
                            'protocol': 'http',
                        }
                    )

            return {
                'id': videoid,
                'title': self.get_video_title(webpage, javascript),
                'formats': formats,
                'thumbnail': thumbnail,
                'upload_date': publicdate,
            }
        except AttributeError:
            mp3_regex = r'play_mp3\("object[0-9]*", "(?P<value>.*?)",'
            mp3_url = self._search_regex(mp3_regex, javascript, 'mp3_url')

            return {
                'id': id,
                'title': self.get_audio_title(webpage),
                'url': mp3_url,
            }

    def get_video_title(self, webpage, javascript):

        title_regex = r'</div>.*<h1>(?P<title>.*?)</h1>.*?<p class="sub">'
        title = re.findall(title_regex, webpage, flags=re.S)

        if title:
            title = title[-1]

        javascript_title_regex = r'object.*\.title = \'(?P<value>.*?)\';'
        javascript_title = self._search_regex(javascript_title_regex, javascript, 'javascript_title', fatal=False)
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
