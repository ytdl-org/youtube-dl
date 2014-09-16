from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    strip_jsonp,
)


class WashingtonPostIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?washingtonpost\.com/.*?/(?P<id>[^/]+)/(?:$|[?#])'
    _TEST = {
        'url': 'http://www.washingtonpost.com/sf/national/2014/03/22/sinkhole-of-bureaucracy/',
        'info_dict': {
            'title': 'Sinkhole of bureaucracy',
        },
        'playlist': [{
            'md5': 'c3f4b4922ffa259243f68e928db2db8c',
            'info_dict': {
                'id': 'fc433c38-b146-11e3-b8b3-44b1d1cd4c1f',
                'ext': 'mp4',
                'title': 'Breaking Points: The Paper Mine',
                'duration': 1287,
                'description': 'Overly complicated paper pushing is nothing new to government bureaucracy. But the way federal retirement applications are filed may be the most outdated. David Fahrenthold explains.',
                'uploader': 'The Washington Post',
                'timestamp': 1395527908,
                'upload_date': '20140322',
            },
        }, {
            'md5': 'f645a07652c2950cd9134bb852c5f5eb',
            'info_dict': {
                'id': '41255e28-b14a-11e3-b8b3-44b1d1cd4c1f',
                'ext': 'mp4',
                'title': 'The town bureaucracy sustains',
                'description': 'Underneath the friendly town of Boyers is a sea of government paperwork. In a disused limestone mine, hundreds of locals now track, file and process retirement applications for the federal government. We set out to find out what it\'s like to do paperwork 230 feet underground.',
                'duration': 2217,
                'timestamp': 1395528005,
                'upload_date': '20140322',
                'uploader': 'The Washington Post',
            },
        }]
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_id = mobj.group('id')

        webpage = self._download_webpage(url, page_id)
        title = self._og_search_title(webpage)
        uuids = re.findall(r'data-video-uuid="([^"]+)"', webpage)
        entries = []
        for i, uuid in enumerate(uuids, start=1):
            vinfo_all = self._download_json(
                'http://www.washingtonpost.com/posttv/c/videojson/%s?resType=jsonp' % uuid,
                page_id,
                transform_source=strip_jsonp,
                note='Downloading information of video %d/%d' % (i, len(uuids))
            )
            vinfo = vinfo_all[0]['contentConfig']
            uploader = vinfo.get('credits', {}).get('source')
            timestamp = int_or_none(
                vinfo.get('dateConfig', {}).get('dateFirstPublished'), 1000)

            formats = [{
                'format_id': (
                    '%s-%s-%s' % (s.get('type'), s.get('width'), s.get('bitrate'))
                    if s.get('width')
                    else s.get('type')),
                'vbr': s.get('bitrate') if s.get('width') != 0 else None,
                'width': s.get('width'),
                'height': s.get('height'),
                'acodec': s.get('audioCodec'),
                'vcodec': s.get('videoCodec') if s.get('width') != 0 else 'none',
                'filesize': s.get('fileSize'),
                'url': s.get('url'),
                'ext': 'mp4',
                'protocol': {
                    'MP4': 'http',
                    'F4F': 'f4m',
                }.get(s.get('type'))
            } for s in vinfo.get('streams', [])]
            source_media_url = vinfo.get('sourceMediaURL')
            if source_media_url:
                formats.append({
                    'format_id': 'source_media',
                    'url': source_media_url,
                })
            self._sort_formats(formats)
            entries.append({
                'id': uuid,
                'title': vinfo['title'],
                'description': vinfo.get('blurb'),
                'uploader': uploader,
                'formats': formats,
                'duration': int_or_none(vinfo.get('videoDuration'), 100),
                'timestamp': timestamp,
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': page_id,
            'title': title,
        }
