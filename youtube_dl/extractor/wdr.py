# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    js_to_json,
    strip_jsonp,
    unified_strdate,
    update_url_query,
    urlhandle_detect_ext,
)


class WDRBaseIE(InfoExtractor):
    def _extract_wdr_video(self, webpage, display_id):
        # for wdr.de the data-extension is in a tag with the class "mediaLink"
        # for wdr.de radio players, in a tag with the class "wdrrPlayerPlayBtn"
        # for wdrmaus, in a tag with the class "videoButton" (previously a link
        # to the page in a multiline "videoLink"-tag)
        json_metadata = self._html_search_regex(
            r'class=(?:"(?:mediaLink|wdrrPlayerPlayBtn|videoButton)\b[^"]*"[^>]+|"videoLink\b[^"]*"[\s]*>\n[^\n]*)data-extension="([^"]+)"',
            webpage, 'media link', default=None, flags=re.MULTILINE)

        if not json_metadata:
            return

        media_link_obj = self._parse_json(json_metadata, display_id,
                                          transform_source=js_to_json)
        jsonp_url = media_link_obj['mediaObj']['url']

        metadata = self._download_json(
            jsonp_url, display_id, transform_source=strip_jsonp)

        metadata_tracker_data = metadata['trackerData']
        metadata_media_resource = metadata['mediaResource']

        formats = []

        # check if the metadata contains a direct URL to a file
        for kind, media_resource in metadata_media_resource.items():
            if kind not in ('dflt', 'alt'):
                continue

            for tag_name, medium_url in media_resource.items():
                if tag_name not in ('videoURL', 'audioURL'):
                    continue

                ext = determine_ext(medium_url)
                if ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        medium_url, display_id, 'mp4', 'm3u8_native',
                        m3u8_id='hls'))
                elif ext == 'f4m':
                    manifest_url = update_url_query(
                        medium_url, {'hdcore': '3.2.0', 'plugin': 'aasp-3.2.0.77.18'})
                    formats.extend(self._extract_f4m_formats(
                        manifest_url, display_id, f4m_id='hds', fatal=False))
                elif ext == 'smil':
                    formats.extend(self._extract_smil_formats(
                        medium_url, 'stream', fatal=False))
                else:
                    a_format = {
                        'url': medium_url
                    }
                    if ext == 'unknown_video':
                        urlh = self._request_webpage(
                            medium_url, display_id, note='Determining extension')
                        ext = urlhandle_detect_ext(urlh)
                        a_format['ext'] = ext
                    formats.append(a_format)

        self._sort_formats(formats)

        subtitles = {}
        caption_url = metadata_media_resource.get('captionURL')
        if caption_url:
            subtitles['de'] = [{
                'url': caption_url,
                'ext': 'ttml',
            }]

        title = metadata_tracker_data['trackerClipTitle']

        return {
            'id': metadata_tracker_data.get('trackerClipId', display_id),
            'display_id': display_id,
            'title': title,
            'alt_title': metadata_tracker_data.get('trackerClipSubcategory'),
            'formats': formats,
            'subtitles': subtitles,
            'upload_date': unified_strdate(metadata_tracker_data.get('trackerClipAirTime')),
        }


