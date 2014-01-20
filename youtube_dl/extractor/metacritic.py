from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    fix_xml_ampersands,
)


class MetacriticIE(InfoExtractor):
    _VALID_URL = r'https?://www\.metacritic\.com/.+?/trailers/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.metacritic.com/game/playstation-4/infamous-second-son/trailers/3698222',
        'file': '3698222.mp4',
        'info_dict': {
            'title': 'inFamous: Second Son - inSide Sucker Punch: Smoke & Mirrors',
            'description': 'Take a peak behind-the-scenes to see how Sucker Punch brings smoke into the universe of inFAMOUS Second Son on the PS4.',
            'duration': 221,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        # The xml is not well formatted, there are raw '&'
        info = self._download_xml('http://www.metacritic.com/video_data?video=' + video_id,
            video_id, 'Downloading info xml', transform_source=fix_xml_ampersands)

        clip = next(c for c in info.findall('playList/clip') if c.find('id').text == video_id)
        formats = []
        for videoFile in clip.findall('httpURI/videoFile'):
            rate_str = videoFile.find('rate').text
            video_url = videoFile.find('filePath').text
            formats.append({
                'url': video_url,
                'ext': 'mp4',
                'format_id': rate_str,
                'tbr': int(rate_str),
            })
        self._sort_formats(formats)

        description = self._html_search_regex(r'<b>Description:</b>(.*?)</p>',
            webpage, 'description', flags=re.DOTALL)

        return {
            'id': video_id,
            'title': clip.find('title').text,
            'formats': formats,
            'description': description,
            'duration': int(clip.find('duration').text),
        }
