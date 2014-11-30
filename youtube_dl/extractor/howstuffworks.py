from __future__ import unicode_literals

import re
import json
import random
import string

from .common import InfoExtractor
from ..utils import find_xpath_attr


class HowStuffWorksIE(InfoExtractor):
    _VALID_URL = r'https?://[\da-z-]+\.howstuffworks\.com/(?:[^/]+/)*\d+-(?P<id>.+?)-video\.htm'
    _TESTS = [
        {
            'url': 'http://adventure.howstuffworks.com/5266-cool-jobs-iditarod-musher-video.htm',
            'info_dict': {
                'id': '450221',
                'display_id': 'cool-jobs-iditarod-musher',
                'ext': 'flv',
                'title': 'Cool Jobs - Iditarod Musher',
                'description': 'md5:82bb58438a88027b8186a1fccb365f90',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                # md5 is not consistent
                'skip_download': True
            }
        },
        {
            'url': 'http://adventure.howstuffworks.com/7199-survival-zone-food-and-water-in-the-savanna-video.htm',
            'info_dict': {
                'id': '453464',
                'display_id': 'survival-zone-food-and-water-in-the-savanna',
                'ext': 'mp4',
                'title': 'Survival Zone: Food and Water In the Savanna',
                'description': 'md5:7e1c89f6411434970c15fa094170c371',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                # md5 is not consistent
                'skip_download': True
            }
        },
        {
            'url': 'http://entertainment.howstuffworks.com/arts/2706-sword-swallowing-1-by-dan-meyer-video.htm',
            'info_dict': {
                'id': '440011',
                'display_id': 'sword-swallowing-1-by-dan-meyer',
                'ext': 'flv',
                'title': 'Sword Swallowing #1 by Dan Meyer',
                'description': 'md5:b2409e88172913e2e7d3d1159b0ef735',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                # md5 is not consistent
                'skip_download': True
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        webpage = self._download_webpage(url, display_id)

        content_id = self._search_regex(r'var siteSectionId="(\d+)";', webpage, 'content id')

        mp4 = self._search_regex(
            r'''(?xs)var\s+clip\s*=\s*{\s*
                .+?\s*
                content_id\s*:\s*%s\s*,\s*
                .+?\s*
                mp4\s*:\s*\[(.*?),?\]\s*
                };\s*
                videoData\.push\(clip\);''' % content_id,
            webpage, 'mp4', fatal=False, default=None)

        smil = self._download_xml(
            'http://services.media.howstuffworks.com/videos/%s/smil-service.smil' % content_id,
            content_id, 'Downloading video SMIL')

        http_base = find_xpath_attr(
            smil,
            './{0}head/{0}meta'.format('{http://www.w3.org/2001/SMIL20/Language}'),
            'name',
            'httpBase').get('content')

        def random_string(str_len=0):
            return ''.join([random.choice(string.ascii_uppercase) for _ in range(str_len)])

        URL_SUFFIX = '?v=2.11.3&fp=LNX 11,2,202,356&r=%s&g=%s' % (random_string(5), random_string(12))

        formats = []

        if mp4:
            for video in json.loads('[%s]' % mp4):
                bitrate = video['bitrate']
                fmt = {
                    'url': video['src'].replace('http://pmd.video.howstuffworks.com', http_base) + URL_SUFFIX,
                    'format_id': bitrate,
                }
                m = re.search(r'(?P<vbr>\d+)[Kk]', bitrate)
                if m:
                    fmt['vbr'] = int(m.group('vbr'))
                formats.append(fmt)
        else:
            for video in smil.findall(
                    './/{0}body/{0}switch/{0}video'.format('{http://www.w3.org/2001/SMIL20/Language}')):
                vbr = int(video.attrib['system-bitrate']) / 1000
                formats.append({
                    'url': '%s/%s%s' % (http_base, video.attrib['src'], URL_SUFFIX),
                    'format_id': '%dk' % vbr,
                    'vbr': vbr,
                })

        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        TITLE_SUFFIX = ' : HowStuffWorks'
        if title.endswith(TITLE_SUFFIX):
            title = title[:-len(TITLE_SUFFIX)]

        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': content_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
