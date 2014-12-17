# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    js_to_json,
    unescapeHTML
)


class DVTVIE(InfoExtractor):
    IE_NAME = 'dvtv'
    IE_DESC = 'http://video.aktualne.cz/dvtv/'

    _VALID_URL = r'http://video\.aktualne\.cz/dvtv/(?P<id>[a-z0-9-]+/r~[0-9a-f]{32})/?'

    _TESTS = [{
        'url': 'http://video.aktualne.cz/dvtv/vondra-o-ceskem-stoleti-pri-pohledu-na-havla-mi-bylo-trapne/r~e5efe9ca855511e4833a0025900fea04/',
        'md5': '75800f964fa0f82939a2914563301f72',
        'info_dict': {
            'id': 'e5efe9ca855511e4833a0025900fea04',
            'ext': 'webm',
            'title': 'Vondra o Českém století: Při pohledu na Havla mi bylo trapně'
        }
    }, {
        'url': 'http://video.aktualne.cz/dvtv/stropnicky-policie-vrbetice-preventivne-nekontrolovala/r~82ed4322849211e4a10c0025900fea04/',
        'md5': '6388f1941b48537dbd28791f712af8bf',
        'info_dict': {
            'id': '82ed4322849211e4a10c0025900fea04',
            'ext': 'mp4',
            'title': 'Stropnický: Policie Vrbětice preventivně nekontrolovala'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        code = self._search_regex(
            r'(?s)embedData[0-9a-f]{32}\[\'asset\'\] = (\{.+?\});',
            webpage, 'video JSON')
        payload = self._parse_json(code, video_id, transform_source=js_to_json)
        formats = []
        for source in payload['sources']:
            ext = source['type'][6:]
            formats.append({
                'url': source['file'],
                'ext': ext,
                'format': '%s %s' % (ext, source['label']),
                'format_id': '%s-%s' % (ext, source['label']),
                'height': int(source['label'].rstrip('p')),
                'fps': 25,
            })
        self._sort_formats(formats)

        return {
            'id': video_id[-32:],
            'display_id': video_id[:-35],
            'title': unescapeHTML(payload['title']),
            'thumbnail': 'http:%s' % payload['image'],
            'formats': formats
        }
