# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE
from ..utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    orderedSet,
    parse_duration,
    qualities,
    str_or_none,
    unified_strdate,
    unified_timestamp,
    update_url_query,
    url_or_none,
    url_basename,
    xpath_text,
)
from ..compat import (
    compat_etree_fromstring,
    compat_urllib_parse_urlencode,
)


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


class ARDMediathekBaseIE(InfoExtractor):

    def _get_page(self, data):
        if not isinstance(data, dict):
            return None

        root = data.get('ROOT_QUERY')
        if isinstance(root, dict):
            for val in root.values():
                if (isinstance(val, dict) and
                        val.get('typename') == self._page_type):
                    return data.get(val.get('id'))
        else:
            root = data.get('data')
            if isinstance(root, dict):
                for val in root.values():
                    if (isinstance(val, dict) and
                            val.get('__typename') == self._page_type):
                        return val
        return None

    def _is_flag_set(self, data, flag):
        return self._get_elements_from_path(data, [flag])

    def _resolve_element(self, data, element):
        """Return the element either directly or linked by ID."""
        if element is None:
            return None

        if isinstance(element, dict) and element.get('type') == 'id':
            # This element refers to another element.
            # Retrieve the actual element.
            if not data:
                return None
            return data.get(element.get('id'))

        return element

    def _get_elements_from_path(self, data, path, parent=None):
        if parent is None:
            parent = self._get_page(data)

        if (not isinstance(parent, dict) or
                not isinstance(path, list) or
                len(path) == 0):
            return None

        element = self._resolve_element(data, parent.get(path[0]))
        res = element
        if isinstance(element, list):
            res = []
            for entry in element:
                entry = self._resolve_element(data, entry)
                if len(path[1:]) > 0:
                    res.append(self._get_elements_from_path(data,
                                                            path[1:],
                                                            entry))
                else:
                    res.append(entry)
        elif len(path[1:]) > 0:
            res = self._get_elements_from_path(data, path[1:], element)

        return res


