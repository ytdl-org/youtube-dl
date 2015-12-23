# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
)

class TheInterceptIE(InfoExtractor):
    _VALID_URL = r'https://theintercept.com/fieldofvision/(?P<id>.+?)/'
    _TESTS = [{
        'url': 'https://theintercept.com/fieldofvision/thisisacoup-episode-four-surrender-or-die/',
        'info_dict': {
            'id': 'thisisacoup-episode-four-surrender-or-die',
            'ext': 'mp4',
            'title': '#ThisIsACoup – Episode Four: Surrender or Die',
            'upload_date': '20151218',
            'description': 'md5:74dd27f0e2fbd50817829f97eaa33140',
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        mobj = re.search(r'initialStoreTree =(?P<json_data>.+})', webpage)
        if mobj is None:
            raise ExtractorError('Unable to extract initialStoreTree')
        json_data = self._parse_json(mobj.group('json_data'), display_id)

        info = None
        for post in json_data['resources']['posts'].values():
            if post['slug'] == display_id:
                info = post
                break
        if info is None:
            raise ExtractorError('Unable to find info for %s'%display_id)

        title = info['title']
        description = info['excerpt']
        upload_date = info['date'][:10].replace('-', '')
        video_id = info['fov_videoid']
        creator = ','.join([a['display_name'] for a in info['authors']])
        thumbnail = self._og_search_property('image', webpage)
        content_id = thumbnail.split('/')[-1].split('.')[0]
        content_url = 'https://content.jwplatform.com/jw6/{content_id}.xml'.format(content_id=content_id)
        content = self._download_xml(content_url, video_id)

        formats = []
        for source in content.findall('.//{http://rss.jwpcdn.com/}source'):
            if source.attrib['file'].endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(
                    source.attrib['file'], video_id, 'mp4', preference=1, m3u8_id='hls'))

        return {
            'creator': creator,
            'description': description,
            'display_id': display_id,
            'formats': formats,
            'id': video_id,
            'id': video_id,
            'thumbnail': thumbnail,
            'title': title,
            'upload_date': upload_date,
        }
