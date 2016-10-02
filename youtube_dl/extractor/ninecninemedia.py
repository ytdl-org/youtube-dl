# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    parse_iso8601,
    float_or_none,
    ExtractorError,
    int_or_none,
)


class NineCNineMediaBaseIE(InfoExtractor):
    _API_BASE_TEMPLATE = 'http://capi.9c9media.com/destinations/%s/platforms/desktop/contents/%s/'


class NineCNineMediaStackIE(NineCNineMediaBaseIE):
    IE_NAME = '9c9media:stack'
    _VALID_URL = r'9c9media:stack:(?P<destination_code>[^:]+):(?P<content_id>\d+):(?P<content_package>\d+):(?P<id>\d+)'

    def _real_extract(self, url):
        destination_code, content_id, package_id, stack_id = re.match(self._VALID_URL, url).groups()
        stack_base_url_template = self._API_BASE_TEMPLATE + 'contentpackages/%s/stacks/%s/manifest.'
        stack_base_url = stack_base_url_template % (destination_code, content_id, package_id, stack_id)

        formats = []
        formats.extend(self._extract_m3u8_formats(
            stack_base_url + 'm3u8', stack_id, 'mp4',
            'm3u8_native', m3u8_id='hls', fatal=False))
        formats.extend(self._extract_f4m_formats(
            stack_base_url + 'f4m', stack_id,
            f4m_id='hds', fatal=False))
        mp4_url = self._download_webpage(stack_base_url + 'pd', stack_id, fatal=False)
        if mp4_url:
            formats.append({
                'url': mp4_url,
                'format_id': 'mp4',
            })
        self._sort_formats(formats)

        return {
            'id': stack_id,
            'formats': formats,
        }


class NineCNineMediaIE(NineCNineMediaBaseIE):
    IE_NAME = '9c9media'
    _VALID_URL = r'9c9media:(?P<destination_code>[^:]+):(?P<id>\d+)'

    def _real_extract(self, url):
        destination_code, content_id = re.match(self._VALID_URL, url).groups()
        api_base_url = self._API_BASE_TEMPLATE % (destination_code, content_id)
        content = self._download_json(api_base_url, content_id, query={
            '$include': '[Media,Season,ContentPackages]',
        })
        title = content['Name']
        if len(content['ContentPackages']) > 1:
            raise ExtractorError('multiple content packages')
        content_package = content['ContentPackages'][0]
        package_id = content_package['Id']
        content_package_url = api_base_url + 'contentpackages/%s/' % package_id
        content_package = self._download_json(content_package_url, content_id)

        if content_package.get('Constraints', {}).get('Security', {}).get('Type') == 'adobe-drm':
            raise ExtractorError('This video is DRM protected.', expected=True)

        stacks = self._download_json(content_package_url + 'stacks/', package_id)['Items']
        multistacks = len(stacks) > 1

        thumbnails = []
        for image in content.get('Images', []):
            image_url = image.get('Url')
            if not image_url:
                continue
            thumbnails.append({
                'url': image_url,
                'width': int_or_none(image.get('Width')),
                'height': int_or_none(image.get('Height')),
            })

        tags, categories = [], []
        for source_name, container in (('Tags', tags), ('Genres', categories)):
            for e in content.get(source_name, []):
                e_name = e.get('Name')
                if not e_name:
                    continue
                container.append(e_name)

        description = content.get('Desc') or content.get('ShortDesc')
        season = content.get('Season', {})
        base_info = {
            'description': description,
            'timestamp': parse_iso8601(content.get('BroadcastDateTime')),
            'episode_number': int_or_none(content.get('Episode')),
            'season': season.get('Name'),
            'season_number': season.get('Number'),
            'season_id': season.get('Id'),
            'series': content.get('Media', {}).get('Name'),
            'tags': tags,
            'categories': categories,
        }

        entries = []
        for stack in stacks:
            stack_id = compat_str(stack['Id'])
            entry = {
                '_type': 'url_transparent',
                'url': '9c9media:stack:%s:%s:%s:%s' % (destination_code, content_id, package_id, stack_id),
                'id': stack_id,
                'title': '%s_part%s' % (title, stack['Name']) if multistacks else title,
                'duration': float_or_none(stack.get('Duration')),
                'ie_key': 'NineCNineMediaStack',
            }
            entry.update(base_info)
            entries.append(entry)

        return {
            '_type': 'multi_video',
            'id': content_id,
            'title': title,
            'description': description,
            'entries': entries,
        }
