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
            'height':378,
            'width':480
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        # TODO more code goes here, for example ...
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
            # TODO more properties (see youtube_dl/extractor/common.py)
        }