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
    }, {
        # Multiple videos per page (https://github.com/rg3/youtube-dl/issues/6542)    
        'url': 'http://www.liveleak.com/view?i=677_1439397581',
        'info_dict': {
            'id': '677_1439397581',
            'title': 'Fuel Depot in China Explosion caught on video',
        },
        'playlist_mincount': 3
    }, {
        # Embedded youtube video
        'url': 'http://www.liveleak.com/view?i=db4_1442324398',
        'md5': 'c72ce559d02cf26b6540c87d6a015c0c',
        'info_dict': {
            'id': 'db4_1442324398',
            'ext': 'mp4',
            'description': 'Is it worth 6 minutes of your time to listen to this?',
            'uploader': 'Vfor',
            'uploader_id': 'iSSerDc',
            'upload_date': '20070703',
            'title': "Pachelbel's Canon in D - Breathtaking"
        }

    }]

    def _video_count(self, entries):
        count = len(entries)
        if count == 0:
            return ''
        else:
            return '-' + str(count)

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
                'id': page_id + self._video_count(entries),
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
                'id': page_id + self._video_count(entries),
                'title': video_title,
                'description': video_description,
                'uploader': video_uploader,
                'formats': formats,
                'age_limit': age_limit,
            })

        embed_urls = list()

        for embed_prochan in re.findall(
                r'<iframe[^>]+src="(https?://www.prochan.com/embed\?[^"]+)"',
                webpage):
            embed_urls.append(embed_prochan)

        for embed_youtube in re.findall(
                r'<iframe[^>]+src="(https?://www.youtube.com/embed/[^"]+)"',
                webpage):
            embed_urls.append(embed_youtube)

        for embed_url in embed_urls:
            entries.append({
                '_type': 'url_transparent',
                'id': page_id + self._video_count(entries),
                'url': embed_url,
                'title': video_title,
                'description': video_description,
                'uploader': video_uploader,
                'age_limit': age_limit,
            })

        return {
            '_type': 'multi_video',
            'id': page_id,
            'title': video_title,
            'entries': entries,
        }
