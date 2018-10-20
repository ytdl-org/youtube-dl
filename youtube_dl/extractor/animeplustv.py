from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class AnimePlusTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?animeplus\.tv/(?P<id>.+)'
    _TESTS = [{
        'url': 'http://www.animeplus.tv/karakuri-circus-episode-2-online',
        'info_dict': {
            'id': 'karakuri-circus-episode-2-online',
            'ext': 'mp4'
        },
        'skip': 'Video does not exist',
    },
        {
        'url': 'http://www.animeplus.tv/5-centimeters-per-second-movie-online',
        'info_dict': {
            'id': '5-centimeters-per-second-movie-online',
            'ext': 'mp4'
        },
        'skip': 'Video does not exist',
    }]

    def _real_extract(self, url):
        host_link_pattern = r'iframe\s*src\s*=\s*"(.+?)"'
        url = url.replace('-watch-online', '-online')
        video_id = self._match_id(url).replace('-watch-online', '-online')
        webpage = self._download_webpage(url, video_id)
        host_links = re.findall(host_link_pattern, webpage)
        additional_links = range(2, len(re.findall(r'a href="{0}'.format(url), webpage)) + 1)
        for add_link in additional_links:
            host_links[:0] = re.findall(
                host_link_pattern, self._download_webpage("{0}/{1}".format(url, add_link), video_id)
            )
        download_info = list()
        for i, host_link in enumerate(host_links, 1):
            video_link_dict = json.loads(
                self._html_search_regex(
                    r'var\svideo_links\s*\=\s*({.*})\;', self._download_webpage(host_link, host_link), 'video_link'
                )
            )
            download_info.append({
                '_type': 'video',
                'id': 'animeplus' if("-movie-" not in video_id) else 'animeplus-part-{0}'.format(i),
                'title': video_id.replace('-online', ''),
                'url': video_link_dict['normal']['storage'][0]['link']
            })
            if("-movie-" in video_id):
                if (i < 3):
                    continue
                else:
                    break
            else:
                break
        return download_info
