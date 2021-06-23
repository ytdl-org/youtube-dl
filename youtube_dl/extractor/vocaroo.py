# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VocarooIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:vocaroo\.com|voca\.ro)/(?:embed/)?(?P<id>[a-zA-Z0-9]{12})'
    _TESTS = [
        {
            'url': 'https://vocaroo.com/1e976QE4oDoy',
            'md5': '9ccf2014af38890e9e10450c901c17a6',
            'info_dict': {
                'id': '1e976QE4oDoy',
                'ext': 'mp3',
                'title': 'Vocaroo - 1e976QE4oDoy',
            }
        },
        {
            'url': 'https://vocaroo.com/embed/1e976QE4oDoy?autoplay=0',
            'only_matching': True
        },
        {
            'url': 'https://voca.ro/1ctMANMty97s',
            'only_matching': True
        },
    ]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        return {
            'id': audio_id,
            'title': "Vocaroo - {}".format(audio_id),
            'url': 'https://media1.vocaroo.com/mp3/{}'.format(audio_id),
            'ext': 'mp3'
        }
