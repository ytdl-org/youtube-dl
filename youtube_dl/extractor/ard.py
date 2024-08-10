# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from .generic import GenericIE
from ..utils import (
    determine_ext,
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
    xpath_text,
)
from ..compat import compat_etree_fromstring


class ARDMediathekBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ['DE']

    def _extract_media_info(self, media_info_url, webpage, video_id):
        media_info = self._download_json(
            media_info_url, video_id, 'Downloading media JSON')
        return self._parse_media_info(media_info, video_id, '"fsk"' in webpage)

    def _parse_media_info(self, media_info, video_id, fsk):
        formats = self._extract_formats(media_info, video_id)

        if not formats:
            if fsk:
                raise ExtractorError(
                    'This video is only available after 20:00', expected=True)
            elif media_info.get('_geoblocked'):
                self.raise_geo_restricted(
                    'This video is not available due to geoblocking',
                    countries=self._GEO_COUNTRIES)

        self._sort_formats(formats)

        subtitles = {}
        subtitle_url = media_info.get('_subtitleUrl')
        if subtitle_url:
            subtitles['de'] = [{
                'ext': 'ttml',
                'url': subtitle_url,
            }]

        return {
            'id': video_id,
            'duration': int_or_none(media_info.get('_duration')),
            'thumbnail': media_info.get('_previewImage'),
            'is_live': media_info.get('_isLive') is True,
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
                            }), video_id, f4m_id='hds', fatal=False))
                    elif ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            stream_url, video_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
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
                        m = re.search(
                            r'_(?P<width>\d+)x(?P<height>\d+)\.mp4$',
                            stream_url)
                        if m:
                            f.update({
                                'width': int(m.group('width')),
                                'height': int(m.group('height')),
                            })
                        if type_ == 'audio':
                            f['vcodec'] = 'none'
                        formats.append(f)
        return formats


class ARDMediathekIE(ARDMediathekBaseIE):
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

        title = self._og_search_title(webpage, default=None) or self._html_search_regex(
            [r'<h1(?:\s+class="boxTopHeadline")?>(.*?)</h1>',
             r'<meta name="dcterms\.title" content="(.*?)"/>',
             r'<h4 class="headline">(.*?)</h4>',
             r'<title[^>]*>(.*?)</title>'],
            webpage, 'title')
        description = self._og_search_description(webpage, default=None) or self._html_search_meta(
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
    _VALID_URL = r'(?P<mainurl>https?://(?:www\.)?daserste\.de/(?:[^/?#&]+/)+(?P<id>[^/?#&]+))\.html'
    _TESTS = [{
        # available till 7.01.2022
        'url': 'https://www.daserste.de/information/talk/maischberger/videos/maischberger-die-woche-video100.html',
        'md5': '867d8aa39eeaf6d76407c5ad1bb0d4c1',
        'info_dict': {
            'id': 'maischberger-die-woche-video100',
            'display_id': 'maischberger-die-woche-video100',
            'ext': 'mp4',
            'duration': 3687.0,
            'title': 'maischberger. die woche vom 7. Januar 2021',
            'upload_date': '20210107',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://www.daserste.de/information/politik-weltgeschehen/morgenmagazin/videosextern/dominik-kahun-aus-der-nhl-direkt-zur-weltmeisterschaft-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.daserste.de/information/nachrichten-wetter/tagesthemen/videosextern/tagesthemen-17736.html',
        'only_matching': True,
    }, {
        'url': 'http://www.daserste.de/information/reportage-dokumentation/dokus/videos/die-story-im-ersten-mission-unter-falscher-flagge-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.daserste.de/unterhaltung/serie/in-aller-freundschaft-die-jungen-aerzte/Drehpause-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.daserste.de/unterhaltung/film/filmmittwoch-im-ersten/videos/making-ofwendezeit-video-100.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        player_url = mobj.group('mainurl') + '~playerXml.xml'
        doc = self._download_xml(player_url, display_id)
        video_node = doc.find('./video')
        upload_date = unified_strdate(xpath_text(
            video_node, './broadcastDate'))
        thumbnail = xpath_text(video_node, './/teaserImage//variant/url')

        formats = []
        for a in video_node.findall('.//asset'):
            file_name = xpath_text(a, './fileName', default=None)
            if not file_name:
                continue
            format_type = a.attrib.get('type')
            format_url = url_or_none(file_name)
            if format_url:
                ext = determine_ext(file_name)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, display_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id=format_type or 'hls', fatal=False))
                    continue
                elif ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        update_url_query(format_url, {'hdcore': '3.7.0'}),
                        display_id, f4m_id=format_type or 'hds', fatal=False))
                    continue
            f = {
                'format_id': format_type,
                'width': int_or_none(xpath_text(a, './frameWidth')),
                'height': int_or_none(xpath_text(a, './frameHeight')),
                'vbr': int_or_none(xpath_text(a, './bitrateVideo')),
                'abr': int_or_none(xpath_text(a, './bitrateAudio')),
                'vcodec': xpath_text(a, './codecVideo'),
                'tbr': int_or_none(xpath_text(a, './totalBitrate')),
            }
            server_prefix = xpath_text(a, './serverPrefix', default=None)
            if server_prefix:
                f.update({
                    'url': server_prefix,
                    'playpath': file_name,
                })
            else:
                if not format_url:
                    continue
                f['url'] = format_url
            formats.append(f)
        self._sort_formats(formats)

        _SUB_FORMATS = (
            ('./dataTimedText', 'ttml'),
            ('./dataTimedTextNoOffset', 'ttml'),
            ('./dataTimedTextVtt', 'vtt'),
        )

        subtitles = {}
        for subsel, subext in _SUB_FORMATS:
            for node in video_node.findall(subsel):
                subtitles.setdefault('de', []).append({
                    'url': node.attrib['url'],
                    'ext': subext,
                })

        return {
            'id': xpath_text(video_node, './videoId', default=display_id),
            'formats': formats,
            'subtitles': subtitles,
            'display_id': display_id,
            'title': video_node.find('./title').text,
            'duration': parse_duration(video_node.find('./duration').text),
            'upload_date': upload_date,
            'thumbnail': thumbnail,
        }


