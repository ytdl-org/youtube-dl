# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from .brightcove import BrightcoveNewIE


class VrakIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vrak\.tv/videos\?.*?target=(?P<id>[0-9\.]+).*'
    _TEST = {
        'url': 'http://www.vrak.tv/videos?target=1.2240923&filtre=emission&id=1.1806721',
        'md5': 'c5d5ce237bca3b1e990ce1b48d1f0948',
        'info_dict': {
            'id': '5231040869001',
            'ext': 'mp4',
            'title': 'Référendums américains, animés japonais et hooligans russes',
            'upload_date': '20161201',
            'description': 'This video file has been uploaded automatically using Oprah. It should be updated with real description soon.',
            'timestamp': 1480628425,
            'uploader_id': '2890187628001',
        }
    }

    def _real_extract(self, url):
        url_id = self._match_id(url)
        webpage = self._download_webpage(url, url_id)

        result = {}
        result['title'] = self._html_search_regex(
            r'<h3 class="videoTitle">(.+?)</h3>', webpage, 'title')

        # Inspired from BrightcoveNewIE._extract_url()
        entries = []
        for account_id, player_id, _, video_id in re.findall(
                # account_id, player_id and embed from:
                #   <div class="video-player [...]
                #     data-publisher-id="2890187628001"
                #     data-player-id="VkSnGw3cx"
                # video id is extracted from weird CMS Java/Javascript notation:
                #   RW java.lang.String value = '5231040869001';
                # Need to use backtrack to pin to a ref since video is in grid
                # layout with others
                r'''(?sx)
                    <div[^>]+
                        data-publisher-id=["\'](\d+)["\']
                        [^>]*
                        data-player-id=["\']([^"\']+)["\']
                        [^>]*
                        refId&quot;:&quot;([^&]+)&quot;
                        [^>]*
                        >.*?
                    </div>.*?
                    RW\ java\.lang\.String\ value\ =\ \'brightcove\.article\.\d+\.\3\'
                    [^>]*
                    RW\ java\.lang\.String\ value\ =\ \'(\d+)\'
                ''', webpage):

            entries.append(
                'http://players.brightcove.net/%s/%s_%s/index.html?videoId=%s'
                % (account_id, player_id, 'default', video_id))

        if entries:
            result = self.url_result(entries[0], BrightcoveNewIE.ie_key())

        return result
