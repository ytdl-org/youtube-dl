from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CultureUnpluggedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cultureunplugged\.com/documentary/watch-online/play/(?P<id>\d+)/(?P<display_id>[^/]+)'
    _TEST = {
        'url': 'http://www.cultureunplugged.com/documentary/watch-online/play/53662/The-Next--Best-West',
        'md5': 'ac6c093b089f7d05e79934dcb3d228fc',
        'info_dict': {
            'id': '53662',
            'display_id': 'The-Next--Best-West',
            'description': 'The Next, Best West explores our changing relationship with the land that sustains us. It tells the story of how the conventional American concept of progress has steered our exploitation of the Western landscape, and takes you to three places – Colorado’s San Luis Valley, the high plains of eastern Montana and the Elwha River on Washington’s Olympic Peninsula – where a vibrant new understanding of progress presages a better future. The Next, Best West shows how our interpretation of progress has shaped the singular landscape of the American West, and how a new understanding of progress may be our best hope for a bright and healthy future. The West is a place of pure beauty that has provided us so much, yet we have cared for it too little. But that is beginning to change.',
            'ext': 'mp4',
            'title': 'The Next, Best West',
            'thumbnail': 'http://cdn.cultureunplugged.com/thumbnails_16_9/lg/53662.jpg',
        }
    }

    def _real_extract(self, url):

        video_id = self._match_id(url)
        display_id = re.match(self._VALID_URL, url).group('display_id')
        json_url = 'http://www.cultureunplugged.com/movie-data/cu-%s.json' % (video_id)
        json_output = self._download_json(json_url, video_id)

        title = json_output.get('title')
        description = json_output.get('synopsis')
        creator = json_output.get('producer')
        thumbnail = json_output.get('large_thumb')

        formats = [{
            'url': json_output['url'],
            'format': 'mp4'
            }]

        return {
            'id': video_id,
            'title': title,
            'display_id': display_id,
            'description': description,
            'creator': creator,
            'thumbnail': thumbnail,
            'formats': formats
        }
