# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    clean_html
)


class VidelloIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?embed\.vidello\.com/[0-9]/(?P<id>[a-zA-Z0-9]+)/player.html'
    _TEST = {
        'url': 'https://embed.vidello.com/2/t1umm637xb1ylgw4/player.html',
        'md5': '7a4d76ac74ef7724af4c6c3ecb5e0042',
        'info_dict': {
            'id': 't1umm637xb1ylgw4',
            'ext': 'mp4',
            'title': 'Vidello Hosting & Marketing',
            'description': "Start marketing your videos more effectively on \x03the web utilising vidello's premium hosting, streaming, \x03analytics & marketing features to grow your \x03online business fast."
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        vidello_settings = self._parse_json(self._search_regex(
            r'settings=({.+});', webpage, 'vidello settings'), video_id)

        video_url = ""
        video_sources = vidello_settings['player']['clip']['sources']
        for curr_entry in video_sources:
            if curr_entry['type'] == "video/mp4":
                video_url = "http://" + curr_entry["src"][2:]
        title = vidello_settings['cta'][0]['values']['product_title']
        description = clean_html(vidello_settings.get('cta')[0].get('values').get('product_desc'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': video_url
        }
