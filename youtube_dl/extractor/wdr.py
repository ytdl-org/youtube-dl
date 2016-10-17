# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)
from ..utils import (
    unified_strdate,
    qualities,
)


class WDRIE(InfoExtractor):
    _PLAYER_REGEX = '-(?:video|audio)player(?:_size-[LMS])?'
    _VALID_URL = r'(?P<url>https?://www\d?\.(?:wdr\d?|funkhauseuropa)\.de/)(?P<id>.+?)(?P<player>%s)?\.html' % _PLAYER_REGEX

    _TESTS = [
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/servicezeit/videoservicezeit560-videoplayer_size-L.html',
            'info_dict': {
                'id': 'mdb-362427',
                'ext': 'flv',
                'title': 'Servicezeit',
                'description': 'md5:c8f43e5e815eeb54d0b96df2fba906cb',
                'upload_date': '20140310',
                'is_live': False
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Page Not Found',
        },
        {
            'url': 'http://www1.wdr.de/themen/av/videomargaspiegelisttot101-videoplayer.html',
            'info_dict': {
                'id': 'mdb-363194',
                'ext': 'flv',
                'title': 'Marga Spiegel ist tot',
                'description': 'md5:2309992a6716c347891c045be50992e4',
                'upload_date': '20140311',
                'is_live': False
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'Page Not Found',
        },
        {
            'url': 'http://www1.wdr.de/themen/kultur/audioerlebtegeschichtenmargaspiegel100-audioplayer.html',
            'md5': '83e9e8fefad36f357278759870805898',
            'info_dict': {
                'id': 'mdb-194332',
                'ext': 'mp3',
                'title': 'Erlebte Geschichten: Marga Spiegel (29.11.2009)',
                'description': 'md5:2309992a6716c347891c045be50992e4',
                'upload_date': '20091129',
                'is_live': False
            },
        },
        {
            'url': 'http://www.funkhauseuropa.de/av/audioflaviacoelhoamaramar100-audioplayer.html',
            'md5': '99a1443ff29af19f6c52cf6f4dc1f4aa',
            'info_dict': {
                'id': 'mdb-478135',
                'ext': 'mp3',
                'title': 'Flavia Coelho: Amar é Amar',
                'description': 'md5:7b29e97e10dfb6e265238b32fa35b23a',
                'upload_date': '20140717',
                'is_live': False
            },
            'skip': 'Page Not Found',
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/quarks_und_co/filterseite-quarks-und-co100.html',
            'playlist_mincount': 146,
            'info_dict': {
                'id': 'mediathek/video/sendungen/quarks_und_co/filterseite-quarks-und-co100',
            }
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/livestream/index.html',
            'info_dict': {
                'id': 'mdb-103364',
                'title': 're:^WDR Fernsehen Live [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
                'description': 'md5:ae2ff888510623bf8d4b115f95a9b7c9',
                'ext': 'flv',
                'upload_date': '20150101',
                'is_live': True
            },
            'params': {
                'skip_download': True,
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_url = mobj.group('url')
        page_id = mobj.group('id')

        webpage = self._download_webpage(url, page_id)

        if mobj.group('player') is None:
            entries = [
                self.url_result(page_url + href, 'WDR')
                for href in re.findall(
                    r'<a href="/?(.+?%s\.html)" rel="nofollow"' % self._PLAYER_REGEX,
                    webpage)
            ]

            if entries:  # Playlist page
                return self.playlist_result(entries, page_id)

            # Overview page
            entries = []
            for page_num in itertools.count(2):
                hrefs = re.findall(
                    r'<li class="mediathekvideo"\s*>\s*<img[^>]*>\s*<a href="(/mediathek/video/[^"]+)"',
                    webpage)
                entries.extend(
                    self.url_result(page_url + href, 'WDR')
                    for href in hrefs)
                next_url_m = re.search(
                    r'<li class="nextToLast">\s*<a href="([^"]+)"', webpage)
                if not next_url_m:
                    break
                next_url = page_url + next_url_m.group(1)
                webpage = self._download_webpage(
                    next_url, page_id,
                    note='Downloading playlist page %d' % page_num)
            return self.playlist_result(entries, page_id)

        flashvars = compat_parse_qs(self._html_search_regex(
            r'<param name="flashvars" value="([^"]+)"', webpage, 'flashvars'))

        page_id = flashvars['trackerClipId'][0]
        video_url = flashvars['dslSrc'][0]
        title = flashvars['trackerClipTitle'][0]
        thumbnail = flashvars['startPicture'][0] if 'startPicture' in flashvars else None
        is_live = flashvars.get('isLive', ['0'])[0] == '1'

        if is_live:
            title = self._live_title(title)

        if 'trackerClipAirTime' in flashvars:
            upload_date = flashvars['trackerClipAirTime'][0]
        else:
            upload_date = self._html_search_meta(
                'DC.Date', webpage, 'upload date')

        if upload_date:
            upload_date = unified_strdate(upload_date)

        formats = []
        preference = qualities(['S', 'M', 'L', 'XL'])

        if video_url.endswith('.f4m'):
            formats.extend(self._extract_f4m_formats(
                video_url + '?hdcore=3.2.0&plugin=aasp-3.2.0.77.18', page_id,
                f4m_id='hds', fatal=False))
        elif video_url.endswith('.smil'):
            formats.extend(self._extract_smil_formats(
                video_url, page_id, False, {
                    'hdcore': '3.3.0',
                    'plugin': 'aasp-3.3.0.99.43',
                }))
        else:
            formats.append({
                'url': video_url,
                'http_headers': {
                    'User-Agent': 'mobile',
                },
            })

        m3u8_url = self._search_regex(
            r'rel="adaptiv"[^>]+href="([^"]+)"',
            webpage, 'm3u8 url', default=None)
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, page_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        direct_urls = re.findall(
            r'rel="web(S|M|L|XL)"[^>]+href="([^"]+)"', webpage)
        if direct_urls:
            for quality, video_url in direct_urls:
                formats.append({
                    'url': video_url,
                    'preference': preference(quality),
                    'http_headers': {
                        'User-Agent': 'mobile',
                    },
                })

        self._sort_formats(formats)

        description = self._html_search_meta('Description', webpage, 'description')

        return {
            'id': page_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'is_live': is_live
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
    _VALID_URL = r'https?://(?:www\.)?wdrmaus\.de/(?:[^/]+/){,2}(?P<id>[^/?#]+)(?:/index\.php5|(?<!index)\.php5|/(?:$|[?#]))'
    IE_DESC = 'Sendung mit der Maus'
    _TESTS = [{
        'url': 'http://www.wdrmaus.de/aktuelle-sendung/index.php5',
        'info_dict': {
            'id': 'aktuelle-sendung',
            'ext': 'mp4',
            'thumbnail': 're:^http://.+\.jpg',
            'upload_date': 're:^[0-9]{8}$',
            'title': 're:^[0-9.]{10} - Aktuelle Sendung$',
        }
    }, {
        'url': 'http://www.wdrmaus.de/sachgeschichten/sachgeschichten/40_jahre_maus.php5',
        'md5': '3b1227ca3ed28d73ec5737c65743b2a3',
        'info_dict': {
            'id': '40_jahre_maus',
            'ext': 'mp4',
            'thumbnail': 're:^http://.+\.jpg',
            'upload_date': '20131007',
            'title': '12.03.2011 - 40 Jahre Maus',
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
