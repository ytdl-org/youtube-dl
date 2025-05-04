# coding: utf-8
from __future__ import unicode_literals

import re
import datetime
import calendar
import json

from .common import InfoExtractor
from ..utils import js_to_json, int_or_none


class CNBCIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cnbc\.com(?P<path>/video/(?:[^/]+/)+(?P<id>[^./?#&]+)\.html)'
    _TEST = {
        'url': 'https://www.cnbc.com/video/2020/07/06/gary-shilling-why-the-stock-market-could-be-set-for-a-big-decline.html',
        'info_dict': {
            'id': 'gary-shilling-why-the-stock-market-could-be-set-for-a-big-decline',
            'ext': 'mp4',
            'title': 'Gary Shilling: Why the stock market could be set for a big decline',
            'alt_title': 'Why the stock market could be set for a big decline, according to financial analyst Gary Shilling',
            'description': 'Financial analyst Gary Shilling says the stock market could be set for a big pullback similar to the decline in the 1930s during the Great Depression. He explains how the coronavirus pandemic will result in long-term changes in the economy.',
            'thumbnail': 'https://image.cnbcfm.com/api/v1/image/106592286-gettyimages-103220190.jpg?v=1594046174',
            'uploader': 'NBCU-CNBC',
            'timestamp': 1594046033,
            'upload_date': '20200706',
            'duration': 658
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        path, video_id = re.match(self._VALID_URL, url).groups()
        video_webpage = self._download_webpage(
            url,
            video_id,
            note='Downloading webpage to get video info'
        )
        video_info_js = self._search_regex(
            r'window.__s_data=(.*); window.__c_data=',
            video_webpage,
            's_data',
        )
        video_info = json.loads(js_to_json(video_info_js))
        core_data = None
        for layout in video_info['page']['page']['layout']:
            for column in layout['columns']:
                data = column['modules'][0]['data']
                if 'playbackURL' not in data:
                    continue
                else:
                    core_data = data
                    break
            if core_data:
                break
        formats = []
        m3u8_url = core_data['playbackURL'].replace('\u002F', '/')
        for entry in self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4', m3u8_id='m3u8'):
            mobj = re.search(r'(?P<tag>(?:-p|-b)).m3u8', entry['url'])
            if mobj:
                entry['format_id'] += mobj.group('tag')
            formats.append(entry)
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': core_data['seoTitle'],
            'alt_title': core_data['title'],
            'description': core_data['description'],
            'formats': formats,
            'thumbnail': core_data['thumbnail'].replace('\u002F', '/'),
            'uploader': 'NBCU-CNBC',
            'timestamp': calendar.timegm(datetime.datetime.strptime(
                core_data['dateFirstPublished'],
                "%Y-%m-%dT%H:%M:%S+0000"
            ).timetuple()),
            'upload_date': core_data['dateFirstPublished'][:10].replace('-', ''),
            'duration': int_or_none(core_data['duration'])
        }


class CNBCPlayerIE(InfoExtractor):
    _VALID_URL = r'https?://player.cnbc.com/p/gZWlPC/cnbc_global\?playertype=synd&byGuid=(?P<id>[0-9]+)&?.*'
    _TEST = {
        'url': 'https://player.cnbc.com/p/gZWlPC/cnbc_global?playertype=synd&byGuid=7000142698',
        'info_dict': {
            'id': '7000142698',
            'ext': 'mp4',
            'title': 'Gary Shilling: Why the stock market could be set for a big decline',
            'alt_title': 'Why the stock market could be set for a big decline, according to financial analyst Gary Shilling',
            'description': 'Financial analyst Gary Shilling says the stock market could be set for a big pullback similar to the decline in the 1930s during the Great Depression. He explains how the coronavirus pandemic will result in long-term changes in the economy.',
            'thumbnail': 'https://image.cnbcfm.com/api/v1/image/106592286-gettyimages-103220190.jpg?v=1594046174',
            'uploader': 'NBCU-CNBC',
            'timestamp': 1594046033,
            'upload_date': '20200706',
            'duration': 658
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id, = re.match(self._VALID_URL, url).groups()
        url = 'https://player.cnbc.com/p/gZWlPC/cnbc_global?playertype=synd&byGuid=%s' % video_id
        video_webpage = self._download_webpage(
            url,
            video_id,
            note='Downloading webpage to get video info'
        )
        video_info = self._search_json(
            '<script id="__NEXT_DATA__" type="application/json">',
            video_webpage,
            'next_data',
            video_id,
        )
        formats = []
        m3u8_url = video_info['props']['pageProps']['videoData']['playbackURL']
        for entry in self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4', m3u8_id='m3u8'):
            mobj = re.search(r'(?P<tag>(?:-p|-b)).m3u8', entry['url'])
            if mobj:
                entry['format_id'] += mobj.group('tag')
            formats.append(entry)
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': video_info['props']['pageProps']['videoData']['seoTitle'],
            'alt_title': video_info['props']['pageProps']['videoData']['title'],
            'description': video_info['props']['pageProps']['videoData']['description'],
            'formats': formats,
            'thumbnail': video_info['props']['pageProps']['videoData']['image']['url'],
            'uploader': 'NBCU-CNBC',
            'timestamp': calendar.timegm(datetime.datetime.strptime(
                video_info['props']['pageProps']['videoData']['dateFirstPublished'],
                "%Y-%m-%dT%H:%M:%S+0000"
            ).timetuple()),
            'upload_date': video_info['props']['pageProps']['videoData']['dateFirstPublished'][:10].replace('-', ''),
            'duration': int_or_none(video_info['props']['pageProps']['videoData']['duration'])
        }
