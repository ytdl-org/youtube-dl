from __future__ import unicode_literals

from .common import InfoExtractor


class TVANouvellesIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.|)tvanouvelles\.(ca|com|qc)/.*.?/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.tvanouvelles.ca/videos/5117035533001',
        'info_dict': {
            'id': '5117035533001',
            'ext': 'mp4',
            'title': 'L\u2019industrie du taxi d\xe9nonce l\u2019entente entre Qu\xe9bec et Uber: explications',
            'description': 'L\u2019industrie du taxi a unanimement a d\xe9nonc\xe9 l\u2019entente avec le gouvernement du Qu\xe9bec qui permet \xe0 l\u2019entreprise de covoiturage Uber de faire des affaires l\xe9galement dans le cadre d\u2019un projet pilote d\u2019un an.',
            'uploader_id': '1741764581',
            'timestamp': 1473352030,
            'upload_date': '20160908',
        },
        'add_ie': ['BrightcoveNew'],
        'skip': 'Not accessible from Travis CI server',
    }
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/1741764581/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        program_name = self._match_id(url)
        webpage = self._download_webpage(url, program_name)
        brightcove_id = self._search_regex(
            r'data-video-id\=(.+[0-9]?)', webpage, 'brightcove id')
        return self.url_result(self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew', brightcove_id)
