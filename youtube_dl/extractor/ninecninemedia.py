# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    parse_duration,
    ExtractorError
)


class NineCNineMediaIE(InfoExtractor):
    _VALID_URL = r'9c9media:(?P<destination_code>[^:]+):(?P<id>\d+)'

    def _real_extract(self, url):
        destination_code, video_id = re.match(self._VALID_URL, url).groups()
        api_base_url = 'http://capi.9c9media.com/destinations/%s/platforms/desktop/contents/%s/' % (destination_code, video_id)
        content = self._download_json(api_base_url, video_id, query={
            '$include': '[contentpackages]',
        })
        title = content['Name']
        if len(content['ContentPackages']) > 1:
            raise ExtractorError('multiple content packages')
        content_package = content['ContentPackages'][0]
        stacks_base_url = api_base_url + 'contentpackages/%s/stacks/' % content_package['Id']
        stacks = self._download_json(stacks_base_url, video_id)['Items']
        if len(stacks) > 1:
            raise ExtractorError('multiple stacks')
        stack = stacks[0]
        stack_base_url = '%s%s/manifest.' % (stacks_base_url, stack['Id'])
        formats = []
        formats.extend(self._extract_m3u8_formats(
            stack_base_url + 'm3u8', video_id, 'mp4',
            'm3u8_native', m3u8_id='hls', fatal=False))
        formats.extend(self._extract_f4m_formats(
            stack_base_url + 'f4m', video_id,
            f4m_id='hds', fatal=False))
        mp4_url = self._download_webpage(stack_base_url + 'pd', video_id, fatal=False)
        if mp4_url:
            formats.append({
                'url': mp4_url,
                'format_id': 'mp4',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': content.get('Desc') or content.get('ShortDesc'),
            'timestamp': parse_iso8601(content.get('BroadcastDateTime')),
            'duration': parse_duration(content.get('BroadcastTime')),
            'formats': formats,
        }
