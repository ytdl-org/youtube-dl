from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    clean_html,
    get_element_by_id,
)


class TechTVMITIE(InfoExtractor):
    IE_NAME = 'techtv.mit.edu'
    _VALID_URL = r'https?://techtv\.mit\.edu/(videos|embeds)/(?P<id>\d+)'

    _TEST = {
        'url': 'http://techtv.mit.edu/videos/25418-mit-dna-learning-center-set',
        'md5': '1f8cb3e170d41fd74add04d3c9330e5f',
        'info_dict': {
            'id': '25418',
            'ext': 'mp4',
            'title': 'MIT DNA Learning Center Set',
            'description': 'md5:82313335e8a8a3f243351ba55bc1b474',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        raw_page = self._download_webpage(
            'http://techtv.mit.edu/videos/%s' % video_id, video_id)
        clean_page = re.compile(r'<!--.*?-->', re.S).sub('', raw_page)

        base_url = self._search_regex(
            r'ipadUrl: \'(.+?cloudfront.net/)', raw_page, 'base url')
        formats_json = self._search_regex(
            r'bitrates: (\[.+?\])', raw_page, 'video formats')
        formats_mit = json.loads(formats_json)
        formats = [
            {
                'format_id': f['label'],
                'url': base_url + f['url'].partition(':')[2],
                'ext': f['url'].partition(':')[0],
                'format': f['label'],
                'width': f['width'],
                'vbr': f['bitrate'],
            }
            for f in formats_mit
        ]

        title = get_element_by_id('edit-title', clean_page)
        description = clean_html(get_element_by_id('edit-description', clean_page))
        thumbnail = self._search_regex(
            r'playlist:.*?url: \'(.+?)\'',
            raw_page, 'thumbnail', flags=re.DOTALL)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
        }


class MITIE(TechTVMITIE):
    IE_NAME = 'video.mit.edu'
    _VALID_URL = r'https?://video\.mit\.edu/watch/(?P<title>[^/]+)'

    _TEST = {
        'url': 'http://video.mit.edu/watch/the-government-is-profiling-you-13222/',
        'file': '.mp4',
        'md5': '7db01d5ccc1895fc5010e9c9e13648da',
        'info_dict': {
            'id': '21783',
            'ext': 'mp4',
            'title': 'The Government is Profiling You',
            'description': 'md5:ad5795fe1e1623b73620dbfd47df9afd',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        embed_url = self._search_regex(
            r'<iframe .*?src="(.+?)"', webpage, 'embed url')
        return self.url_result(embed_url, ie='TechTVMIT')
