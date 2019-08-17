# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE
from ..utils import (
    determine_ext,
    dict_get,
    ExtractorError,
    int_or_none,
    parse_duration,
    qualities,
    str_or_none,
    try_get,
    unified_strdate,
    unified_timestamp,
    update_url_query,
    url_or_none,
    url_basename,
    xpath_text,
)
from ..compat import compat_etree_fromstring


class ARDMediathekIE(InfoExtractor):
    IE_NAME = 'ARD:mediathek'
    _VALID_URL = r'^https?://(?:(?:(?:www|classic)\.)?ardmediathek\.de|mediathek\.(?:daserste|rbb-online)\.de|one\.ard\.de)/(?:.*/)(?P<video_id>[0-9]+|[^0-9][^/\?]+)[^/\?]*(?:\?.*)?'

    _TESTS = [{
        # available till 26.07.2022
        'url': 'http://www.ardmediathek.de/tv/S%C3%9CDLICHT/Was-ist-die-Kunst-der-Zukunft-liebe-Ann/BR-Fernsehen/Video?bcastId=34633636&documentId=44726822',
        'info_dict': {
            'id': '44726822',
            'ext': 'mp4',
            'title': 'Was ist die Kunst der Zukunft, liebe Anna McCarthy?',
            'description': 'md5:4ada28b3e3b5df01647310e41f3a62f5',
            'duration': 1740,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }, {
        'url': 'https://one.ard.de/tv/Mord-mit-Aussicht/Mord-mit-Aussicht-6-39-T%C3%B6dliche-Nach/ONE/Video?bcastId=46384294&documentId=55586872',
        'only_matching': True,
    }, {
        # audio
        'url': 'http://www.ardmediathek.de/tv/WDR-H%C3%B6rspiel-Speicher/Tod-eines-Fu%C3%9Fballers/WDR-3/Audio-Podcast?documentId=28488308&bcastId=23074086',
        'only_matching': True,
    }, {
        'url': 'http://mediathek.daserste.de/sendungen_a-z/328454_anne-will/22429276_vertrauen-ist-gut-spionieren-ist-besser-geht',
        'only_matching': True,
    }, {
        # audio
        'url': 'http://mediathek.rbb-online.de/radio/Hörspiel/Vor-dem-Fest/kulturradio/Audio?documentId=30796318&topRessort=radio&bcastId=9839158',
        'only_matching': True,
    }, {
        'url': 'https://classic.ardmediathek.de/tv/Panda-Gorilla-Co/Panda-Gorilla-Co-Folge-274/Das-Erste/Video?bcastId=16355486&documentId=58234698',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if ARDBetaMediathekIE.suitable(url) else super(ARDMediathekIE, cls).suitable(url)

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
        is_live = media_info.get('_isLive') is True

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
            'is_live': is_live,
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
                    if not url_or_none(stream_url):
                        continue
                    ext = determine_ext(stream_url)
                    if quality != 'auto' and ext in ('f4m', 'm3u8'):
                        continue
                    if ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            update_url_query(stream_url, {
                                'hdcore': '3.1.1',
                                'plugin': 'aasp-3.1.1.69.124'
                            }),
                            video_id, f4m_id='hds', fatal=False))
                    elif ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            stream_url, video_id, 'mp4', m3u8_id='hls', fatal=False))
                    else:
                        if server and server.startswith('rtmp'):
                            f = {
                                'url': server,
                                'play_path': stream_url,
                                'format_id': 'a%s-rtmp-%s' % (num, quality),
                            }
                        else:
                            f = {
                                'url': stream_url,
                                'format_id': 'a%s-%s-%s' % (num, ext, quality)
                            }
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

        document_id = None

        numid = re.search(r'documentId=([0-9]+)', url)
        if numid:
            document_id = video_id = numid.group(1)
        else:
            video_id = m.group('video_id')

        webpage = self._download_webpage(url, video_id)

        ERRORS = (
            ('>Leider liegt eine Störung vor.', 'Video %s is unavailable'),
            ('>Der gewünschte Beitrag ist nicht mehr verfügbar.<',
             'Video %s is no longer available'),
        )

        for pattern, message in ERRORS:
            if pattern in webpage:
                raise ExtractorError(message % video_id, expected=True)

        if re.search(r'[\?&]rss($|[=&])', url):
            doc = compat_etree_fromstring(webpage.encode('utf-8'))
            if doc.tag == 'rss':
                return GenericIE()._extract_rss(url, video_id, doc)

        title = self._html_search_regex(
            [r'<h1(?:\s+class="boxTopHeadline")?>(.*?)</h1>',
             r'<meta name="dcterms\.title" content="(.*?)"/>',
             r'<h4 class="headline">(.*?)</h4>',
             r'<title[^>]*>(.*?)</title>'],
            webpage, 'title')
        description = self._html_search_meta(
            'dcterms.abstract', webpage, 'description', default=None)
        if description is None:
            description = self._html_search_meta(
                'description', webpage, 'meta description', default=None)
        if description is None:
            description = self._html_search_regex(
                r'<p\s+class="teasertext">(.+?)</p>',
                webpage, 'teaser text', default=None)

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
            if not document_id:
                video_id = self._search_regex(
                    r'/play/(?:config|media)/(\d+)', webpage, 'media id')
            info = self._extract_media_info(
                'http://www.ardmediathek.de/play/media/%s' % video_id,
                webpage, video_id)

        info.update({
            'id': video_id,
            'title': self._live_title(title) if info.get('is_live') else title,
            'description': description,
            'thumbnail': thumbnail,
        })

        return info


