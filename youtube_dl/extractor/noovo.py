# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import ExtractorError


class NoovoIE(InfoExtractor):

    _VALID_URL = r'https?://(?:[a-z0-9\-]+\.)?noovo\.ca/videos/(?P<id>[a-z0-9\-]+/[a-z0-9\-]+)'

    _TESTS = [{
        'url': 'http://noovo.ca/videos/rpm-plus/chrysler-imperial',
        'md5': '2fcc04d0a8f4a853fad91233c2fdd121',
        'info_dict': {
            'id': '5386045029001',
            'description': 'Antoine présente des véhicules qu\'il aperçoit sur la rue.',
            'ext': 'mp4',
            'timestamp': 1491399228,
            'title': 'Chrysler Imperial',
            'upload_date': '20170405',
            'uploader_id': '618566855001'
        }
    }, {
        'url': 'http://interventions.noovo.ca/911/video/intoxication-aux-drogues-dures/?autoplay=1',
        'md5': '0ca96cef6d6b3a3a4836a05936964da4',
        'info_dict': {
            'id': '5397570276001',
            'description': 'md5:573bb7da6ffbfa310e2ebab88688e5ad',
            'ext': 'mp4',
            'timestamp': 1492112546,
            'title': 'md5:5015fe58f797e58abdda1c6711530405',
            'upload_date': '20170413',
            'uploader_id': '618566855001'
        }
    }]

    TEMPLATE_API_URL = 'http://api.noovo.ca/api/v1/pages/single-episode/%s'

    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/618566855001/default_default/index.html?videoId=%s'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_url = self.TEMPLATE_API_URL % video_id

        api_content = self._download_webpage(api_url, video_id)

        brightcove_id = self._search_regex(
            r'"?brightcoveId"?\s*:\s*"?(\d+)', api_content, 'brightcove id'
        )

        if brightcove_id:
            return self.url_result(
                self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id, 'BrightcoveNew', brightcove_id
            )
        else:
            raise ExtractorError('Unable to extract brightcove id from api')
