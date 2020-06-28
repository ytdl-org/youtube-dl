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
    _VALID_URL = r'(?P<mainurl>https?://(www\.)?daserste\.de/[^?#]+/videos(?:extern)?/(?P<display_id>[^/?#]+)-(?P<id>[0-9]+))\.html'
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
        'url': 'https://www.daserste.de/information/reportage-dokumentation/erlebnis-erde/videosextern/woelfe-und-herdenschutzhunde-ungleiche-brueder-102.html',
        'only_matching': True,
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


class ARDBetaMediathekIE(ARDMediathekBaseIE):
    _VALID_URL = r'https://(?:(?:beta|www)\.)?ardmediathek\.de/(?P<client>[^/]+)/(?:player|live|video)/(?P<display_id>(?:[^/]+/)*)(?P<video_id>[a-zA-Z0-9]+)'
    _TESTS = [{
        'url': 'https://ardmediathek.de/ard/video/die-robuste-roswita/Y3JpZDovL2Rhc2Vyc3RlLmRlL3RhdG9ydC9mYmM4NGM1NC0xNzU4LTRmZGYtYWFhZS0wYzcyZTIxNGEyMDE',
        'md5': 'dfdc87d2e7e09d073d5a80770a9ce88f',
        'info_dict': {
            'display_id': 'die-robuste-roswita',
            'id': '70153354',
            'title': 'Die robuste Roswita',
            'description': r're:^Der Mord.*trüber ist als die Ilm.',
            'duration': 5316,
            'thumbnail': 'https://img.ardmediathek.de/standard/00/70/15/33/90/-1852531467/16x9/960?mandant=ard',
            'timestamp': 1577047500,
            'upload_date': '20191222',
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
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        display_id = mobj.group('display_id')
        if display_id:
            display_id = display_id.rstrip('/')
        if not display_id:
            display_id = video_id

        player_page = self._download_json(
            'https://api.ardmediathek.de/public-gateway',
            display_id, data=json.dumps({
                'query': '''{
  playerPage(client:"%s", clipId: "%s") {
    blockedByFsk
    broadcastedOn
    maturityContentRating
    mediaCollection {
      _duration
      _geoblocked
      _isLive
      _mediaArray {
        _mediaStreamArray {
          _quality
          _server
          _stream
        }
      }
      _previewImage
      _subtitleUrl
      _type
    }
    show {
      title
    }
    synopsis
    title
    tracking {
      atiCustomVars {
        contentId
      }
    }
  }
}''' % (mobj.group('client'), video_id),
            }).encode(), headers={
                'Content-Type': 'application/json'
            })['data']['playerPage']
        title = player_page['title']
        content_id = str_or_none(try_get(
            player_page, lambda x: x['tracking']['atiCustomVars']['contentId']))
        media_collection = player_page.get('mediaCollection') or {}
        if not media_collection and content_id:
            media_collection = self._download_json(
                'https://www.ardmediathek.de/play/media/' + content_id,
                content_id, fatal=False) or {}
        info = self._parse_media_info(
            media_collection, content_id or video_id,
            player_page.get('blockedByFsk'))
        age_limit = None
        description = player_page.get('synopsis')
        maturity_content_rating = player_page.get('maturityContentRating')
        if maturity_content_rating:
            age_limit = int_or_none(maturity_content_rating.lstrip('FSK'))
        if not age_limit and description:
            age_limit = int_or_none(self._search_regex(
                r'\(FSK\s*(\d+)\)\s*$', description, 'age limit', default=None))
        info.update({
            'age_limit': age_limit,
            'display_id': display_id,
            'title': title,
            'description': description,
            'timestamp': unified_timestamp(player_page.get('broadcastedOn')),
            'series': try_get(player_page, lambda x: x['show']['title']),
        })
        return info
