# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class KonserthusetPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?konserthusetplay\.se/\?m=(?P<id>[0-9A-Za-z_-]+)'

    _TESTS = [{
        'url': 'http://www.konserthusetplay.se/?m=CKDDnlCY-dhWAAqiMERd-A',
        'md5': 'e272a765e0d12a0226199e5f32d76116',
        'info_dict': {
            'id': 'CKDDnlCY-dhWAAqiMERd-A',
            'ext': 'mp4',
            'title': 'Orkesterns instrument: Valthornen',
            'description': 'md5:f10e1f0030202020396a4d712d2fa827',
            'thumbnail': 'http://csp.picsearch.com/img/C/K/D/D/title_CKDDnlCY-dhWAAqiMERd-A'
        }
    }, {
        'url': 'http://www.konserthusetplay.se/?m=IyQcMOEpmKqT91SVT5OP8Q',
        'md5': 'c4adb8ca76fdd33d4cbdcc7c3d181f22',
        'info_dict': {
            'id': 'IyQcMOEpmKqT91SVT5OP8Q',
            'ext': 'mp4',
            'title': 'Eliasson Einsame Fahrt, violinkonsert',
            'description': 'md5:a8dcc8dfd9473d52433b2c5f588ba191',
            'thumbnail': 'http://csp.picsearch.com/img/I/y/Q/c/title_IyQcMOEpmKqT91SVT5OP8Q'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        description = self._og_search_description(webpage)
        title = self._og_search_title(webpage)
        main_video = self._html_search_regex(r'<link rel="video_src" href="(.+?)" />', webpage, 'url')
        thumbnail = self._og_search_thumbnail(webpage)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'url': main_video,
            'thumbnail': thumbnail
        }
