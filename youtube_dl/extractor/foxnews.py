from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_iso8601,
    int_or_none,
)


class FoxNewsIE(InfoExtractor):
    IE_DESC = 'Fox News and Fox Business Video'
    _VALID_URL = r'https?://(?P<host>video\.fox(?:news|business)\.com)/v/(?:video-embed\.html\?video_id=)?(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://video.foxnews.com/v/3937480/frozen-in-time/#sp=show-clips',
            'md5': '32aaded6ba3ef0d1c04e238d01031e5e',
            'info_dict': {
                'id': '3937480',
                'ext': 'flv',
                'title': 'Frozen in Time',
                'description': 'Doctors baffled by 16-year-old girl that is the size of a toddler',
                'duration': 265,
                'timestamp': 1304411491,
                'upload_date': '20110503',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://video.foxnews.com/v/3922535568001/rep-luis-gutierrez-on-if-obamas-immigration-plan-is-legal/#sp=show-clips',
            'md5': '5846c64a1ea05ec78175421b8323e2df',
            'info_dict': {
                'id': '3922535568001',
                'ext': 'mp4',
                'title': "Rep. Luis Gutierrez on if Obama's immigration plan is legal",
                'description': "Congressman discusses the president's executive action",
                'duration': 292,
                'timestamp': 1417662047,
                'upload_date': '20141204',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://video.foxnews.com/v/video-embed.html?video_id=3937480&d=video.foxnews.com',
            'only_matching': True,
        },
        {
            'url': 'http://video.foxbusiness.com/v/4442309889001',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')

        video = self._download_json(
            'http://%s/v/feed/video/%s.js?template=fox' % (host, video_id), video_id)

        item = video['channel']['item']
        title = item['title']
        description = item['description']
        timestamp = parse_iso8601(item['dc-date'])

        media_group = item['media-group']
        duration = None
        formats = []
        for media in media_group['media-content']:
            attributes = media['@attributes']
            video_url = attributes['url']
            if video_url.endswith('.f4m'):
                formats.extend(self._extract_f4m_formats(video_url + '?hdcore=3.4.0&plugin=aasp-3.4.0.132.124', video_id))
            elif video_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(video_url, video_id, 'flv'))
            elif not video_url.endswith('.smil'):
                duration = int_or_none(attributes.get('duration'))
                formats.append({
                    'url': video_url,
                    'format_id': media['media-category']['@attributes']['label'],
                    'preference': 1,
                    'vbr': int_or_none(attributes.get('bitrate')),
                    'filesize': int_or_none(attributes.get('fileSize'))
                })
        self._sort_formats(formats)

        media_thumbnail = media_group['media-thumbnail']['@attributes']
        thumbnails = [{
            'url': media_thumbnail['url'],
            'width': int_or_none(media_thumbnail.get('width')),
            'height': int_or_none(media_thumbnail.get('height')),
        }] if media_thumbnail else []

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'formats': formats,
            'thumbnails': thumbnails,
        }