class ARDBetaMediathekIE(ARDMediathekBaseIE):
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

    _page_type = "PlayerPage"

    _format_url_templates = [
        # Das Erste
        {
            'pattern': r'^.+/(?P<width>\d{1,4})-[^/]+_[^/]+\..{3,4}$',
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
            'pattern': r'^.+/[^/]+?(?P<width>[0-9]{1,4})x(?P<height>[0-9]{1,4})-(?P<fps>[0-9]{1,3})[pi]-(?P<tbr>[0-9]{1,5})kbit\..{3,4}$',
            'format_id_suffix': 'tbr',
        },

        # Radio Bremen
        {
            'pattern': r'^.+/[^/]+_(?P<height>\d{1,4})p\..{3,4}$',
            'format_id_suffix': 'height',
        },

        # RBB
        {
            'pattern': r'^.+/[^/]+_(?P<vbr>\d{1,5})k\..{3,4}$',
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
                # tagesschau24 uses a width of 256 instead of 320 for its
                # smallest videos
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

        # There is no format information in the URLs of videos from
        # WDR and ONE.
    ]

    def _extract_format_from_url(self, format_url, suffix, width_from_json_pos):
        """Extract as much format data from the format_url as possible.

        Use the templates listed in _format_url_templates to do so.
        """
        result = {
            'url': format_url,
            'width': width_from_json_pos,
            'preference': 10,  # Plain HTTP, that's nice
        }

        format_id_suffix = None

        for template in self._format_url_templates:
            m = re.match(template['pattern'], format_url)
            if m:
                groupdict = m.groupdict()
                result['width'] = int_or_none(groupdict.get(
                    'width', width_from_json_pos))
                result['height'] = int_or_none(groupdict.get('height'))
                result['fps'] = int_or_none(groupdict.get('fps'))
                result['tbr'] = int_or_none(groupdict.get('tbr'))
                result['vbr'] = int_or_none(groupdict.get('vbr'))

                width_dict = template.get('width_dict')
                if width_dict:
                    result['width'] = width_dict.get(groupdict.get('width_key'))

                format_id_suffix = groupdict.get(
                    template.get('format_id_suffix'))
                break

        if result.get('width') and not result.get('height'):
            result['height'] = int((result['width'] / 16) * 9)

        if result.get('height') and not result.get('width'):
            result['width'] = int((result['height'] / 9) * 16)

        result['format_id'] = ((('http-' + suffix)
                                if suffix else 'http') +
                               ('-' + format_id_suffix
                                if format_id_suffix else ''))

        return result

    def _extract_format_from_index_pos(self,
                                       data,
                                       format_url,
                                       media_array_i,
                                       media_stream_array_i,
                                       stream_i):
        if not data:
            return None

        qualities = self._get_elements_from_path(data, ['mediaCollection',
                                                        '_mediaArray',
                                                        '_mediaStreamArray',
                                                        '_quality'])

        if (qualities and
                media_array_i < len(qualities) and
                media_stream_array_i < len(
                    qualities[media_array_i])):
            quality = str_or_none(
                qualities[media_array_i][media_stream_array_i])
        else:
            quality = None

        suffix = '-'.join(map(
            str,
            [media_array_i, media_stream_array_i, stream_i]))
        if quality is not None:
            suffix = suffix + '-q' + quality

        # The streams are ordered by their size in the JSON data.
        # Infer the video's size from its position within the JSON arrays.
        # The first index is the _mediaStreamArray index, the second one is
        # the _stream.json index.
        widths = [
            [],  # At index 0 there's an m3u8 playlist ('quality' = 'auto')
            [320],
            [512, 480, 480],
            [640, 960],
            [1280],
            [1920],
        ]
        width = None
        if media_stream_array_i < len(widths):
            if stream_i < len(widths[media_stream_array_i]):
                width = widths[media_stream_array_i][stream_i]

        return self._extract_format_from_url(format_url, suffix, width)

    def _extract_episode_info(self, title):
        res = {}
        if not title:
            return res

        # Try to read episode data from the title.
        for pattern in [
            r'.*(?P<ep_info> \(S(?P<season_number>\d+)/E(?P<episode_number>\d+)\)).*',
            r'.*(?P<ep_info> \((?:Folge |Teil )?(?P<episode_number>\d+)(?:/\d+)?\)).*',
            r'.*(?P<ep_info>Folge (?P<episode_number>\d+)(?:\:| -|) )\"(?P<episode>.+)\".*',
            r'.*(?P<ep_info>Folge (?P<episode_number>\d+)(?:/\d+)?(?:\:| -|) ).*',
        ]:
            m = re.match(pattern, title)
            if m:
                groupdict = m.groupdict()
                for int_entry in ['season_number', 'episode_number']:
                    res[int_entry] = int_or_none(groupdict.get(int_entry))

                for str_entry in ['episode']:
                    res[str_entry] = str_or_none(groupdict.get(str_entry))

                # Build the episode title by removing numeric episode
                # information.
                if groupdict.get('ep_info') and not res['episode']:
                    res['episode'] = str_or_none(
                        title.replace(groupdict.get('ep_info'), ''))

                if res['episode']:
                    res['episode'] = res['episode'].strip()

                break

        # Fallback
        if not res.get('episode'):
            res['episode'] = title.strip()

        return res

    def _extract_age_limit(self, fsk_str):
        m = re.match(r'(?:FSK|fsk|Fsk)(\d+)', fsk_str)
        if m and m.group(1):
            return int_or_none(m.group(1))
        else:
            return 0

    def _extract_metadata(self, data):
        res = {}

        for template in [
            {'key': 'channel',
             'path': ['publicationService', 'name']},

            {'key': 'series',
             'path': ['show', 'title']},

            {'key': 'title',
             'path': ['title']},

            {'key': 'description',
             'path': ['synopsis']},

            {'key': 'thumbnail',
             'path': ['image', 'src'],
             'filter': lambda image_url: image_url.replace('{width}', '1920')},

            {'key': 'timestamp',
             'path': ['broadcastedOn'],
             'filter': unified_timestamp},

            {'key': 'release_date',
             'path': ['broadcastedOn'],
             'filter': unified_strdate},

            {'key': 'age_limit',
             'path': ['maturityContentRating'],
             'filter': self._extract_age_limit},

            {'key': 'duration',
             'path': ['mediaCollection', '_duration'],
             'filter': int_or_none},

            {'key': 'subtitles',
             'path': ['mediaCollection', '_subtitleUrl'],
             'filter': lambda subtitle_url: {'de': [{'ext': 'ttml',
                                                     'url': subtitle_url}]}},
        ]:
            value = self._get_elements_from_path(data, template.get('path'))
            if value is not None:
                filter_func = template.get('filter', str_or_none)
                res[template['key']] = filter_func(value)

        res.update(self._extract_episode_info(res.get('title')))

        return res

    def _extract_video_formats(self, video_id, data):
        formats = []

        if not data:
            return formats

        streams = self._get_elements_from_path(data, ['mediaCollection',
                                                      '_mediaArray',
                                                      '_mediaStreamArray',
                                                      '_stream',
                                                      'json'])
        if not streams:
            return formats

        for media_array_i, media_stream_arrays in enumerate(streams):
            for media_stream_array_i, streams in enumerate(media_stream_arrays):
                for stream_i, stream in enumerate(streams):
                    format_url = url_or_none(stream)
                    if not format_url:
                        continue

                    # Make sure this format isn't already in our list.
                    # Occassionally, there are duplicate files from
                    # different servers.
                    duplicate = next((x for x in formats
                                      if url_basename(x['url']) == url_basename(
                                        format_url)),
                                     None)
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
                        # This is a video file for direct HTTP download
                        formats.append(self._extract_format_from_index_pos(
                            data, format_url,
                            media_array_i, media_stream_array_i, stream_i))

        return formats

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)
        data_json = self._search_regex(
            r'window\.__APOLLO_STATE__\s*=\s*(\{.*);\n',
            webpage,
            'json')
        data = self._parse_json(data_json, display_id)

        if not data:
            raise ExtractorError(
                msg='Did not find any video data to extract', expected=True)

        res = {
            'id': video_id,
            'display_id': display_id,
        }

        res.update(self._extract_metadata(data))

        formats = self._extract_video_formats(video_id, data)

        if not formats and self._is_flag_set(data, 'geoblocked'):
            self.raise_geo_restricted(
                msg='This video is not available due to geoblocking',
                countries=['DE'])

        if not formats and self._is_flag_set(data, 'blockedByFsk'):
            age_limit = res.get('age_limit')
            if age_limit is not None:
                raise ExtractorError(
                    msg='This video is currently not available due to age '
                        'restrictions (FSK %d). '
                        'Try again from %02d:00 to 06:00.' % (
                            age_limit, 22 if age_limit < 18 else 23),
                    expected=True)
            else:
                raise ExtractorError(
                    msg='This video is currently not available due to age '
                        'restrictions. Try again later.',
                    expected=True)

        if formats:
            self._sort_formats(formats)
            res['formats'] = formats

        return res


