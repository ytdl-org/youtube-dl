from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import int_or_none


class LiveLeakIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?liveleak\.com/view\?(?:.*?)i=(?P<id>[\w_]+)(?:.*)'
    _TESTS = [{
        'url': 'http://www.liveleak.com/view?i=757_1364311680',
        'md5': '50f79e05ba149149c1b4ea961223d5b3',
        'info_dict': {
            'id': '757_1364311680',
            'ext': 'flv',
            'description': 'extremely bad day for this guy..!',
            'uploader': 'ljfriel2',
            'title': 'Most unlucky car accident'
        }
    }, {
        'url': 'http://www.liveleak.com/view?i=f93_1390833151',
        'md5': 'b13a29626183c9d33944e6a04f41aafc',
        'info_dict': {
            'id': 'f93_1390833151',
            'ext': 'mp4',
            'description': 'German Television Channel NDR does an exclusive interview with Edward Snowden.\r\nUploaded on LiveLeak cause German Television thinks the rest of the world isn\'t intereseted in Edward Snowden.',
            'uploader': 'ARD_Stinkt',
            'title': 'German Television does first Edward Snowden Interview (ENGLISH)',
        }
    }, {
        'url': 'http://www.liveleak.com/view?i=4f7_1392687779',
        'md5': '42c6d97d54f1db107958760788c5f48f',
        'info_dict': {
            'id': '4f7_1392687779',
            'ext': 'mp4',
            'description': "The guy with the cigarette seems amazingly nonchalant about the whole thing...  I really hope my friends' reactions would be a bit stronger.\r\n\r\nAction-go to 0:55.",
            'uploader': 'CapObveus',
            'title': 'Man is Fatally Struck by Reckless Car While Packing up a Moving Truck',
            'age_limit': 18,
        }
    }, {
        # Covers https://github.com/rg3/youtube-dl/pull/5983
        'url': 'http://www.liveleak.com/view?i=801_1409392012',
        'md5': '0b3bec2d888c20728ca2ad3642f0ef15',
        'info_dict': {
            'id': '801_1409392012',
            'ext': 'mp4',
            'description': "Happened on 27.7.2014. \r\nAt 0:53 you can see people still swimming at near beach.",
            'uploader': 'bony333',
            'title': 'Crazy Hungarian tourist films close call waterspout in Croatia'
        }
    }]

    video_count = 0
    def _video_count(self):
        self.video_count += 1
        if self.video_count == 1:
            return ''
        else:
            return '-' + str(self.video_count-1)

    # Removing '.h264_*.mp4' gives the raw video, which is essentially
    # the same video without the LiveLeak logo at the top (see
    # https://github.com/rg3/youtube-dl/pull/4768)
    def _get_orig_video_url(self, url):
        return re.sub(r'\.h264_.+?\.mp4', '', url)

    def _remove_rate_limit(self, url):
        return re.sub(r'&ec_rate=[0-9]+', '', url)

    def _real_extract(self, url):

        entries = list()  # collect all found videos

        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        video_title = self._og_search_title(webpage).replace('LiveLeak.com -', '').strip()
        video_description = self._og_search_description(webpage)
        video_uploader = self._html_search_regex(
            r'By:.*?(\w+)</a>', webpage, 'uploader', fatal=False)
        age_limit = int_or_none(self._search_regex(
            r'you confirm that you are ([0-9]+) years and over.',
            webpage, 'age limit', default=None))

        # extracts native video #1 (single video, maybe multiple formats)
        sources_raw = self._search_regex(
            r'(?s)sources:\s*(\[.*?\]),', webpage, 'video URLs', default=None)
        if sources_raw:
            sources_json = re.sub(r'\s([a-z]+):\s', r'"\1": ', sources_raw)
            sources = json.loads(sources_json)

            formats = [{
                'format_id': '%s' % i,
                'format_note': s.get('label'),
                'url': self._remove_rate_limit(s['file']),
            } for i, s in enumerate(sources)]
            for i, s in enumerate(sources):
                orig_url = self._remove_rate_limit(self._get_orig_video_url(s['file']))
                if s['file'] != orig_url:
                    formats.append({
                        'format_id': 'original-%s' % i,
                        'format_note': s.get('label'),
                        'url': orig_url,
                        'preference': 1,
                    })
            self._sort_formats(formats)

            entries.append({
                'id': page_id,
                'title': video_title,
                'description': video_description,
                'uploader': video_uploader,
                'formats': formats,
                'age_limit': age_limit,
            })

        # extracts native videos #2 (maybe multiple videos, single format)
        sources = re.findall(r'(?s)jwplayer.+?file: "(.+?)".+?config:', webpage)
        for url in sources:
            url = self._remove_rate_limit(url)
            formats = [{
                'format_id': '0',
                'format_note': 'standard quality (with logo)',
                'url': url,
            }]
            orig_url = self._get_orig_video_url(url)
            if orig_url != url:
                formats.append({
                    'format_id': '1',
                    'format_note': 'high quality (no logo)',
                    'url': orig_url,
                    'preference': 1,
                })
            entries.append({
                'id': page_id + self._video_count(),
                'title': video_title,
                'description': video_description,
                'uploader': video_uploader,
                'formats': formats,
                'age_limit': age_limit,
            })


        # collect embedded videos:
        embed_urls = list()

        # prochan.com:
        embed_prochan = (re.findall(
            r'<iframe[^>]+src="(http://www.prochan.com/embed\?[^"]+)"',
            webpage))
        if len(embed_prochan) > 0:
            for embed in embed_prochan:
                embed_urls.append(embed)

        # add all collected embed urls to list
        for embed_url in embed_urls:
            entries.append({
                '_type': 'url_transparent',
                'id': page_id + self._video_count(),
                'url': embed_url,
                'title': video_title,
                'description': video_description,
                'uploader': video_uploader,
                'age_limit': age_limit,
            })

        if len(entries) == 1:
            return entries[0]
        else:
            return {
                '_type': 'multi_video',
                'id': page_id,
                'entries': entries,
            }
