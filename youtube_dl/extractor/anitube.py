from __future__ import unicode_literals

from .nuevo import NuevoBaseIE


class AnitubeIE(NuevoBaseIE):
    IE_NAME = 'anitube.se'
    _VALID_URL = r'https?://(?:www\.)?anitube\.se/video/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.anitube.se/video/36621',
        'md5': '59d0eeae28ea0bc8c05e7af429998d43',
        'info_dict': {
            'id': '36621',
            'ext': 'mp4',
            'title': 'Recorder to Randoseru 01',
            'duration': 180.19,
        },
        'skip': 'Blocked in the US',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        key = self._search_regex(
            r'src=["\']https?://[^/]+/embed/([A-Za-z0-9_-]+)', webpage, 'key')

        return self._extract_nuevo(
            'http://www.anitube.se/nuevo/econfig.php?key=%s' % key, video_id)
