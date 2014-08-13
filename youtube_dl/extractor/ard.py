# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    qualities,
    compat_urllib_parse_urlparse,
    compat_urllib_parse,
)


class ARDIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:(?:www\.)?ardmediathek\.de|mediathek\.daserste\.de)/(?:.*/)(?P<video_id>[0-9]+|[^0-9][^/\?]+)[^/\?]*(?:\?.*)?'

    _TESTS = [{
        'url': 'http://mediathek.daserste.de/sendungen_a-z/328454_anne-will/22429276_vertrauen-ist-gut-spionieren-ist-besser-geht',
        'file': '22429276.mp4',
        'md5': '469751912f1de0816a9fc9df8336476c',
        'info_dict': {
            'title': 'Vertrauen ist gut, Spionieren ist besser - Geht so deutsch-amerikanische Freundschaft?',
            'description': 'Das Erste Mediathek [ARD]: Vertrauen ist gut, Spionieren ist besser - Geht so deutsch-amerikanische Freundschaft?, Anne Will, Über die Spionage-Affäre diskutieren Clemens Binninger, Katrin Göring-Eckardt, Georg Mascolo, Andrew B. Denison und Constanze Kurz.. Das Video zur Sendung Anne Will am Mittwoch, 16.07.2014',
        },
        'skip': 'Blocked outside of Germany',
    }, {
        'url': 'http://www.ardmediathek.de/tv/Tatort/Das-Wunder-von-Wolbeck-Video-tgl-ab-20/Das-Erste/Video?documentId=22490580&bcastId=602916',
        'info_dict': {
            'id': '22490580',
            'ext': 'mp4',
            'title': 'Das Wunder von Wolbeck (Video tgl. ab 20 Uhr)',
            'description': 'Auf einem restaurierten Hof bei Wolbeck wird der Heilpraktiker Raffael Lembeck eines morgens von seiner Frau Stella tot aufgefunden. Das Opfer war offensichtlich in seiner Praxis zu Fall gekommen und ist dann verblutet, erklärt Prof. Boerne am Tatort.',
        },
        'skip': 'Blocked outside of Germany',
    }]

    def _real_extract(self, url):
        # determine video id from url
        m = re.match(self._VALID_URL, url)

        numid = re.search(r'documentId=([0-9]+)', url)
        if numid:
            video_id = numid.group(1)
        else:
            video_id = m.group('video_id')

        urlp = compat_urllib_parse_urlparse(url)
        url = urlp._replace(path=compat_urllib_parse.quote(urlp.path.encode('utf-8'))).geturl()

        webpage = self._download_webpage(url, video_id)

        if '>Der gewünschte Beitrag ist nicht mehr verfügbar.<' in webpage:
            raise ExtractorError('Video %s is no longer available' % video_id, expected=True)

        title = self._html_search_regex(
            [r'<h1(?:\s+class="boxTopHeadline")?>(.*?)</h1>',
             r'<meta name="dcterms.title" content="(.*?)"/>',
             r'<h4 class="headline">(.*?)</h4>'],
            webpage, 'title')
        description = self._html_search_meta(
            'dcterms.abstract', webpage, 'description', default=None)
        if description is None:
            description = self._html_search_meta(
                'description', webpage, 'meta description')

        # Thumbnail is sometimes not present.
        # It is in the mobile version, but that seems to use a different URL
        # structure altogether.
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        media_streams = re.findall(r'''(?x)
            mediaCollection\.addMediaStream\([0-9]+,\s*[0-9]+,\s*"[^"]*",\s*
            "([^"]+)"''', webpage)

        if media_streams:
            QUALITIES = qualities(['lo', 'hi', 'hq'])
            formats = []
            for furl in set(media_streams):
                if furl.endswith('.f4m'):
                    fid = 'f4m'
                else:
                    fid_m = re.match(r'.*\.([^.]+)\.[^.]+$', furl)
                    fid = fid_m.group(1) if fid_m else None
                formats.append({
                    'quality': QUALITIES(fid),
                    'format_id': fid,
                    'url': furl,
                })
        else:  # request JSON file
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
