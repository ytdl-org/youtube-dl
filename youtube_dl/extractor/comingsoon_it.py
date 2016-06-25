# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ComingSoonITIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?comingsoon\.it/film/.*\b/video/\?.*\bvid=(?P<id>\w+)'
    _TEST = {
        'url': 'http://www.comingsoon.it/film/1981-indagine-a-new-york/50825/video/?vid=16392',
        'md5': '347808c99cce66b7b3654f7b694f6dfa',
        'info_dict': {
            'id': '16392',
            'ext': 'mp4',
            'title': '1981: Indagine a New York, Trailer del film, versione originale - Film (2014)',
            'url': 'http://video.comingsoon.it/MP4/16392.mp4',
            'description': 'Trailer del film, versione originale - 1981: Indagine a New York'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            
            'formats': [{
                    'url': 'http://video.comingsoon.it/MP4/' + video_id + '.mp4',
                    'format': 'Standard Definition'
                },{
                    'url': 'http://video.comingsoon.it/MP4/' + video_id + '.mp4',
                    'format': 'High Definition'}],
            'ext': 'mp4'
        }