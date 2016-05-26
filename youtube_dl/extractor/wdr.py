# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)
from ..utils import (
    strip_jsonp,
    unified_strdate,
    ExtractorError,
)


class WDRIE(InfoExtractor):
    _CURRENT_MAUS_URL = r'https?://www.wdrmaus.de/aktuelle-sendung/(wdr|index).php5'
    _PAGE_REGEX = r'/mediathek/(?P<media_type>[^/]+)/(?P<type>[^/]+)/(?P<display_id>.+)\.html'
    _VALID_URL = r'(?P<page_url>https?://(?:www\d\.)?wdr\d?\.de)' + _PAGE_REGEX + '|' + _CURRENT_MAUS_URL

    _JS_URL_REGEX = r'(https?://deviceids-medp.wdr.de/ondemand/\d+/\d+\.js)'

    _TESTS = [
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/doku-am-freitag/video-geheimnis-aachener-dom-100.html',
            'md5': 'e58c39c3e30077141d258bf588700a7b',
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
                    'url': 'http://ondemand-ww.wdr.de/medp/fsk0/105/1058683/1058683_12220974.xml'
                }]},
            },
            'skip': 'Page Not Found',
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
            'skip': 'Page Not Found',
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/live/index.html',
            'info_dict': {
                'id': 'mdb-103364',
                'ext': 'flv',
                'display_id': 'index',
                'title': r're:^WDR Fernsehen im Livestream [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
                'alt_title': 'WDR Fernsehen Live',
                'upload_date': None,
                'description': 'md5:ae2ff888510623bf8d4b115f95a9b7c9',
                'is_live': True,
                'subtitles': {}
            }
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/aktuelle-stunde/aktuelle-stunde-120.html',
            'playlist_mincount': 10,
            'info_dict': {
                'id': 'aktuelle-stunde/aktuelle-stunde-120',
            },
        },
        {
            'url': 'http://www.wdrmaus.de/aktuelle-sendung/index.php5',
            'info_dict': {
                'id': 'mdb-1096487',
                'ext': 'flv',
                'upload_date': 're:^[0-9]{8}$',
                'title': 're:^Die Sendung mit der Maus vom [0-9.]{10}$',
                'description': '- Die Sendung mit der Maus -',
            },
            'skip': 'The id changes from week to week because of the new episode'
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        url_type = mobj.group('type')
        page_url = mobj.group('page_url')
        display_id = mobj.group('display_id')
        webpage = self._download_webpage(url, display_id)

        js_url = self._search_regex(self._JS_URL_REGEX, webpage, 'js_url', default=None)

        if not js_url:
            entries = [
                self.url_result(page_url + href[0], 'WDR')
                for href in re.findall(
                    r'<a href="(%s)"' % self._PAGE_REGEX,
                    webpage)
            ]

            if entries:  # Playlist page
                return self.playlist_result(entries, playlist_id=display_id)

            raise ExtractorError('No downloadable streams found', expected=True)

        metadata = self._download_json(
            js_url, 'metadata', transform_source=strip_jsonp)

        metadata_tracker_data = metadata['trackerData']
        metadata_media_resource = metadata['mediaResource']

        formats = []

        # check if the metadata contains a direct URL to a file
        metadata_media_alt = metadata_media_resource.get('alt')
        if metadata_media_alt:
            for tag_name in ['videoURL', 'audioURL']:
                if tag_name in metadata_media_alt:
                    formats.append({
                        'url': metadata_media_alt[tag_name]
                    })

        # check if there are flash-streams for this video
        if 'dflt' in metadata_media_resource and 'videoURL' in metadata_media_resource['dflt']:
            video_url = metadata_media_resource['dflt']['videoURL']
            if video_url.endswith('.f4m'):
                full_video_url = video_url + '?hdcore=3.2.0&plugin=aasp-3.2.0.77.18'
                formats.extend(self._extract_f4m_formats(full_video_url, display_id, f4m_id='hds', fatal=False))
            elif video_url.endswith('.smil'):
                formats.extend(self._extract_smil_formats(video_url, 'stream', fatal=False))

        subtitles = {}
        caption_url = metadata_media_resource.get('captionURL')
        if caption_url:
            subtitles['de'] = [{
                'url': caption_url
            }]

        title = metadata_tracker_data.get('trackerClipTitle')
        is_live = url_type == 'live'

        if is_live:
            title = self._live_title(title)
            upload_date = None
        elif 'trackerClipAirTime' in metadata_tracker_data:
            upload_date = metadata_tracker_data['trackerClipAirTime']
        else:
            upload_date = self._html_search_meta('DC.Date', webpage, 'upload date')

        if upload_date:
            upload_date = unified_strdate(upload_date)

        self._sort_formats(formats)

        return {
            'id': metadata_tracker_data.get('trackerClipId', display_id),
            'display_id': display_id,
            'title': title,
            'alt_title': metadata_tracker_data.get('trackerClipSubcategory'),
            'formats': formats,
            'upload_date': upload_date,
            'description': self._html_search_meta('Description', webpage),
            'is_live': is_live,
            'subtitles': subtitles,
        }


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


class WDRMausIE(InfoExtractor):
    _VALID_URL = 'https?://(?:www\.)?wdrmaus\.de/(?:[^/]+/){,2}(?P<id>[^/?#]+)((?<!index)\.php5|/(?:$|[?#]))'
    IE_DESC = 'Sendung mit der Maus'
    _TESTS = [{
        'url': 'http://www.wdrmaus.de/sachgeschichten/sachgeschichten/achterbahn.php5',
        'md5': '178b432d002162a14ccb3e0876741095',
        'info_dict': {
            'id': 'achterbahn',
            'ext': 'mp4',
            'thumbnail': 're:^http://.+\.jpg',
            'upload_date': '20131001',
            'title': '19.09.2013 - Achterbahn',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        param_code = self._html_search_regex(
            r'<a href="\?startVideo=1&amp;([^"]+)"', webpage, 'parameters')

        title_date = self._search_regex(
            r'<div class="sendedatum"><p>Sendedatum:\s*([0-9\.]+)</p>',
            webpage, 'air date')
        title_str = self._html_search_regex(
            r'<h1>(.*?)</h1>', webpage, 'title')
        title = '%s - %s' % (title_date, title_str)
        upload_date = unified_strdate(
            self._html_search_meta('dc.date', webpage))

        fields = compat_parse_qs(param_code)
        video_url = fields['firstVideo'][0]
        thumbnail = compat_urlparse.urljoin(url, fields['startPicture'][0])

        formats = [{
            'format_id': 'rtmp',
            'url': video_url,
        }]

        jscode = self._download_webpage(
            'http://www.wdrmaus.de/codebase/js/extended-medien.min.js',
            video_id, fatal=False,
            note='Downloading URL translation table',
            errnote='Could not download URL translation table')
        if jscode:
            for m in re.finditer(
                    r"stream:\s*'dslSrc=(?P<stream>[^']+)',\s*download:\s*'(?P<dl>[^']+)'\s*\}",
                    jscode):
                if video_url.startswith(m.group('stream')):
                    http_url = video_url.replace(
                        m.group('stream'), m.group('dl'))
                    formats.append({
                        'format_id': 'http',
                        'url': http_url,
                    })
                    break

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
        }
