# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    unified_strdate,
)


class WDRIE(InfoExtractor):
    _PLAYER_REGEX = 'https?://deviceids-medstdp.wdr.de/ondemand/.+?/.+?\.js'
    _VALID_URL = r'(?P<url>https?://www\d?\.(?:wdr\d?|funkhauseuropa)\.de/)(?P<id>.+?)\.html'
    _TESTS = [
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/hier_und_heute/videostreetfoodpioniere100.html',
            'info_dict': {
                'id': 'mdb-750693',
                'ext': 'mp4',
                'title': 'Streetfood-Pioniere',
                'description': 'md5:bff1fdc6de7df044ac2bec13ab46e6a9',
                'upload_date': '20150703',
                'is_live': False
            },
            'params': {
                'skip_download': True,
                'format': 'best'
            },
        },
        {
            'url': 'http://www1.wdr.de/mediathek/audio/1live/einslive-bahnansage-100.html',
            'md5': '87c389aac18ee6fc041aa1ced52aac76',
            'info_dict': {
                'id': 'mdb-726385',
                'ext': 'mp3',
                'title': 'Weselsky | 1LIVE Bahnansage (04.06.2015)',
                'description': 'md5:8b9ef2af8c1bb01394ab98f3450ff04d',
                'upload_date': '20150604',
                'is_live': False
            },
        },
        {
            'url': 'http://www.funkhauseuropa.de/musik/musikspecials/roskilde-zweitausendfuenfzehn-100.html',
            'md5': 'e50e0c8900f6558ae12cd9953aca5a20',
            'info_dict': {
                'id': 'mdb-752045',
                'ext': 'mp3',
                'title': 'Roskilde Festival 2015',
                'description': 'md5:48e7a0a884c0e841a9d9174e27c67df3',
                'upload_date': '20150702',
                'is_live': False
            },
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
                'title': 're:^24 Stunden Livestream [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
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

    def _overiew_page_extractor(self, page_url, page_id, webpage):
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

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_url = mobj.group('url')
        page_id = mobj.group('id')

        webpage = self._download_webpage(url, page_id)
        entries = re.search(r'%s' % self._PLAYER_REGEX, webpage)

        if entries is None:  # Overview page
            return self._overiew_page_extractor(page_url, page_id, webpage)

        jsonpage = self._download_webpage(entries.group(0), entries.group(0))
        jsonvars = json.loads(jsonpage[38:-2])

        page_id = jsonvars['trackerData']['trackerClipId']
        title = jsonvars['trackerData']['trackerClipTitle']
        formats = []
        for _id, video_field in jsonvars['mediaResource'].items():
            if 'videoURL' in video_field:
                video_url = video_field['videoURL']
            elif 'audioURL' in video_field:
                video_url = video_field['audioURL']
            else:
                break
            is_live = video_field.get('flashvarsExt', {'isLive': '0'})
            is_live = is_live.get('isLive', '0') == '1'

            if video_url.endswith('.f4m'):
                video_url += '?hdcore=3.2.0&plugin=aasp-3.2.0.77.18'
                ext = 'flv'
            elif video_url.endswith('.smil'):
                fmt = self._extract_smil_formats(video_url, page_id)[0]
                video_url = fmt['url']
                sep = '&' if '?' in video_url else '?'
                video_url += sep
                video_url += 'hdcore=3.3.0&plugin=aasp-3.3.0.99.43'
                ext = fmt['ext']
            else:
                ext = determine_ext(video_url)

            formats.append({'url': video_url, 'ext': ext, 'format_id': _id})

        thumbnail = re.search('<div class="illustrationCont w960">\n<div class="linkCont">\n<img src="(?P<thumbnail>.+?)"', webpage)
        if thumbnail is not None:
            thumbnail = page_url + thumbnail.group('thumbnail')

        if is_live:
            title = self._live_title(title)

        if 'trackerClipAirTime' in jsonvars['trackerData']:
            upload_date = jsonvars['trackerData']['trackerClipAirTime']
        else:
            upload_date = self._html_search_meta('DC.Date', webpage, 'content')

        if upload_date:
            upload_date = unified_strdate(upload_date)

        description = self._html_search_meta('Description', webpage, 'content')

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
    _VALID_URL = 'http://(?:www\.)?wdrmaus\.de/(?:[^/]+/){,2}(?P<id>[^/?#]+)(?:/index\.php5|(?<!index)\.php5|/(?:$|[?#]))'
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
