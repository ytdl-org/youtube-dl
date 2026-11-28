# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from time import mktime, strptime


class HSE24IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hse24\.de/dpl/(?:p/product|c/tv-shows)?/(?P<id>[0-9]+)'
    _GEO_COUNTRIES = ['DE']
    _TESTS = [{
        'url': 'https://www.hse24.de/dpl/c/tv-shows/476357',
        'info_dict': {
            'id': '476357',
            'ext': 'mp4',
            'title': 'Jürgen Hirsch Schuhe zum Wohlfühlen',
            'timestamp': 1604926800,
            'upload_date': '20201109',
            'channel': 'HSE24EXTRA',
            'uploader': 'Daniela Elger'
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.hse24.de/dpl/p/product/408630',
        'info_dict': {
            'id': '408630',
            'ext': 'mp4',
            'title': 'Hose im Ponte-Mix',
            'timestamp': 1603058400,
            'upload_date': '20201018',
            'channel': 'HSE24',
            'uploader': 'Judith Williams'
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        json_str = self._html_search_regex(r'window\.__REDUX_DATA__ = ({.*});?', webpage, 'json_str')
        json_str = json_str.replace('\n', '')
        json_data = self._parse_json(json_str, video_id)

        formats = []
        if 'tvShow' in json_data:  # /dpl/c/tv-shows
            show = json_data['tvShow']['tvShow']
            title, date, hour, uploader = show['title'], show['date'], show['hour'], show['presenter']
            channel = self._search_regex(r'tvShow \| ([A-Z0-9]+)_', show['actionFieldText'], video_id)
            timestamp = mktime(strptime(' '.join((date, hour)), '%Y-%m-%d %H'))

            video = json_data['tvShow']['tvShowVideo']
            thumbnail = video['poster']
            sources = video['sources']
            for src in sources:
                if src['mimetype'] == 'application/x-mpegURL':
                    formats.extend(self._extract_m3u8_formats(src['url'], video_id, ext='mp4'))
        elif 'productDetail' in json_data:  # /dpl/p/product
            product = json_data['productDetail']['product']
            title, uploader = product['name']['short'], product['brand']['brandName']
            channel = 'HSE24'
            default_time = '2001-01-01T01:01:01+0100'
            time = product['variants'][0]['price']['validFrom'] if len(product['variants']) > 0 else default_time
            # python2 compatibility (no %z directive support)
            time = strptime(time[:-6], '%Y-%m-%dT%H:%M:%S')
            if time[-6] == '+':
                time += strptime(time[-6:], '%H:%M')
            elif time[-6] == '-':
                time -= strptime(time[-6:], '%H:%M')
            timestamp = mktime(time)

            for video in json_data['productContent']['productContent']['videos']:
                thumbnail = video['poster']
                sources = video['sources']
                for src in sources:
                    if src['mimetype'] == 'application/x-mpegURL':
                        formats.extend(self._extract_m3u8_formats(src['url'], video_id, ext='mp4'))
                    # elif src['mimetype'] == 'video/mp4':
                    #     formats.append({'url': src['url']})

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'timestamp': int(timestamp),
            'thumbnail': thumbnail,
            'channel': channel,
            'uploader': uploader
        }
