from __future__ import unicode_literals

from .common import InfoExtractor


class YouJizzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?youjizz\.com/videos/(?:[^/#?]+)?-(?P<id>[0-9]+)\.html(?:$|[?#])'
    _TESTS = [{
        'url': 'http://www.youjizz.com/videos/zeichentrick-1-2189178.html',
        'md5': '78fc1901148284c69af12640e01c6310',
        'info_dict': {
            'id': '2189178',
            'ext': 'mp4',
            'title': 'Zeichentrick 1',
            'age_limit': 18,
        }
    }, {
        'url': 'http://www.youjizz.com/videos/-2189178.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        # YouJizz's HTML5 player has invalid HTML
        webpage = webpage.replace('"controls', '" controls')
        age_limit = self._rta_search(webpage)
        video_title = self._html_search_regex(
            r'<title>\s*(.*)\s*</title>', webpage, 'title')

        info_dict = self._parse_html5_media_entries(url, webpage, video_id)[0]

        info_dict.update({
            'id': video_id,
            'title': video_title,
            'age_limit': age_limit,
        })

        return info_dict
