# coding: utf-8
from __future__ import unicode_literals

from .common import (
    InfoExtractor,
    ExtractorError
)
from ..utils import (
    determine_ext,
    parse_duration,
    unified_strdate
)


class MediasetIE(InfoExtractor):
    _VALID_URL = r'https?://www\.video\.mediaset\.it/(?:(?:video|on-demand)/(?:.+)_|player/playerIFrame(?:Twitter)?\.shtml\?id=)(?P<id>[0-9]+)(?:.html|&.+)'
    _TESTS = [{
        # full episode
        'url': 'http://www.video.mediaset.it/video/hello_goodbye/full/quarta-puntata_661824.html',
        'md5': '9b75534d42c44ecef7bf1ffeacb7f85d',
        'info_dict': {
            'id': '661824',
            'ext': 'mp4',
            'title': 'Quarta puntata',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'md5:7183696d6df570e3412a5ef74b27c5e2',
            'uploader': 'mediaset'
        }
    }, {
        # on demand
        'url': 'http://www.video.mediaset.it/video/domenica_live/interviste/il-fenomeno-elettra-lamborghini_716283.html',
        'md5': '81c57566bf2ee02e995f5342f079ca25',
        'info_dict': {
            'id': '716283',
            'ext': 'mp4',
            'title': 'Il fenomeno Elettra Lamborghini',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'md5:dabf0e7cf48fc6d0a3417b989028748a',
            'uploader': 'mediaset'
        }
    }, {
        # clip
        'url': 'http://www.video.mediaset.it/video/gogglebox/clip/un-grande-classico-della-commedia-sexy_661680.html',
        'md5': '189ca72fe399db80dbfa595a4abf42d0',
        'info_dict': {
            'id': '661680',
            'ext': 'mp4',
            'title': 'Un grande classico della commedia sexy',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'Un film che riesce a risvegliare i sensi di Gigi.',
            'uploader': 'mediaset'
        }
    }, {
        # iframe simple
        'url': 'http://www.video.mediaset.it/player/playerIFrame.shtml?id=665924&autoplay=true',
        'md5': '308430901e55e1ad83dddb4be2a4454a',
        'info_dict': {
            'id': '665924',
            'ext': 'mp4',
            'title': 'Gianna Nannini incontra i fan a Milano',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'La cantante parla del nuovo libro',
            'uploader': 'mediaset'
        }
    }, {
        # iframe twitter (from http://www.wittytv.it/se-prima-mi-fidavo-zero/)
        'url': 'https://www.video.mediaset.it/player/playerIFrameTwitter.shtml?id=665104&playrelated=false&autoplay=false&related=true&hidesocial=true',
        'md5': '6f53a834b3b5eac1ebc2037ccf7194d0',
        'info_dict': {
            'id': '665104',
            'ext': 'mp4',
            'title': '\"Se prima mi fidavo zero...\"',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'Una piccola anteprima della prossima puntata del Trono Classico',
            'uploader': 'mediaset'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        formats = []
        uploader = None
        categories = None

        mediainfo = self._download_json(
            'http://plr.video.mediaset.it/html/metainfo.sjson?id=%s' % video_id,
            video_id, 'Downloading video info JSON').get('video')

        if 'brand-info' in mediainfo:
            uploader = mediainfo.get('brand-info').get('publisher')
            categories = [mediainfo.get('brand-info').get('category')]

        cnd = self._download_json(
            'http://cdnsel01.mediaset.net/GetCdn.aspx?streamid=%s&format=json' % video_id,
            video_id, 'Downloading video CND JSON')

        if not cnd.get('videoList'):
            raise ExtractorError('Video not found')

        for media_url in cnd.get('videoList'):
            formats.append({
                'url': media_url,
                'ext': determine_ext(media_url)
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': mediainfo.get('title'),
            'formats': formats,
            'description': mediainfo.get('short-description'),
            'uploader': uploader,
            'thumbnail': mediainfo.get('thumbnail'),
            'duration': parse_duration(mediainfo.get('duration')),
            'release_date': unified_strdate(mediainfo.get('production-date')),
            'webpage_url': mediainfo.get('url'),
            'categories': categories
        }
