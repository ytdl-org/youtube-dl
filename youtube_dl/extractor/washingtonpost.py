# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    strip_jsonp,
)


class WashingtonPostIE(InfoExtractor):
    IE_NAME = 'washingtonpost'
    _VALID_URL = r'(?:washingtonpost:|https?://(?:www\.)?washingtonpost\.com/video/(?:[^/]+/)*)(?P<id>[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12})'
    _TEST = {
        'url': 'https://www.washingtonpost.com/video/c/video/480ba4ee-1ec7-11e6-82c2-a7dcb313287d',
        'md5': '6f537e1334b714eb15f9563bd4b9cdfa',
        'info_dict': {
            'id': '480ba4ee-1ec7-11e6-82c2-a7dcb313287d',
            'ext': 'mp4',
            'title': 'Egypt finds belongings, debris from plane crash',
            'description': 'md5:a17ceee432f215a5371388c1f680bd86',
            'upload_date': '20160520',
            'uploader': 'Reuters',
            'timestamp': 1463778452,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_data = self._download_json(
            'http://www.washingtonpost.com/posttv/c/videojson/%s?resType=jsonp' % video_id,
            video_id, transform_source=strip_jsonp)[0]['contentConfig']
        title = video_data['title']

        urls = []
        formats = []
        for s in video_data.get('streams', []):
            s_url = s.get('url')
            if not s_url or s_url in urls:
                continue
            urls.append(s_url)
            video_type = s.get('type')
            if video_type == 'smil':
                continue
            elif video_type in ('ts', 'hls') and ('_master.m3u8' in s_url or '_mobile.m3u8' in s_url):
                m3u8_formats = self._extract_m3u8_formats(
                    s_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
                for m3u8_format in m3u8_formats:
                    width = m3u8_format.get('width')
                    if not width:
                        continue
                    vbr = self._search_regex(
                        r'%d_%d_(\d+)' % (width, m3u8_format['height']), m3u8_format['url'], 'vbr', default=None)
                    if vbr:
                        m3u8_format.update({
                            'vbr': int_or_none(vbr),
                        })
                formats.extend(m3u8_formats)
            else:
                width = int_or_none(s.get('width'))
                vbr = int_or_none(s.get('bitrate'))
                has_width = width != 0
                formats.append({
                    'format_id': (
                        '%s-%d-%d' % (video_type, width, vbr)
                        if width
                        else video_type),
                    'vbr': vbr if has_width else None,
                    'width': width,
                    'height': int_or_none(s.get('height')),
                    'acodec': s.get('audioCodec'),
                    'vcodec': s.get('videoCodec') if has_width else 'none',
                    'filesize': int_or_none(s.get('fileSize')),
                    'url': s_url,
                    'ext': 'mp4',
                    'protocol': 'm3u8_native' if video_type in ('ts', 'hls') else None,
                })
        source_media_url = video_data.get('sourceMediaURL')
        if source_media_url:
            formats.append({
                'format_id': 'source_media',
                'url': source_media_url,
            })
        self._sort_formats(
            formats, ('width', 'height', 'vbr', 'filesize', 'tbr', 'format_id'))

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('blurb'),
            'uploader': video_data.get('credits', {}).get('source'),
            'formats': formats,
            'duration': int_or_none(video_data.get('videoDuration'), 100),
            'timestamp': int_or_none(
                video_data.get('dateConfig', {}).get('dateFirstPublished'), 1000),
        }


class WashingtonPostArticleIE(InfoExtractor):
    IE_NAME = 'washingtonpost:article'
    _VALID_URL = r'https?://(?:www\.)?washingtonpost\.com/(?:[^/]+/)*(?P<id>[^/?#]+)'
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

    @classmethod
    def suitable(cls, url):
        return False if WashingtonPostIE.suitable(url) else super(WashingtonPostArticleIE, cls).suitable(url)

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)

        title = self._og_search_title(webpage)

        uuids = re.findall(r'''(?x)
            (?:
                <div\s+class="posttv-video-embed[^>]*?data-uuid=|
                data-video-uuid=
            )"([^"]+)"''', webpage)
        entries = [self.url_result('washingtonpost:%s' % uuid, 'WashingtonPost', uuid) for uuid in uuids]

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': page_id,
            'title': title,
        }