class WDRIE(WDRBaseIE):
    _CURRENT_MAUS_URL = r'https?://(?:www\.)wdrmaus.de/(?:[^/]+/){1,2}[^/?#]+\.php5'
    _PAGE_REGEX = r'/(?:mediathek/)?[^/]+/(?P<type>[^/]+)/(?P<display_id>.+)\.html'
    _VALID_URL = r'(?P<page_url>https?://(?:www\d\.)?wdr\d?\.de)' + _PAGE_REGEX + '|' + _CURRENT_MAUS_URL

    _TESTS = [
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/doku-am-freitag/video-geheimnis-aachener-dom-100.html',
            # HDS download, MD5 is unstable
            'info_dict': {
                'id': 'mdb-1058683',
                'ext': 'flv',
                'display_id': 'doku-am-freitag/video-geheimnis-aachener-dom-100',
                'title': 'Geheimnis Aachener Dom',
                'alt_title': 'Doku am Freitag',
                'upload_date': '20160304',
                'description': 'md5:87be8ff14d8dfd7a7ee46f0299b52318',
                'is_live': False,
                'subtitles': {'de': [{
                    'url': 'http://ondemand-ww.wdr.de/medp/fsk0/105/1058683/1058683_12220974.xml',
                    'ext': 'ttml',
                }]},
            },
        },
        {
            'url': 'http://www1.wdr.de/mediathek/audio/wdr3/wdr3-gespraech-am-samstag/audio-schriftstellerin-juli-zeh-100.html',
            'md5': 'f4c1f96d01cf285240f53ea4309663d8',
            'info_dict': {
                'id': 'mdb-1072000',
                'ext': 'mp3',
                'display_id': 'wdr3-gespraech-am-samstag/audio-schriftstellerin-juli-zeh-100',
                'title': 'Schriftstellerin Juli Zeh',
                'alt_title': 'WDR 3 Gespräch am Samstag',
                'upload_date': '20160312',
                'description': 'md5:e127d320bc2b1f149be697ce044a3dd7',
                'is_live': False,
                'subtitles': {}
            },
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/live/index.html',
            'info_dict': {
                'id': 'mdb-103364',
                'ext': 'mp4',
                'display_id': 'index',
                'title': r're:^WDR Fernsehen im Livestream [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
                'alt_title': 'WDR Fernsehen Live',
                'upload_date': None,
                'description': 'md5:ae2ff888510623bf8d4b115f95a9b7c9',
                'is_live': True,
                'subtitles': {}
            },
            'params': {
                'skip_download': True,  # m3u8 download
            },
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/aktuelle-stunde/aktuelle-stunde-120.html',
            'playlist_mincount': 8,
            'info_dict': {
                'id': 'aktuelle-stunde/aktuelle-stunde-120',
            },
        },
        {
            'url': 'http://www.wdrmaus.de/aktuelle-sendung/index.php5',
            'info_dict': {
                'id': 'mdb-1323501',
                'ext': 'mp4',
                'upload_date': 're:^[0-9]{8}$',
                'title': 're:^Die Sendung mit der Maus vom [0-9.]{10}$',
                'description': 'Die Seite mit der Maus -',
            },
            'skip': 'The id changes from week to week because of the new episode'
        },
        {
            'url': 'http://www.wdrmaus.de/filme/sachgeschichten/achterbahn.php5',
            'md5': '803138901f6368ee497b4d195bb164f2',
            'info_dict': {
                'id': 'mdb-186083',
                'ext': 'mp4',
                'upload_date': '20130919',
                'title': 'Sachgeschichte - Achterbahn ',
                'description': 'Die Seite mit der Maus -',
            },
        },
        {
            'url': 'http://www1.wdr.de/radio/player/radioplayer116~_layout-popupVersion.html',
            # Live stream, MD5 unstable
            'info_dict': {
                'id': 'mdb-869971',
                'ext': 'flv',
                'title': 'COSMO Livestream',
                'description': 'md5:2309992a6716c347891c045be50992e4',
                'upload_date': '20160101',
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        url_type = mobj.group('type')
        page_url = mobj.group('page_url')
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)

        info_dict = self._extract_wdr_video(webpage, display_id)

        if not info_dict:
            entries = [
                self.url_result(page_url + href[0], 'WDR')
                for href in re.findall(
                    r'<a href="(%s)"[^>]+data-extension=' % self._PAGE_REGEX,
                    webpage)
            ]

            if entries:  # Playlist page
                return self.playlist_result(entries, playlist_id=display_id)

            raise ExtractorError('No downloadable streams found', expected=True)

        is_live = url_type == 'live'

        if is_live:
            info_dict.update({
                'title': self._live_title(info_dict['title']),
                'upload_date': None,
            })
        elif 'upload_date' not in info_dict:
            info_dict['upload_date'] = unified_strdate(self._html_search_meta('DC.Date', webpage, 'upload date'))

        info_dict.update({
            'description': self._html_search_meta('Description', webpage),
            'is_live': is_live,
        })

        return info_dict


class WDRMobileIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://mobile-ondemand\.wdr\.de/
        .*?/fsk(?P<age_limit>[0-9]+)
        /[0-9]+/[0-9]+/
        (?P<id>[0-9]+)_(?P<title>[0-9]+)'''
    IE_NAME = 'wdr:mobile'
    _TEST = {
        'url': 'http://mobile-ondemand.wdr.de/CMS2010/mdb/ondemand/weltweit/fsk0/42/421735/421735_4283021.mp4',
        'info_dict': {
            'title': '4283021',
            'id': '421735',
            'ext': 'mp4',
            'age_limit': 0,
        },
        'skip': 'Problems with loading data.'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        return {
            'id': mobj.group('id'),
            'title': mobj.group('title'),
            'age_limit': int(mobj.group('age_limit')),
            'url': url,
            'http_headers': {
                'User-Agent': 'mobile',
            },
        }
