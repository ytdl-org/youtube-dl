# coding: utf-8
from __future__ import unicode_literals

from .. import utils
from .common import InfoExtractor


class IndavideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?indavideo\.hu/video/(?P<id>.+)'
    _TESTS = [
        {
            'url': 'http://indavideo.hu/video/Cicatanc',
            'md5': 'c8a507a1c7410685f83a06eaeeaafeab',
            'info_dict': {
                'id': '1837039',
                'title': 'Cicatánc',
                'ext': 'mp4',
                'display_id': 'Cicatanc',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': '',
                'uploader': 'cukiajanlo',
                'uploader_id': '83729',
                'duration': 72,
                'age_limit': 0,
                'tags': ['tánc', 'cica', 'cuki', 'cukiajanlo', 'newsroom']
            },
        },
        {
            'url': 'http://indavideo.hu/video/Vicces_cica_1',
            'md5': '8c82244ba85d2a2310275b318eb51eac',
            'info_dict': {
                'id': '1335611',
                'title': 'Vicces cica',
                'ext': 'mp4',
                'display_id': 'Vicces_cica_1',
                'thumbnail': 're:^https?://.*\.jpg$',
                'description': 'Játszik a tablettel. :D',
                'uploader': 'Jet_Pack',
                'uploader_id': '491217',
                'duration': 7,
                'age_limit': 0,
                'tags': ['vicces', 'macska', 'cica', 'ügyes', 'nevetés', 'játszik', 'Cukiság', 'Jet_Pack'],
            },
        },
    ]

    def _real_extract(self, url):
        video_disp_id = self._match_id(url)
        webpage = self._download_webpage(url, video_disp_id)

        embed_url = self._html_search_regex(r'<link rel="video_src" href="(.+?)"/>', webpage, 'embed_url')
        video_hash = embed_url.split('/')[-1]

        payload = self._download_json('http://amfphp.indavideo.hu/SYm0json.php/player.playerHandler.getVideoData/' + video_hash, video_disp_id)
        video_info = payload['data']

        thumbnails = video_info.get('thumbnails')
        if thumbnails:
            thumbnails = [{'url': self._proto_relative_url(x)} for x in thumbnails]

        tags = video_info.get('tags')
        if tags:
            tags = [x['title'] for x in tags]

        return {
            'id': video_info.get('id'),
            'title': video_info['title'],
            'url': video_info['video_file'],
            'ext': 'mp4',
            'display_id': video_disp_id,
            'thumbnails': thumbnails,
            'description': video_info.get('description'),
            'uploader': video_info.get('user_name'),
            # TODO: upload date (it's in CET/CEST)
            'uploader_id': video_info.get('user_id'),
            'duration': utils.int_or_none(video_info.get('length')),
            'age_limit': utils.int_or_none(video_info.get('age_limit')),
            'tags': tags,
        }