class ARDBetaMediathekIE(ARDMediathekBaseIE):

    _VALID_URL = r'https://(?:(?:beta|www)\.)?ardmediathek\.de/(((?:[^/]+/)?(?:player|live|video|serie|sendung)/(?:[^/]+/)*(?P<id>Y3JpZDovL[a-zA-Z0-9]+))|(((?P<sender>[a-zA-Z0-9\-]+)([/]))?(?P<name>[a-zA-Z0-9\-]+)))'

    _TESTS = [{
        'url': 'https://www.ardmediathek.de/mdr/video/die-robuste-roswita/Y3JpZDovL21kci5kZS9iZWl0cmFnL2Ntcy84MWMxN2MzZC0wMjkxLTRmMzUtODk4ZS0wYzhlOWQxODE2NGI/',
        'md5': 'a1dc75a39c61601b980648f7c9f9f71d',
        'info_dict': {
            'display_id': 'die-robuste-roswita',
            'id': '78566716',
            'title': 'Die robuste Roswita',
            'description': r're:^Der Mord.*totgeglaubte Ehefrau Roswita',
            'duration': 5316,
            'thumbnail': 'https://img.ardmediathek.de/standard/00/78/56/67/84/575672121/16x9/960?mandant=ard',
            'timestamp': 1596658200,
            'upload_date': '20200805',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://beta.ardmediathek.de/ard/video/Y3JpZDovL2Rhc2Vyc3RlLmRlL3RhdG9ydC9mYmM4NGM1NC0xNzU4LTRmZGYtYWFhZS0wYzcyZTIxNGEyMDE',
        'only_matching': True,
    }, {
        'url': 'https://ardmediathek.de/ard/video/saartalk/saartalk-gesellschaftsgift-haltung-gegen-hass/sr-fernsehen/Y3JpZDovL3NyLW9ubGluZS5kZS9TVF84MTY4MA/',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/ard/video/trailer/private-eyes-s01-e01/one/Y3JpZDovL3dkci5kZS9CZWl0cmFnLTE1MTgwYzczLWNiMTEtNGNkMS1iMjUyLTg5MGYzOWQxZmQ1YQ/',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/ard/player/Y3JpZDovL3N3ci5kZS9hZXgvbzEwNzE5MTU/',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/swr/live/Y3JpZDovL3N3ci5kZS8xMzQ4MTA0Mg',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/video/coronavirus-update-ndr-info/astrazeneca-kurz-lockdown-und-pims-syndrom-81/ndr/Y3JpZDovL25kci5kZS84NzE0M2FjNi0wMWEwLTQ5ODEtOTE5NS1mOGZhNzdhOTFmOTI/',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/ard/player/Y3JpZDovL3dkci5kZS9CZWl0cmFnLWQ2NDJjYWEzLTMwZWYtNGI4NS1iMTI2LTU1N2UxYTcxOGIzOQ/tatort-duo-koeln-leipzig-ihr-kinderlein-kommet',
        'only_matching': True,
    }, {
        'url': 'https://ardmediathek.de/sendung/saartalk/saartalk-gesellschaftsgift-haltung-gegen-hass/sr-fernsehen/Y3JpZDovL3NyLW9ubGluZS5kZS9TVF84MTY4MA/',
        'only_matching': True,
    }, {
        'url': 'https://ardmediathek.de/serie/saartalk/saartalk-gesellschaftsgift-haltung-gegen-hass/sr-fernsehen/Y3JpZDovL3NyLW9ubGluZS5kZS9TVF84MTY4MA/',
        'only_matching': True,
    }, {
        'url': 'https://www.ardmediathek.de/br/dahoam-is-dahoam',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_name = self._match_id(url, group_name='name')
        sender = self._match_id(url, group_name='sender')

        if '/serie/' in url or '/sendung/' in url:
            return self._real_extract_serie(video_id)
        elif 'none' != video_name.lower():
            return self._real_extract_named_serie(video_name, sender if 'none' != sender.lower() else "ard")
        else:
            return self._real_extract_video(video_id)

    def _real_extract_video(self, video_id):

        player_page = self._download_json(
                f'https://api.ardmediathek.de/page-gateway/pages/ard/item/{video_id}',
                video_id
        )

        title = player_page['title']
        content_id = str_or_none(
                try_get(
                        player_page, lambda x: x['tracking']['atiCustomVars']['contentId']
                )
        )
        media_collection = player_page['widgets'][0].get('mediaCollection') or {}
        if not media_collection and content_id:
            media_collection = self._download_json(
                    'https://www.ardmediathek.de/play/media/' + content_id,
                    content_id, fatal=False
            ) or {}

        info = self._parse_media_info(
            media_collection['embedded'], content_id or video_id,
            player_page['widgets'][0].get('blockedByFsk')
        )

        age_limit = None
        description = player_page['widgets'][0].get('synopsis')
        maturity_content_rating = player_page['widgets'][0].get('maturityContentRating')
        if maturity_content_rating:
            age_limit = int_or_none(maturity_content_rating.lstrip('FSK'))
        if not age_limit and description:
            age_limit = int_or_none(
                self._search_regex(
                    r'\(FSK\s*(\d+)\)\s*$', description, 'age limit', default=None
                )
            )

        session_episode_match = re.search(r"\(S(\d+)/E(\d+)\)", title)
        episode_match = re.search(r"\((\d+)\)", title)
        episode_name_match = re.search(r"(Folge\s\d+)", title)

        if session_episode_match:
            season_number = session_episode_match.group(1)
            episode_number = session_episode_match.group(2)

            alt_title = re.sub(r"\(S\d+/E\d+\)", "", title)
            alt_title = re.sub(r"(Folge \d+(\:|\s\-))", "", alt_title)
            alt_title = alt_title.replace("|", "").replace("  ", " ").replace(" .", "").strip()

            info.update(
                {
                    'season_number': int(season_number),
                    'episode_number': int(episode_number),
                    'alt_title':  alt_title
                }
            )
        elif episode_name_match:
            episode_number = episode_name_match.group(1).replace("Folge ", "")

            alt_title = re.sub(r"(Folge\s\d+)", "", title)
            alt_title = alt_title.replace("|", "").replace("  ", " ").replace(" .", "").strip()

            info.update(
                {
                    'season_number': int(0),
                    'episode_number': int(episode_number),
                    'alt_title':  alt_title
                    }
            )

        elif episode_match:
            episode_number = episode_match.group(1)
            info.update(
                {
                    'season_number': int(0),
                    'episode_number': int(episode_number),
                    'alt_title':re.sub(r"\(\d+\)", "", title).replace("  ", "").strip()
                }
            )
        else:
            info.update(
                {
                    'alt_title': title
                }
            )

        info.update(
            {
                'age_limit': age_limit,
                'title': title,
                'description': description,
                'timestamp': unified_timestamp(player_page['widgets'][0].get('broadcastedOn')),
                'series': try_get(player_page['widgets'][0], lambda x: x['show']['title']),
                'channel': player_page['widgets'][0]['publicationService']['name'],
                'channel_id': player_page['widgets'][0]['publicationService']['id'],
                'channel_url': f"https://www.ardmediathek.de/{player_page['widgets'][0]['publicationService']['id']}",
            }
        )
        return info

    def _real_extract_serie(self, video_id):
        entries = []

        page_number = 0
        page_size = 100

        while True:

            widgets = self._download_json(
                    f'https://api.ardmediathek.de/page-gateway/widgets/ard/asset/{video_id}',
                    video_id,
                    query={'pageSize':str(page_size), 'pageNumber':page_number}
            )

            for teaser in widgets['teasers']:
                if 'EPISODE' == teaser['coreAssetType']:
                    item = self._real_extract_video(teaser['id'])
                    item['webpage_url'] = f"https://www.ardmediathek.de/video/{teaser['id']}"

                    entries.append(item)

            total = widgets['pagination']['totalElements']
            if (page_number + 1) * page_size > total:
                break
            page_number += 1

        return self.playlist_result(entries)

    def _real_extract_named_serie(self, video_id, sender):

        entries = []
        page_size = 100

        widgets = self._download_json(
                f'https://api.ardmediathek.de/page-gateway/pages/{sender}/editorial/{video_id}',
                video_id,
                query={'pageSize': str(10), 'pageNumber': 0}
        )['widgets']

        for widget in widgets:
            widget_id = widget['id']
            page_number = 0

            while True:
                page_data = self._download_json(
                        f'https://api.ardmediathek.de/page-gateway/widgets/{sender}/editorials/{widget_id}',
                        video_id,
                        query={'pageSize': page_size, 'pageNumber': page_number}
                )

                for teaser in page_data['teasers']:
                    if 'EPISODE' == teaser.get('coreAssetType', None) and teaser['type'] not in ['poster'] and ':' not in teaser['id']:

                        item = self._real_extract_video(teaser['id'])
                        item['webpage_url'] = f"https://www.ardmediathek.de/video/{teaser['id']}"
                        entries.append(item)

                total = page_data['pagination']['totalElements']
                if (page_number + 1) * page_size > total:
                    break
                page_number += 1

        return self.playlist_result(entries)
