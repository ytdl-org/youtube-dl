# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .theplatform import ThePlatformIE


class CBSNewsIE(ThePlatformIE):
    IE_DESC = 'CBS News'
    _VALID_URL = r'http://(?:www\.)?cbsnews\.com/(?:[^/]+/)+(?P<id>[\da-z_-]+)'

    _TESTS = [
        {
            'url': 'http://www.cbsnews.com/news/tesla-and-spacex-elon-musks-industrial-empire/',
            'info_dict': {
                'id': 'tesla-and-spacex-elon-musks-industrial-empire',
                'ext': 'flv',
                'title': 'Tesla and SpaceX: Elon Musk\'s industrial empire',
                'thumbnail': 'http://beta.img.cbsnews.com/i/2014/03/30/60147937-2f53-4565-ad64-1bdd6eb64679/60-0330-pelley-640x360.jpg',
                'duration': 791,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.cbsnews.com/videos/fort-hood-shooting-army-downplays-mental-illness-as-cause-of-attack/',
            'info_dict': {
                'id': 'fort-hood-shooting-army-downplays-mental-illness-as-cause-of-attack',
                'ext': 'mp4',
                'title': 'Fort Hood shooting: Army downplays mental illness as cause of attack',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 205,
                'subtitles': {
                    'en': [{
                        'ext': 'ttml',
                    }],
                },
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_info = json.loads(self._html_search_regex(
            r'(?:<ul class="media-list items" id="media-related-items"><li data-video-info|<div id="cbsNewsVideoPlayer" data-video-player-options)=\'({.+?})\'',
            webpage, 'video JSON info'))

        item = video_info['item'] if 'item' in video_info else video_info
        title = item.get('articleTitle') or item.get('hed')
        duration = item.get('duration')
        thumbnail = item.get('mediaImage') or item.get('thumbnail')

        subtitles = {}
        if 'mpxRefId' in video_info:
            subtitles['en'] = [{
                'ext': 'ttml',
                'url': 'http://www.cbsnews.com/videos/captions/%s.adb_xml' % video_info['mpxRefId'],
            }]

        formats = []
        for format_id in ['RtmpMobileLow', 'RtmpMobileHigh', 'Hls', 'RtmpDesktop']:
            pid = item.get('media' + format_id)
            if not pid:
                continue
            release_url = 'http://link.theplatform.com/s/dJ5BDC/%s?format=SMIL&mbr=true' % pid
            tp_formats, tp_subtitles = self._extract_theplatform_smil(release_url, video_id, 'Downloading %s SMIL data' % pid)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }
