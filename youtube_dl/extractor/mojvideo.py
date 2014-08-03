import re

from .common import InfoExtractor

class MojvideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mojvideo\.com/video-.*/(?P<id>[a-f0-9]+)'
    _TEST = {
        'url': 'http://www.mojvideo.com/video-v-avtu-pred-mano-rdecelaska-alfi-nipic/3d1ed4497707730b2906',
        'md5': 'f7fd662cc8ce2be107b0d4f2c0483ae7',
        'info_dict': {
            'id': '3d1ed4497707730b2906',
            'ext': 'mp4',
            'title': 'V avtu pred mano rdečelaska - Alfi Nipič',
            'description':'Video: V avtu pred mano rdečelaska - Alfi Nipič',
            'height':37 8,
            'width':480
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        description = self._search_regex(r'<meta name="description" content="(.*)" />', webpage, 'video description')
        final_url = self._html_search_regex(r'mp4: \'(.*)\'', webpage, 'video url')
        height=int(self._search_regex(r'<meta name="video_height" content="([0-9]*)" />',webpage,"video height"))
        width=int(self._search_regex(r'<meta name="video_width" content="([0-9]*)" />',webpage,"video width"))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'ext': 'mp4',
            'url': final_url,
            'height':height,
            'width':width
        }