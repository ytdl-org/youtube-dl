from __future__ import unicode_literals

from .nuevo import NuevoBaseIE


class NonkTubeIE(NuevoBaseIE):
    _VALID_URL = r'https?://(?:www\.)?nonktube\.com/(?:(?:video|embed)/|media/nuevo/embed\.php\?.*?\bid=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.nonktube.com/video/118636/sensual-wife-uncensored-fucked-in-hairy-pussy-and-facialized',
        'info_dict': {
            'id': '118636',
            'ext': 'mp4',
            'title': 'Sensual Wife Uncensored Fucked In Hairy Pussy And Facialized',
            'age_limit': 18,
            'duration': 1150.98,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://www.nonktube.com/embed/118636',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._extract_nuevo(
            'https://www.nonktube.com/media/nuevo/econfig.php?key=%s'
            % video_id, video_id)

        info['age_limit'] = 18
        return info