class ARDIE(InfoExtractor):
    _VALID_URL = r'(?P<mainurl>https?://(www\.)?daserste\.de/[^?#]+/videos/(?P<display_id>[^/?#]+)-(?P<id>[0-9]+))\.html'
    _TESTS = [{
        # available till 14.02.2019
        'url': 'http://www.daserste.de/information/talk/maischberger/videos/das-groko-drama-zerlegen-sich-die-volksparteien-video-102.html',
        'md5': '8e4ec85f31be7c7fc08a26cdbc5a1f49',
        'info_dict': {
            'display_id': 'das-groko-drama-zerlegen-sich-die-volksparteien-video',
            'id': '102',
            'ext': 'mp4',
            'duration': 4435.0,
            'title': 'Das GroKo-Drama: Zerlegen sich die Volksparteien?',
            'upload_date': '20180214',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://www.daserste.de/information/reportage-dokumentation/dokus/videos/die-story-im-ersten-mission-unter-falscher-flagge-100.html',
        'only_matching': True,
    }]

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


class ARDBetaMediathekIE(InfoExtractor):
    _VALID_URL = r'https://(?:beta|www)\.ardmediathek\.de/[^/]+/(?:player|live)/(?P<video_id>[a-zA-Z0-9]+)(?:/(?P<display_id>[^/?#]+))?'
    _TESTS = [{
        'url': 'https://beta.ardmediathek.de/ard/player/Y3JpZDovL2Rhc2Vyc3RlLmRlL3RhdG9ydC9mYmM4NGM1NC0xNzU4LTRmZGYtYWFhZS0wYzcyZTIxNGEyMDE/die-robuste-roswita',
        'md5': '2d02d996156ea3c397cfc5036b5d7f8f',
        'info_dict': {
            'display_id': 'die-robuste-roswita',
            'id': 'Y3JpZDovL2Rhc2Vyc3RlLmRlL3RhdG9ydC9mYmM4NGM1NC0xNzU4LTRmZGYtYWFhZS0wYzcyZTIxNGEyMDE',
            'title': 'Tatort: Die robuste Roswita',
            'description': r're:^Der Mord.*trüber ist als die Ilm.',
            'duration': 5316,
            'thumbnail': 'https://img.ardmediathek.de/standard/00/55/43/59/34/-1774185891/16x9/960?mandant=ard',
            'upload_date': '20180826',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://www.ardmediathek.de/ard/player/Y3JpZDovL3N3ci5kZS9hZXgvbzEwNzE5MTU/',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/swr/live/Y3JpZDovL3N3ci5kZS8xMzQ4MTA0Mg',
        'only_matching': True,
    }]

    _format_url_templates = [
        # Das Erste
        {
            'pattern': r'^.+/(?P<width>\d+)-[^/]+_[^/]+\..{3,4}$',
            'format_id_suffix': 'width',
        },

        # SWR / SR / NDR
        {
            'pattern': r'^.+/[^/]+\.(?P<width_key>[a-z]+)\..{3,4}$',
            'format_id_suffix': 'width_key',
            'width_dict': {
                # SWR / SR
                'xxl': 1920,
                'xl': 1280,
                'l': 960,
                'ml': 640,
                'm': 512,
                'sm': 480,
                's': 320,

                # NDR
                'hd': 1280,
                'hq': 960,
                'ln': 640,
                'hi': 512,
                'mn': 480,
                'lo': 320,
            },
        },

        # BR / ARD-alpha / SR
        {
            'pattern': r'^.+/[^/]+_(?P<width_key>[A-Z0-9])\..{3,4}$',
            'format_id_suffix': 'width_key',
            'width_dict': {
                # BR, ARD-alpha
                'X': 1280,
                'C': 960,
                'E': 640,
                'B': 512,
                '2': 480,
                'A': 480,
                '0': 320,

                # SR
                'P': 1280,
                'L': 960,
                'N': 640,
                'M': 512,
                'K': 480,
                'S': 320,
            },
        },

        # HR
        {
            'pattern': r'^.+/[^/]+?(?P<width>[0-9]+)x(?P<height>[0-9]+)-(?P<fps>[0-9]+)[pi]-(?P<tbr>[0-9]+)kbit\..{3,4}$',
            'format_id_suffix': 'tbr',
        },

        # Radio Bremen
        {
            'pattern': r'^.+/[^/]+_(?P<height>\d+)p\..{3,4}$',
            'format_id_suffix': 'height',
        },

        # RBB
        {
            'pattern': r'^.+/[^/]+_(?P<vbr>\d+)k\..{3,4}$',
            'format_id_suffix': 'vbr',
        },

        # tagesschau24
        {
            'pattern': r'^.+/[^/]+\.(?P<width_key>[a-z]+)\.[^/]+\..{3,4}$',
            'format_id_suffix': 'width_key',
            'width_dict': {
                'webxl': 1280,
                'webl': 960,
                'webml': 640,
                'webm': 512,
                'websm': 480,
                'webs': 256,
            },
        },

        # MDR
        {
            'pattern': r'^.+/[^/]+-(?P<width_key>[a-z0-9]+)_[^/]+\..{3,4}$',
            'format_id_suffix': 'width_key',
            'width_dict': {
                'be7c2950aac6': 1280,
                '730aae549c28': 960,
                '41dd60577440': 640,
                '9a4bb04739be': 512,
                '39c393010ca9': 480,
                'd1ceaa57a495': 320,
            },
        },

        # TODO Find out format data for videos from WDR and ONE.
    ]

    def _get_format_from_url(self, format_url, quality):
        """Extract as much format data from the format_url as possible.

        Use the templates listed in _format_url_templates to do so.
        """

        result = {
            'url': format_url,
            'preference': 10,  # Plain HTTP, that's nice
        }

        format_id_suffix = None

        for template in self._format_url_templates:
            m = re.match(template['pattern'], format_url)
            if m:
                groupdict = m.groupdict()
                result['width'] = int_or_none(groupdict.get('width'))
                result['height'] = int_or_none(groupdict.get('height'))
                result['fps'] = int_or_none(groupdict.get('fps'))
                result['tbr'] = int_or_none(groupdict.get('tbr'))
                result['vbr'] = int_or_none(groupdict.get('vbr'))

                width_dict = template.get('width_dict')
                if width_dict:
                    result['width'] = width_dict.get(groupdict.get('width_key'))

                format_id_suffix = groupdict.get(template.get('format_id_suffix'))
                break

        if result.get('width') and not result.get('height'):
            result['height'] = int((result['width'] / 16) * 9)

        if result.get('height') and not result.get('width'):
            result['width'] = int((result['height'] / 9) * 16)

        result['format_id'] = (('http-' + quality) if quality else 'http') + ('-' + format_id_suffix if format_id_suffix else '')

        return result


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)
        data_json = self._search_regex(r'window\.__APOLLO_STATE__\s*=\s*(\{.*);\n', webpage, 'json')
        data = self._parse_json(data_json, display_id)

        res = {
            'id': video_id,
            'display_id': display_id,
        }
        formats = []
        subtitles = {}
        geoblocked = False
        blocked_by_fsk = False
        for widget in data.values():
            if widget.get('_geoblocked') is True:
                geoblocked = True
            if widget.get('blockedByFsk') is True:
                blocked_by_fsk = True
            if '_duration' in widget:
                res['duration'] = int_or_none(widget['_duration'])
            if 'clipTitle' in widget:
                res['title'] = widget['clipTitle']
            if '_previewImage' in widget:
                res['thumbnail'] = widget['_previewImage']
            if 'broadcastedOn' in widget:
                res['timestamp'] = unified_timestamp(widget['broadcastedOn'])
            if 'synopsis' in widget:
                res['description'] = widget['synopsis']
            if 'maturityContentRating' in widget:
                fsk_str = str_or_none(widget['maturityContentRating'])
                if fsk_str:
                    m = re.match(r'(?:FSK|fsk|Fsk)(\d+)', fsk_str)
                    if m and m.group(1):
                        res['age_limit'] = int_or_none(m.group(1))
                    else:
                        res['age_limit'] = 0

            subtitle_url = url_or_none(widget.get('_subtitleUrl'))
            if subtitle_url:
                subtitles.setdefault('de', []).append({
                    'ext': 'ttml',
                    'url': subtitle_url,
                })
            if '_quality' in widget:
                # Read format URLs from a MediaStreamArray
                stream_array = try_get(widget,
                                       lambda x: x['_stream']['json'])
                if not stream_array:
                    continue

                for format_url in stream_array:
                    format_url = url_or_none(format_url)
                    if not format_url:
                        continue

                    # Make sure this format isn't already in our list.
                    # Occassionally, there are duplicate files from
                    # different servers.
                    duplicate = next((x for x in formats
                        if url_basename(x['url']) == url_basename(format_url)), None)
                    if duplicate:
                        continue

                    ext = determine_ext(format_url)
                    if ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            format_url + '?hdcore=3.11.0',
                            video_id, f4m_id='hds', fatal=False))
                    elif ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            format_url, video_id, 'mp4', m3u8_id='hls',
                            fatal=False))
                    else:
                        quality = str_or_none(widget.get('_quality'))
                        formats.append(self._get_format_from_url(format_url, quality))

        if not formats and geoblocked:
            self.raise_geo_restricted(
                msg='This video is not available due to geoblocking',
                countries=['DE'])

        if not formats and blocked_by_fsk:
            raise ExtractorError(
                msg = 'This video is currently not available due to age restrictions (FSK %d). Try again from %02d:00 to 06:00.' % (res['age_limit'], 22 if res['age_limit'] < 18 else 23),
                expected = True)

        self._sort_formats(formats)
        res.update({
            'subtitles': subtitles,
            'formats': formats,
        })

        return res
