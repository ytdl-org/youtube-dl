from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json


class StOlafIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?stolaf\.edu/multimedia/play/\?e=(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.stolaf.edu/multimedia/play/?e=573',
        'info_dict': {
            'id': '573',
            'ext': 'mp4',
            'title': 'Senior Soloists Concert',
            'description': 'St. Olaf Orchestra & Senior Soloists',
            'thumbnail': 'http://www.stolaf.edu/multimedia/components/poster/e573',
        },
        'params': {
            'skip_download': True, # because m3u8
        },
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        title = self._og_search_property('title', webpage)
        description = self._og_search_property('description', webpage)

        javascript = self._download_webpage(
            'http://www.stolaf.edu/multimedia/components/eventlib.cfc',
            playlist_id, 'Downloading playlist #%u' % (3),
            query={
                'method': 'getPlayerPlaylist',
                'eventtype': 'e',
                'eventid': playlist_id,
                # param below selects quality of the m3u8 stream; any floating-point
                # constant is accepted, but values above 3 are clamped. only
                # 1, 2 and 3 seem to give actual streams, though.
                # XXX: request all three? or transform the URL locally?
                'html5stream': 3
            })
        thePlaylist = self._parse_json(
            self._search_regex(r'(?s)thePlaylist\s*=\s*(\[.*?\]);', javascript, 'thePlaylist'),
            playlist_id, transform_source=js_to_json)
        token = self._search_regex(r'n7kIjJed73\s*=\s*\'(.*?)\';', javascript, 'token')

        entries = []
        for (i, item) in enumerate(thePlaylist):
            video_id = '%s-%u' % (playlist_id, i)
            formats = []
            for (j, source) in enumerate(item['sources']):
                if source.get('type') == 'rtmp':
                    formats.extend(self._extract_smil_formats('//stolaf.edu' + source['file'], video_id, rtmp_securetoken=token))
                else:
                    formats.extend(self._extract_m3u8_formats(source['file'], video_id, 'mp4'))

            entries.append({
                'id': video_id,
                'title': title,
                'description': description,
                'formats': formats,
                'thumbnail': item.get('image'),
            })

        if len(entries) == 1:
            result = entries[0]
            result['id'] = playlist_id
            return result

        return {
            '_type': 'multi_video',
            'id': playlist_id,
            'title': title,
            'description': description,
            'entries': entries,
        }
