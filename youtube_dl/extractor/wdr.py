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
    determine_ext,
    unified_strdate,
    qualities
)


class WDRIE(InfoExtractor):
    _PLAYER_REGEX = '-(?:video|audio)player(?:_size-[LMS])?'
    _VALID_URL = r'(?P<url>https?://www\d?\.(?:wdr\d?|funkhauseuropa)\.de/)(?P<id>.+?)(?P<player>%s)?\.html' % _PLAYER_REGEX

    _TESTS = [
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/hier_und_heute/videostreetfoodpioniere100.html',  # Test single media extraction (video, link to webpage)
            'info_dict': {
                'id': 'mdb-750693',
                'ext': 'mp4',
                'title': 'HIER UND HEUTE: Streetfood-Pioniere',
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
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/hier_und_heute/videostreetfoodpioniere100-videoplayer_size-L.html',  # Test single media extraction (video, link to playerpage)
            'info_dict': {
                'id': 'mdb-750693',
                'ext': 'mp4',
                'title': 'HIER UND HEUTE: Streetfood-Pioniere',
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
            'url': 'http://www1.wdr.de/mediathek/audio/1live/einslive-bahnansage-100.html',  # Test single media extraction (audio)
            'md5': '87c389aac18ee6fc041aa1ced52aac76',
            'info_dict': {
                'id': 'mdb-726385',
                'ext': 'mp3',
                'title': '1LIVE Bahnansage',
                'description': 'md5:8b9ef2af8c1bb01394ab98f3450ff04d',
                'upload_date': '20150604',
                'is_live': False
            },
        },
        {
            'url': 'http://www.funkhauseuropa.de/av/audioroskildefestival100-audioplayer.html',  # Test single media extraction (audio)
            'md5': 'e50e0c8900f6558ae12cd9953aca5a20',
            'info_dict': {
                'id': 'mdb-752045',
                'ext': 'mp3',
                'title': 'Roskilde Festival 2015',
                'description': 'md5:7b29e97e10dfb6e265238b32fa35b23a',
                'upload_date': '20150702',
                'is_live': False
            },
        },
        {
            'url': 'http://www.funkhauseuropa.de/themen/aktuell/zwanzig-jahre-mpdrei-100.html',  # Test single media extraction (audio)
            'md5': 'a0966afb15714a5c5a364b8d36a6e721',
            'info_dict': {
                'id': 'mdb-762163',
                'ext': 'mp3',
                'title': '20 Jahre mp3',
                'description': 'md5:5b1d78b210443081e9a08a9d0fb78306',
                'upload_date': '20150714',
                'is_live': False
            },
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/sendungen/quarks_und_co/filterseite-quarks-und-co100.html',  # Test playlist extraction (containing links to webpages)
            'playlist_mincount': 146,
            'info_dict': {
                'id': 'mediathek/video/sendungen/quarks_und_co/filterseite-quarks-und-co100',
                'title': 'md5:acf18a9eb2e3342d05de07380f1672b4'
            }
        },
        {
            'url': 'http://www.funkhauseuropa.de/index.html',  # Test playlist extraction (containing links to playerpages)
            'playlist_mincount': 3,
            'info_dict': {
                'id': 'index',
            }
        },
        {
            'url': 'http://www1.wdr.de/mediathek/video/livestream/index.html',  # Test live tv
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

    def _playlist_extract(self, page_url, page_id, webpage):
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
            return self.playlist_result(entries, page_id, webpage)

    def _media_extract(self, page_url, page_id, webpage, mobj=None, entrie=None):
        if entrie is not None:
            mobj = re.search(self._VALID_URL, entrie['url'])
            playerpage = self._download_webpage(entrie['url'], mobj.group('id') + mobj.group('player'))
        elif mobj is not None:
            playerpage = webpage
        formats = []
        flashvars = compat_parse_qs(
            self._html_search_regex(r'<param name="flashvars" value="([^"]+)"', playerpage, 'flashvars'))

        page_id = flashvars['trackerClipId'][0]
        video_url = flashvars['dslSrc'][0]
        title = flashvars['trackerClipTitle'][0]
        thumbnail = flashvars['startPicture'][0] if 'startPicture' in flashvars else None

        if thumbnail is not None:
            double_url_regex = r'(' + re.escape(page_url) + r'*){2,}'
            thumbnail = re.sub(double_url_regex, page_url, thumbnail)

        is_live = flashvars.get('isLive', ['0'])[0] == '1'

        if is_live:
            title = self._live_title(title)

        if 'trackerClipAirTime' in flashvars:
            upload_date = flashvars['trackerClipAirTime'][0]
        else:
            upload_date = self._html_search_meta('DC.Date', webpage, 'content')

        if upload_date:
            upload_date = unified_strdate(upload_date)

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

        formats.append({'ext': ext, 'url': video_url})

        m3u8_url = re.search(r'<li>\n<a rel="adaptiv" type="application/vnd\.apple\.mpegURL" href="(?P<link>.+?)"', playerpage)

        if m3u8_url is not None:
            m3u8_url = m3u8_url.group('link')
            formats.extend(self._extract_m3u8_formats(m3u8_url, page_id))

        quality = qualities(['webS', 'webM', 'webL_Lo', 'webL_Hi'])
        webL_first = True  # There are two videos tagged as webL. The first one is usually of better quality
        for video_vars in re.findall(r'<li>\n<a rel="(?P<format_id>web.?)"  href=".+?/(?P<link>fsk.+?)"', playerpage):
            format_id = video_vars[0]
            video_url = 'http://ondemand-ww.wdr.de/medstdp/' + video_vars[1]  # Just using the href results in a warning page (that tells you to install flash player) and not the actual media
            ext = determine_ext(video_url)
            if format_id == 'webL' and webL_first is True:
                format_id = 'webL_Hi'
                webL_first = False
            elif format_id == 'webL' and webL_first is False:
                format_id = 'webL_Lo'
            formats.append({'format_id': format_id, 'ext': ext, 'url': video_url, 'source_preference': quality(format_id)})

        self._sort_formats(formats)

        description = self._html_search_meta('Description', webpage, 'content')  # Using the webpage works better with funkhauseuropa

        return {
            'id': page_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'is_live': is_live
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_url = mobj.group('url')
        page_id = mobj.group('id')

        webpage = self._download_webpage(url, page_id)

        entries = [
            self.url_result(page_url + href, 'WDR')
            for href in re.findall(r'<a href="/?(.+?%s\.html)" rel="nofollow"' % self._PLAYER_REGEX, webpage)
        ]

        # The url doesn't seem to contain any information if the current page is a playlist or page with a single media item
        if not entries and mobj.group('player') is None:  # Playlist containing links to webpages
            return self._playlist_extract(page_url, page_id, webpage)

        elif entries and len(entries) > 1:  # Playlist containing multiple playerpages
            return self.playlist_result(entries, page_id)

        elif mobj.group('player') is not None:  # Mediaextractor (used if a playlist containes multiple playerpages)
            return self._media_extract(page_url, page_id, webpage, mobj=mobj)

        elif entries and len(entries) == 1:  # Mediaextractor (a page with a single video is usally not a playlist)
            return self._media_extract(page_url, page_id, webpage, entrie=entries[0])


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
