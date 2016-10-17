# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE
from ..utils import (
    determine_ext,
    ExtractorError,
    get_element_by_attribute,
    qualities,
    int_or_none,
    parse_duration,
    unified_strdate,
    xpath_text,
)
from ..compat import compat_etree_fromstring


class ARDMediathekIE(InfoExtractor):
    IE_NAME = 'ARD:mediathek'
    _VALID_URL = r'^https?://(?:(?:www\.)?ardmediathek\.de|mediathek\.daserste\.de)/(?:.*/)(?P<video_id>[0-9]+|[^0-9][^/\?]+)[^/\?]*(?:\?.*)?'

    _TESTS = [{
        'url': 'http://www.ardmediathek.de/tv/Dokumentation-und-Reportage/Ich-liebe-das-Leben-trotzdem/rbb-Fernsehen/Video?documentId=29582122&bcastId=3822114',
        'info_dict': {
            'id': '29582122',
            'ext': 'mp4',
            'title': 'Ich liebe das Leben trotzdem',
            'description': 'md5:45e4c225c72b27993314b31a84a5261c',
            'duration': 4557,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.ardmediathek.de/tv/Tatort/Tatort-Scheinwelten-H%C3%B6rfassung-Video/Das-Erste/Video?documentId=29522730&bcastId=602916',
        'md5': 'f4d98b10759ac06c0072bbcd1f0b9e3e',
        'info_dict': {
            'id': '29522730',
            'ext': 'mp4',
            'title': 'Tatort: Scheinwelten - Hörfassung (Video tgl. ab 20 Uhr)',
            'description': 'md5:196392e79876d0ac94c94e8cdb2875f1',
            'duration': 5252,
        },
    }, {
        # audio
        'url': 'http://www.ardmediathek.de/tv/WDR-H%C3%B6rspiel-Speicher/Tod-eines-Fu%C3%9Fballers/WDR-3/Audio-Podcast?documentId=28488308&bcastId=23074086',
        'md5': '219d94d8980b4f538c7fcb0865eb7f2c',
        'info_dict': {
            'id': '28488308',
            'ext': 'mp3',
            'title': 'Tod eines Fußballers',
            'description': 'md5:f6e39f3461f0e1f54bfa48c8875c86ef',
            'duration': 3240,
        },
    }, {
        'url': 'http://mediathek.daserste.de/sendungen_a-z/328454_anne-will/22429276_vertrauen-ist-gut-spionieren-ist-besser-geht',
        'only_matching': True,
    }]

    def _extract_media_info(self, media_info_url, webpage, video_id):
        media_info = self._download_json(
            media_info_url, video_id, 'Downloading media JSON')

        formats = self._extract_formats(media_info, video_id)

        if not formats:
            if '"fsk"' in webpage:
                raise ExtractorError(
                    'This video is only available after 20:00', expected=True)
            elif media_info.get('_geoblocked'):
                raise ExtractorError('This video is not available due to geo restriction', expected=True)

        self._sort_formats(formats)

        duration = int_or_none(media_info.get('_duration'))
        thumbnail = media_info.get('_previewImage')

        subtitles = {}
        subtitle_url = media_info.get('_subtitleUrl')
        if subtitle_url:
            subtitles['de'] = [{
                'ext': 'ttml',
                'url': subtitle_url,
            }]

        return {
            'id': video_id,
            'duration': duration,
            'thumbnail': thumbnail,
            'formats': formats,
            'subtitles': subtitles,
        }

    def _extract_formats(self, media_info, video_id):
        type_ = media_info.get('_type')
        media_array = media_info.get('_mediaArray', [])
        formats = []
        for num, media in enumerate(media_array):
            for stream in media.get('_mediaStreamArray', []):
                stream_urls = stream.get('_stream')
                if not stream_urls:
                    continue
                if not isinstance(stream_urls, list):
                    stream_urls = [stream_urls]
                quality = stream.get('_quality')
                server = stream.get('_server')
                for stream_url in stream_urls:
                    ext = determine_ext(stream_url)
                    if quality != 'auto' and ext in ('f4m', 'm3u8'):
                        continue
                    if ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            stream_url + '?hdcore=3.1.1&plugin=aasp-3.1.1.69.124',
                            video_id, preference=-1, f4m_id='hds', fatal=False))
                    elif ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            stream_url, video_id, 'mp4', preference=1, m3u8_id='hls', fatal=False))
                    else:
                        if server and server.startswith('rtmp'):
                            f = {
                                'url': server,
                                'play_path': stream_url,
                                'format_id': 'a%s-rtmp-%s' % (num, quality),
                            }
                        elif stream_url.startswith('http'):
                            f = {
                                'url': stream_url,
                                'format_id': 'a%s-%s-%s' % (num, ext, quality)
                            }
                        else:
                            continue
                        m = re.search(r'_(?P<width>\d+)x(?P<height>\d+)\.mp4$', stream_url)
                        if m:
                            f.update({
                                'width': int(m.group('width')),
                                'height': int(m.group('height')),
                            })
                        if type_ == 'audio':
                            f['vcodec'] = 'none'
                        formats.append(f)
        return formats

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

        if 'Diese Sendung ist für Jugendliche unter 12 Jahren nicht geeignet. Der Clip ist deshalb nur von 20 bis 6 Uhr verfügbar.' in webpage:
            raise ExtractorError('This program is only suitable for those aged 12 and older. Video %s is therefore only available between 20 pm and 6 am.' % video_id, expected=True)

        if re.search(r'[\?&]rss($|[=&])', url):
            doc = compat_etree_fromstring(webpage.encode('utf-8'))
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
            self._sort_formats(formats)
            info = {
                'formats': formats,
            }
        else:  # request JSON file
            info = self._extract_media_info(
                'http://www.ardmediathek.de/play/media/%s' % video_id, webpage, video_id)

        info.update({
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        })

        return info


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


class SportschauIE(ARDMediathekIE):
    IE_NAME = 'Sportschau'
    _VALID_URL = r'(?P<baseurl>https?://(?:www\.)?sportschau\.de/(?:[^/]+/)+video(?P<id>[^/#?]+))\.html'
    _TESTS = [{
        'url': 'http://www.sportschau.de/tourdefrance/videoseppeltkokainhatnichtsmitklassischemdopingzutun100.html',
        'info_dict': {
            'id': 'seppeltkokainhatnichtsmitklassischemdopingzutun100',
            'ext': 'mp4',
            'title': 'Seppelt: "Kokain hat nichts mit klassischem Doping zu tun"',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'Der ARD-Doping Experte Hajo Seppelt gibt seine Einschätzung zum ersten Dopingfall der diesjährigen Tour de France um den Italiener Luca Paolini ab.',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        base_url = mobj.group('baseurl')

        webpage = self._download_webpage(url, video_id)
        title = get_element_by_attribute('class', 'headline', webpage)
        description = self._html_search_meta('description', webpage, 'description')

        info = self._extract_media_info(
            base_url + '-mc_defaultQuality-h.json', webpage, video_id)

        info.update({
            'title': title,
            'description': description,
        })

        return info
