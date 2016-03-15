# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    strip_jsonp,
)


class WashingtonPostIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?washingtonpost\.com/.*?/(?P<id>[^/]+)/(?:$|[?#])'
    _TESTS = [{
        'url': 'http://www.washingtonpost.com/sf/national/2014/03/22/sinkhole-of-bureaucracy/',
        'info_dict': {
            'id': 'sinkhole-of-bureaucracy',
            'title': 'Sinkhole of bureaucracy',
        },
        'playlist': [{
            'md5': 'b9be794ceb56c7267d410a13f99d801a',
            'info_dict': {
                'id': 'fc433c38-b146-11e3-b8b3-44b1d1cd4c1f',
                'ext': 'mp4',
                'title': 'Breaking Points: The Paper Mine',
                'duration': 1290,
                'description': 'Overly complicated paper pushing is nothing new to government bureaucracy. But the way federal retirement applications are filed may be the most outdated. David Fahrenthold explains.',
                'uploader': 'The Washington Post',
                'timestamp': 1395527908,
                'upload_date': '20140322',
            },
        }, {
            'md5': '1fff6a689d8770966df78c8cb6c8c17c',
            'info_dict': {
                'id': '41255e28-b14a-11e3-b8b3-44b1d1cd4c1f',
                'ext': 'mp4',
                'title': 'The town bureaucracy sustains',
                'description': 'Underneath the friendly town of Boyers is a sea of government paperwork. In a disused limestone mine, hundreds of locals now track, file and process retirement applications for the federal government. We set out to find out what it\'s like to do paperwork 230 feet underground.',
                'duration': 2220,
                'timestamp': 1395528005,
                'upload_date': '20140322',
                'uploader': 'The Washington Post',
            },
        }],
    }, {
        'url': 'http://www.washingtonpost.com/blogs/wonkblog/wp/2014/12/31/one-airline-figured-out-how-to-make-sure-its-airplanes-never-disappear/',
        'info_dict': {
            'id': 'one-airline-figured-out-how-to-make-sure-its-airplanes-never-disappear',
            'title': 'One airline figured out how to make sure its airplanes never disappear',
        },
        'playlist': [{
            'md5': 'a7c1b5634ba5e57a6a82cdffa5b1e0d0',
            'info_dict': {
                'id': '0e4bb54c-9065-11e4-a66f-0ca5037a597d',
                'ext': 'mp4',
                'description': 'Washington Post transportation reporter Ashley Halsey III explains why a plane\'s black box needs to be recovered from a crash site instead of having its information streamed in real time throughout the flight.',
                'upload_date': '20141230',
                'uploader': 'The Washington Post',
                'timestamp': 1419974765,
                'title': 'Why black boxes don’t transmit data in real time',
            }
        }]
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        title = self._og_search_title(webpage)

        uuids = re.findall(r'''(?x)
            (?:
                <div\s+class="posttv-video-embed[^>]*?data-uuid=|
                data-video-uuid=
            )"([^"]+)"''', webpage)
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
                'preference': -100 if s.get('type') == 'smil' else None,
                'protocol': {
                    'MP4': 'http',
                    'F4F': 'f4m',
                }.get(s.get('type')),
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