class ARDBetaMediathekPlaylistIE(ARDMediathekBaseIE):
    _VALID_URL = r'https://(?:beta|www)\.ardmediathek\.de/(?P<channel>[^/]+)/(?P<playlist_type>shows|more)/(?P<video_id>[a-zA-Z0-9]+)(?:/(?P<display_id>[^/?#]+))?'
    _TESTS = [{
        'url': 'https://www.ardmediathek.de/daserste/shows/Y3JpZDovL2Rhc2Vyc3RlLmRlL3N0dXJtIGRlciBsaWViZQ/sturm-der-liebe',
        'info_dict': {
            'id': '4e55c4bGxyuGq2gig0Q4WU',
            'display_id': 'menschen-und-leben',
            'title': 'Menschen & Leben',
        }
    }, {
        'url': 'https://www.ardmediathek.de/alpha/shows/Y3JpZDovL2JyLmRlL2Jyb2FkY2FzdFNlcmllcy82YmM4YzFhMS1mYWQxLTRiMmYtOGRjYi0wZjk5YTk4YzU3ZTA/bob-ross-the-joy-of-painting',
        'info_dict': {
            'id': 'Y3JpZDovL2JyLmRlL2Jyb2FkY2FzdFNlcmllcy82YmM4YzFhMS1mYWQxLTRiMmYtOGRjYi0wZjk5YTk4YzU3ZTA',
            'display_id': 'bob-ross-the-joy-of-painting',
            'title': 'Bob Ross - The Joy of Painting',
        }
    }, {
        'url': 'https://www.ardmediathek.de/ard/more/4e55c4bGxyuGq2gig0Q4WU/menschen-und-leben',
        'info_dict': {
            'id': '4e55c4bGxyuGq2gig0Q4WU',
            'display_id': 'menschen-und-leben',
            'title': 'Menschen & Leben',
            }
    },
    ]

    _configurations = {
        'shows': {
            'page_type': 'ShowPage',
            'playlist_id_name': 'showId',
            'persisted_query_hash':
            '1801f782ce062a81d19465b059e6147671da882c510cca99e9a9ade8e542922e',
            'total_elements_path': ['pagination', 'totalElements'],
            'video_ids_path': ['teasers', 'links', 'target', 'id'],
        },
        'more': {
            'page_type': 'MorePage',
            'playlist_id_name': 'compilationId',
            'persisted_query_hash':
            '0aa6f77b1d2400b94b9f92e6dbd0fabf652903ecf7c9e74d1367458d079f0810',
            'total_elements_path': ['widget', 'pagination', 'totalElements'],
            'video_ids_path': ['widget', 'teasers', 'links', 'target', 'id'],
        },
    }

    def _build_query_str(self, client, playlist_id, page_number):
        query_variables = '{{"client":"{}","{}":"{}","pageNumber":{}}}'.format(
            client,
            self._conf.get('playlist_id_name'),
            playlist_id,
            page_number)

        # The order of the parameters is important. It only works like this.
        return compat_urllib_parse_urlencode([
            ('variables', query_variables),
            ('extensions', '{"persistedQuery":{"version":1,"sha256Hash":"' +
             self._conf.get('persisted_query_hash') + '"}}'), ])

    def _download_page(self,
                       video_id, referer, client, playlist_id, page_number):
        api_url = 'https://api.ardmediathek.de/public-gateway'

        m = re.match(r'(?P<origin>https?://[^/]+)/[^/]*', referer)
        origin = m.group('origin')
        headers = {'Referer': referer, 'Origin': origin,
                   # The following headers are necessary to get a proper
                   # response.
                   'Content-type': 'application/json',
                   'Accept': '*/*', }
        query_str = self._build_query_str(client, playlist_id,  page_number)

        try:
            note = 'Downloading video IDs (page {})'.format(page_number)
            page_data = self._download_json(api_url + '?' + query_str,
                                            video_id,
                                            headers=headers,
                                            note=note)
            page = self._get_page(page_data)
        except ExtractorError:
            return None, None

        return page_data, page

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        display_id = mobj.group('display_id') or video_id
        channel = mobj.group('channel')
        playlist_type = mobj.group('playlist_type')

        self._conf = self._configurations.get(playlist_type)
        self._page_type = self._conf.get('page_type')

        webpage = self._download_webpage(url, display_id)
        data_json = self._search_regex(
            r'window\.__APOLLO_STATE__\s*=\s*(\{.*);\n', webpage, 'json')
        data = self._parse_json(data_json, display_id)
        page = self._get_page(data)
        if not isinstance(page, dict):
            raise ExtractorError(msg='No playlist data available',
                                 expected=True)

        title = self._get_elements_from_path(data, ['title'], page)
        description = self._get_elements_from_path(data, ['synopsis'], page)
        description = None

        page_number = 0

        ep_data, page = self._download_page(display_id, url, channel,
                                            video_id, page_number)
        if not isinstance(page, dict):
            raise ExtractorError(msg='No playlist data available',
                                 expected=True)

        total_elements = self._get_elements_from_path(
            ep_data, self._conf.get('total_elements_path'), page) or 0
        self.to_screen('{}: There are supposed to be {} videos.'.format(
            display_id, total_elements))

        page_size = 0
        num_skipped_ids = 0
        skipped_previous_page = False

        urls = []
        while True:
            ids_on_page = self._get_elements_from_path(
                ep_data, self._conf.get('video_ids_path'), page)
            if ids_on_page:
                urls.extend(['https://www.ardmediathek.de/{}/player/{}'.format(
                    channel, x) for x in ids_on_page])
                page_size = max(page_size, len(ids_on_page))
            elif not skipped_previous_page:
                # We're receiving data but it doesn't contain any
                # video IDs. This might happen if the number of reported
                # elements is higher than the actual number of videos
                # in this collection.
                break

            if len(urls) + num_skipped_ids >= total_elements:
                break

            page_number = page_number + 1
            ep_data, page = self._download_page(display_id, url, channel,
                                                video_id, page_number)
            skipped_previous_page = False

            if not isinstance(page, dict):
                self.report_warning(
                    'Could not download page {} with video IDs. '
                    'Skipping {} videos.'.format(
                        page_number,
                        min(page_size,
                            total_elements - len(urls) - num_skipped_ids)),
                    display_id)
                num_skipped_ids = num_skipped_ids + page_size
                skipped_previous_page = True

        # Remove duplicates
        urls = orderedSet(urls)

        if total_elements > len(urls):
            msg = 'Only received {} video IDs'.format(len(urls))
            if num_skipped_ids > 0:
                # We had to skip pages because they could not be downloaded
                msg = msg + '. Had to skip {} of {} vidoes'.format(
                    total_elements - len(urls), total_elements)
            else:
                # The API reported the wrong number of videos and/or there
                # might have been duplicate entries
                msg = msg + ' of {} reported videos.'.format(total_elements)
            self.report_warning(msg)

        entries = [
            self.url_result(item_url, ie=ARDBetaMediathekIE.ie_key())
            for item_url in urls]

        return self.playlist_result(entries, video_id, title, description)
