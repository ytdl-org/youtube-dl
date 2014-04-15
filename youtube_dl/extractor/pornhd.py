from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import int_or_none


class PornHdIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?pornhd\.com/(?:[a-z]{2,4}/)?videos/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
        'md5': '956b8ca569f7f4d8ec563e2c41598441',
        'info_dict': {
            'id': '1962',
            'ext': 'mp4',
            'title': 'Sierra loves doing laundry',
            'description': 'md5:8ff0523848ac2b8f9b065ba781ccf294',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        TITLE_SUFFIX = ' porn HD Video | PornHD.com '
        if title.endswith(TITLE_SUFFIX):
            title = title[:-len(TITLE_SUFFIX)]

        description = self._html_search_regex(
            r'<div class="description">([^<]+)</div>', webpage, 'description', fatal=False)
        view_count = int_or_none(self._html_search_regex(
            r'(\d+) views 	</span>', webpage, 'view count', fatal=False))

        formats = [
            {
                'url': format_url,
                'ext': format.lower(),
                'format_id': '%s-%s' % (format.lower(), quality.lower()),
                'quality': 1 if quality.lower() == 'high' else 0,
            } for format, quality, format_url in re.findall(
                r'var __video([\da-zA-Z]+?)(Low|High)StreamUrl = \'(http://.+?)\?noProxy=1\'', webpage)
        ]

        mobj = re.search(r'flashVars = (?P<flashvars>{.+?});', webpage)
        if mobj:
            flashvars = json.loads(mobj.group('flashvars'))
            formats.extend([
                {
                    'url': flashvars['hashlink'].replace('?noProxy=1', ''),
                    'ext': 'flv',
                    'format_id': 'flv-low',
                    'quality': 0,
                },
                {
                    'url': flashvars['hd'].replace('?noProxy=1', ''),
                    'ext': 'flv',
                    'format_id': 'flv-high',
                    'quality': 1,
                }
            ])
            thumbnail = flashvars['urlWallpaper']
        else:
            thumbnail = self._og_search_thumbnail(webpage)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'formats': formats,
            'age_limit': 18,
        }
