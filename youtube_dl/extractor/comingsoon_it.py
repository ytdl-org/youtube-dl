# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ComingSoonITIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?comingsoon\.it/film/.*\b/video/\?.*\bvid=(?P<id>\w+)'
    _TESTS = [
        {
            'url': 'http://www.comingsoon.it/film/1981-indagine-a-new-york/50825/video/?vid=16392',
            'md5': '347808c99cce66b7b3654f7b694f6dfa',
            'info_dict': {
                'id': '16392',
                'ext': 'mp4',
                'title': '1981: Indagine a New York, Trailer del film, versione originale - Film (2014)',
                'url': 'http://video.comingsoon.it/MP4/16392.mp4',
                'description': 'Trailer del film, versione originale - 1981: Indagine a New York'
            },
            'params': {
                'format': 'sd',
            },
        },
        {
            'url': 'http://www.comingsoon.it/film/1981-indagine-a-new-york/50825/video/?vid=16392',
            'md5': '15910a31dc49cb709d83d012ddefa8b1',
            'info_dict': {
                'id': '16392',
                'ext': 'mp4',
                'title': '1981: Indagine a New York, Trailer del film, versione originale - Film (2014)',
                'url': 'http://video.comingsoon.it/MP4/16392HD.mp4',
                'description': 'Trailer del film, versione originale - 1981: Indagine a New York'
            },
            'params': {
                'format': 'hd',
            },
        },
        {
            'url': 'http://www.comingsoon.it/film/il-passato-e-una-terra-straniera/39912/video/?vid=1564',
            'md5': '9c8db6b04d4c3858ad31857ce1c82350',
            'info_dict': {
                'id': '1564',
                'ext': 'flv',
                'title': 'Il passato è una terra straniera, Trailer del film diretto da Daniele Vicari, con Elio Germano - Film (2008)',
                'url': 'http://video.comingsoon.it/1564.flv',
                'description': 'Trailer del film diretto da Daniele Vicari, con Elio Germano - Il passato è una terra straniera'
            },
            'params': {
                'format': 'sd',
            },
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, 'downloading webpage with metadata')
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        embedPage = self._download_webpage('http://www.comingsoon.it/videoplayer/embed/?idv=' + video_id, video_id, 'downloading webpage with video urls')
        lowRes = self._search_regex(r'vLwRes:  "(.*)"', embedPage, 'Low resolution filename', default=None)
        highRes = self._search_regex(r'vHiRes:  "(.*)"', embedPage, 'High ressolution filename', default=None)
        formats = []
        formats.append(
            {
                'url': 'http://video.comingsoon.it/' + lowRes,
                'format': 'Standard Definition',
                'format_id': 'sd'
            })
        if(lowRes != highRes):
            formats.append(
                {
                    'url': 'http://video.comingsoon.it/' + highRes,
                    'format': 'High Definition',
                    'format_id': 'hd'
                })
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }
