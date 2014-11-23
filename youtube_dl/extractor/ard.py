# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE
from ..utils import (
    determine_ext,
    ExtractorError,
    qualities,
    int_or_none,
    parse_duration,
    unified_strdate,
    xpath_text,
    parse_xml,
)


class ARDMediathekIE(InfoExtractor):
    IE_NAME = 'ARD:mediathek'
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

        webpage = self._download_webpage(url, video_id)

        if '>Der gewünschte Beitrag ist nicht mehr verfügbar.<' in webpage:
            raise ExtractorError('Video %s is no longer available' % video_id, expected=True)

        if re.search(r'[\?&]rss($|[=&])', url):
            doc = parse_xml(webpage)
            if doc.tag == 'rss':
                return GenericIE()._extract_rss(url, video_id, doc)

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


class ARDIE(InfoExtractor):
    _VALID_URL = '(?P<mainurl>https?://(www\.)?daserste\.de/[^?#]+/videos/(?P<display_id>[^/?#]+)-(?P<id>[0-9]+))\.html'
    _TEST = {
        'url': 'http://www.daserste.de/information/reportage-dokumentation/dokus/videos/die-story-im-ersten-mission-unter-falscher-flagge-100.html',
        'md5': 'd216c3a86493f9322545e045ddc3eb35',
        'info_dict': {
            'display_id': 'die-story-im-ersten-mission-unter-falscher-flagge',
            'id': '100',
            'ext': 'mp4',
            'duration': 2600,
            'title': 'Die Story im Ersten: Mission unter falscher Flagge',
            'upload_date': '20140804',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        player_url = mobj.group('mainurl') + '~playerXml.xml'
        doc = self._download_xml(player_url, display_id)
        video_node = doc.find('./video')
        upload_date = unified_strdate(xpath_text(
            video_node, './broadcastDate'))
        thumbnail = xpath_text(video_node, './/teaserImage//variant/url')

        formats = []
        for a in video_node.findall('.//asset'):
            f = {
                'format_id': a.attrib['type'],
                'width': int_or_none(a.find('./frameWidth').text),
                'height': int_or_none(a.find('./frameHeight').text),
                'vbr': int_or_none(a.find('./bitrateVideo').text),
                'abr': int_or_none(a.find('./bitrateAudio').text),
                'vcodec': a.find('./codecVideo').text,
                'tbr': int_or_none(a.find('./totalBitrate').text),
            }
            if a.find('./serverPrefix').text:
                f['url'] = a.find('./serverPrefix').text
                f['playpath'] = a.find('./fileName').text
            else:
                f['url'] = a.find('./fileName').text
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': mobj.group('id'),
            'formats': formats,
            'display_id': display_id,
            'title': video_node.find('./title').text,
            'duration': parse_duration(video_node.find('./duration').text),
            'upload_date': upload_date,
            'thumbnail': thumbnail,
        }
