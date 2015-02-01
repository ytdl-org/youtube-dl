from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
)


class LA7IE(InfoExtractor):
    IE_NAME = 'la7.tv'
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?la7\.tv/
        (?:
            richplayer/\?assetid=|
            \?contentId=
        )
        (?P<id>[0-9]+)'''

    _TEST = {
        'url': 'http://www.la7.tv/richplayer/?assetid=50355319',
        'md5': 'ec7d1f0224d20ba293ab56cf2259651f',
        'info_dict': {
            'id': '50355319',
            'ext': 'mp4',
            'title': 'IL DIVO',
            'description': 'Un film di Paolo Sorrentino con Toni Servillo, Anna Bonaiuto, Giulio Bosetti  e Flavio Bucci',
            'duration': 6254,
        },
        'skip': 'Blocked in the US',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        xml_url = 'http://www.la7.tv/repliche/content/index.php?contentId=%s' % video_id
        doc = self._download_xml(xml_url, video_id)

        video_title = doc.find('title').text
        description = doc.find('description').text
        duration = parse_duration(doc.find('duration').text)
        thumbnail = doc.find('img').text
        view_count = int(doc.find('views').text)

        prefix = doc.find('.//fqdn').text.strip().replace('auto:', 'http:')

        formats = [{
            'format': vnode.find('quality').text,
            'tbr': int(vnode.find('quality').text),
            'url': vnode.find('fms').text.strip().replace('mp4:', prefix),
        } for vnode in doc.findall('.//videos/video')]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
            'view_count': view_count,
        }
