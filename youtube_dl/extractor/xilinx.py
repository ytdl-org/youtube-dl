# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .brightcove import BrightcoveNewIE


class XilinxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xilinx\.com/video/(?P<cat>[^/]+)/(?P<id>[\w-]+)\.html'
    _TEST = {
        'url': 'https://www.xilinx.com/video/hardware/model-composer-product-overview.html',
        'info_dict': {
            'id': '5678303886001',
            'ext': 'mp4',
            'title': 'Model Composer Product Overview',
            'description': 'md5:806e3831788848342777cdc3947c3d58',
            'timestamp': 1513121997,
            'upload_date': '20171212',
            'uploader_id': '17209957001',
            'categories': 'hardware',
        },
        'params': {
            't': True,
        },
    }

    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/%s_%s/index.html?videoId=%s'

    def _real_extract(self, url):

        page_id = self._match_id(url)
        category = re.match(self._VALID_URL, url).group('cat')
        webpage = self._download_webpage(url, page_id)

        urls = []
        for account_id, player_id, embed in re.findall(
                r'''<script[^>]+src=["\'](?:https?:)?//players\.brightcove\.net/(\d+)/([^/]+)_([^/]+)/index(?:\.min)?\.js''', webpage):
            for video_id in re.findall(r'''<div[^>]*data-video-id=['"](\d+)['"]''', webpage):

                if not video_id:
                    continue

                if not account_id:
                    continue

                player_id = player_id or 'default'

                embed = embed or 'default'

                bc_url = self.BRIGHTCOVE_URL_TEMPLATE % (account_id, player_id, embed, video_id)

                urls.append(bc_url)

        if (len(urls) == 0):
            self.report_warning("Couldn't get any video urls.")

        if (len(urls) > 1):
            self.report_warning("Got more than one video urls, using the first one.")

        return {
            '_type': 'url_transparent',
            'url': urls[0],
            'categories': category,
            'ie_key': BrightcoveNewIE.ie_key(),
        }
