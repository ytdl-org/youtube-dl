# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
)


class ARDIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:(?:www\.)?ardmediathek\.de|mediathek\.daserste\.de)/(?:.*/)(?P<video_id>[^/\?]+)(?:\?.*)?'

    _TEST = {
        'url': 'http://www.ardmediathek.de/das-erste/guenther-jauch/edward-snowden-im-interview-held-oder-verraeter?documentId=19288786',
        'file': '19288786.mp4',
        'md5': '515bf47ce209fb3f5a61b7aad364634c',
        'info_dict': {
            'title': 'Edward Snowden im Interview - Held oder Verräter?',
            'description': 'Edward Snowden hat alles aufs Spiel gesetzt, um die weltweite \xdcberwachung durch die Geheimdienste zu enttarnen. Nun stellt sich der ehemalige NSA-Mitarbeiter erstmals weltweit in einem TV-Interview den Fragen eines NDR-Journalisten. Die Sendung vom Sonntagabend.',
            'thumbnail': 'http://www.ardmediathek.de/ard/servlet/contentblob/19/28/87/90/19288790/bild/2250037',
        },
        'skip': 'Blocked outside of Germany',
    }

    def _real_extract(self, url):
        # determine video id from url
        m = re.match(self._VALID_URL, url)

        numid = re.search(r'documentId=([0-9]+)', url)
        if numid:
            video_id = numid.group(1)
        else:
            video_id = m.group('video_id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            [r'<h1(?:\s+class="boxTopHeadline")?>(.*?)</h1>',
             r'<meta name="dcterms.title" content="(.*?)"/>',
             r'<h4 class="headline">(.*?)</h4>'],
            webpage, 'title')
        description = self._html_search_meta(
            'dcterms.abstract', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage)


        media_info = self._download_json(
            'http://www.ardmediathek.de/play/media/%s' % video_id, video_id)
        # The second element of the _mediaArray contains the standard http urls
        streams = media_info['_mediaArray'][1]['_mediaStreamArray']
        if not streams:
            if '"fsk"' in webpage:
                raise ExtractorError('This video is only available after 20:00')

        formats = []

        for s in streams:
            if type(s['_stream']) == list:
                for index, url in enumerate(s['_stream'][::-1]):
                    quality = s['_quality'] + index
                    formats.append({
                        'quality': quality,
                        'url': url,
                        'format_id': '%s-%s' % (determine_ext(url), quality)
                        })
                continue

            format = {
                'quality': s['_quality'],
                'url': s['_stream'],
            }

            format['format_id'] = '%s-%s' % (
                determine_ext(format['url']), format['quality'])

            formats.append(format)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'thumbnail': thumbnail,
        }
