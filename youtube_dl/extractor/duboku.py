# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import *


class DubokuIE(InfoExtractor):
    _VALID_URL = r'(?:https?://[^/]+\.duboku\.co/vodplay/)(?P<id>[0-9\-]+)\.html.*'
    _TESTS = [{
        'url': 'https://www.duboku.co/vodplay/1575-1-1.html',
        'info_dict': {
            'id': '1575-1-1',
            'title': '白色月光',
            'season': 1,
            'episode': 1,
        },
        'params': {
            'skip_download': 'm3u8 download',
        },
    }]

    _PLAYER_DATA_PATTERN = r'player_data\s*=\s*(\{\s*(.*)})\s*;?\s*</script'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        temp = video_id.split('-')
        series_id = temp[0]
        season_id = temp[1]
        episode_id = temp[2]

        webpage_url = 'https://www.duboku.co/vodplay/%s.html' % video_id
        webpage_html = self._download_webpage(webpage_url, video_id)

        # extract video url

        player_data = self._search_regex(
            self._PLAYER_DATA_PATTERN, webpage_html, 'player_data')
        player_data = self._parse_json(js_to_json(player_data), video_id)

        # extract title

        temp = get_elements_by_class('title', webpage_html)
        series_title = None
        title = None
        for html in temp:
            mobj = re.search(r'<a\s+.*>(.*)</a>', html)
            if mobj:
                href = extract_attributes(mobj.group(0)).get('href')
                if href:
                    mobj1 = re.search(r'/(\d+)\.html', href)
                    if mobj1 and mobj1.group(1) == series_id:
                        series_title = clean_html(mobj.group(0))
                        series_title = re.sub(r'[\s\r\n\t]+', ' ', series_title)
                        title = clean_html(html)
                        title = re.sub(r'[\s\r\n\t]+', ' ', title)
                        break

        data_url = player_data['url']
        assert data_url
        data_from = player_data.get('from')

        # if it is an embedded iframe, maybe it's an external source
        if data_from == 'iframe':
            # use _type url_transparent to retain the meaningful details
            # of the video.
            return {
                '_type': 'url_transparent',
                'url': smuggle_url(data_url, {'http_headers': {'Referer': webpage_url}}),
                'id': video_id,
                'title': title,
                'series': series_title,
                'season_number': int_or_none(season_id),
                'season_id': season_id,
                'episode_number': int_or_none(episode_id),
                'episode_id': episode_id,
            }

        formats = self._extract_m3u8_formats(data_url, video_id, 'ts')

        return {
            'id': video_id,
            'title': title,
            'series': series_title,
            'season_number': int_or_none(season_id),
            'season_id': season_id,
            'episode_number': int_or_none(episode_id),
            'episode_id': episode_id,
            'formats': formats,
        }
