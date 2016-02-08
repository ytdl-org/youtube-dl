from __future__ import unicode_literals

from .common import InfoExtractor


class LemondeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?lemonde\.fr/(?:[^/]+/)*(?P<id>[^/]+)\.html'
    _TESTS = [{
        'url': 'http://www.lemonde.fr/police-justice/video/2016/01/19/comprendre-l-affaire-bygmalion-en-cinq-minutes_4849702_1653578.html',
        'md5': '01fb3c92de4c12c573343d63e163d302',
        'info_dict': {
            'id': 'lqm3kl',
            'ext': 'mp4',
            'title': "Comprendre l'affaire Bygmalion en 5 minutes",
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 320,
            'upload_date': '20160119',
            'timestamp': 1453194778,
            'uploader_id': '3pmkp',
        },
    }, {
        'url': 'http://redaction.actu.lemonde.fr/societe/video/2016/01/18/calais-debut-des-travaux-de-defrichement-dans-la-jungle_4849233_3224.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        digiteka_url = self._proto_relative_url(self._search_regex(
            r'url\s*:\s*(["\'])(?P<url>(?:https?://)?//(?:www\.)?(?:digiteka\.net|ultimedia\.com)/deliver/.+?)\1',
            webpage, 'digiteka url', group='url'))
        return self.url_result(digiteka_url, 'Digiteka')
