# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
import os
from ..utils import (
    js_to_json,
    urljoin,
)


class ReshetIE(InfoExtractor):
    _VALID_URL = r'https?://13tv\.co\.il/(?:(?:item/)?[^/]+/[^/]+/[^/]+/[^/]+(?:/(?P<id>[^/]+))?/?|live/?)'

    _TEST = {
        'url': 'https://13tv.co.il/item/entertainment/gav-hauma/season-10/episodes/jz1a1-1028855',
        'note': 'Test URL extraction',
        'info_dict': {
            'id': '6015811232001',
            'ext': 'mp4',
            'timestamp': 1553031049,
            'title': 'entertainment-gav-hauma-season-10-episodes-10-full_au8bmF8M',
            'uploader_id': '1551111274001',
            'upload_date': '20190319',
        }
    }

    def _real_extract(self, url):
        if re.search('live/?$', url):
            reshet_id = 'live'
        else:
            reshet_id = self._match_id(url)

        page = self._download_webpage(url, reshet_id)

        data = self._parse_json(re.search(r'window.data_query = (.*?).data_query;\n', page).group(1), reshet_id)

        liveId = data.get('header', {}).get('Live', {}).get('videoId')
        curItem = data.get('curItem')

        if liveId is None and curItem is None:
            # create a playlist result
            entries = []

            for item in data['items'].values():
                if item.get('video') is None:
                    continue

                entries.append(self.url_result(item['link'],
                                               video_id=item['post_ID'],
                                               video_title=item['title']))

            return self.playlist_result(entries)

        main_js_url = urljoin(url, re.search(r'<script type="text/javascript" src="(/[^"]*/main.[a-f0-9]+\.js)">', page).group(1))
        js = self._download_webpage(main_js_url, reshet_id)

        ccid = re.search('"data-ccid":"(.*?)"', js).group(1)

        if curItem is not None:
            item = data['items'][str(data['curItem'])]
            ref = item['video']['videoRef']
            video_info = self._download_json('https://13tv-api.oplayer.io/api/getlink/getVideoByFileName?userId=%s&videoName=%s&serverType=web' % (ccid, ref), ref)

            v = video_info[0]
            base_name, ext = os.path.splitext(v['MediaFile'])
            cdn_url = ''.join((v['ProtocolType'], v['ServerAddress'], v['MediaRoot'], base_name, v['Bitrates'], ext, v['StreamingType'], v['Token']))

            return {
                'id': str(item['video']['videoID']),
                'title': ref,
                'formats': self._extract_m3u8_formats(cdn_url, ref, 'mp4')
            }
        elif liveId is not None:
            liveName = liveId.split(':')[1]
            config_js = self._download_webpage('https://13tv.co.il/wp-content/themes/reshet_tv/build/config.min.js', reshet_id)
            config = self._parse_json(js_to_json(re.fullmatch('.*?=(.*);', config_js).group(1)), reshet_id)
            channel = config['liveRefId'][liveName]['ch']
            video_info = self._download_json('https://13tv-api.oplayer.io/api/getlink/?userId=%s&serverType=web&ch=%s&cdnName=casttime' % (ccid, channel), reshet_id)
            video_url = video_info[0]['Link']
            return {
                'id': str(channel),
                'title': liveName,
                'formats': self._extract_m3u8_formats(video_url, liveName, 'mp4')
            }
