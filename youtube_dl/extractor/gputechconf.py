# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    xpath_element,
    xpath_text,
    int_or_none,
    parse_duration,
)


class GPUTechConfIE(InfoExtractor):
    _VALID_URL = r'https?://on-demand\.gputechconf\.com/gtc/2015/video/S(?P<id>\d+)\.html'
    _TEST = {
        'url': 'http://on-demand.gputechconf.com/gtc/2015/video/S5156.html',
        'md5': 'a8862a00a0fd65b8b43acc5b8e33f798',
        'info_dict': {
            'id': '5156',
            'ext': 'mp4',
            'title': 'Coordinating More Than 3 Million CUDA Threads for Social Network Analysis',
            'duration': 1219,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        root_path = self._search_regex(r'var\s+rootPath\s*=\s*"([^"]+)', webpage, 'root path', 'http://evt.dispeak.com/nvidia/events/gtc15/')
        xml_file_id = self._search_regex(r'var\s+xmlFileId\s*=\s*"([^"]+)', webpage, 'xml file id')

        doc = self._download_xml('%sxml/%s.xml' % (root_path, xml_file_id), video_id)

        metadata = xpath_element(doc, 'metadata')
        http_host = xpath_text(metadata, 'httpHost', 'http host', True)
        mbr_videos = xpath_element(metadata, 'MBRVideos')

        formats = []
        for mbr_video in mbr_videos.findall('MBRVideo'):
            stream_name = xpath_text(mbr_video, 'streamName')
            if stream_name:
                formats.append({
                    'url': 'http://%s/%s' % (http_host, stream_name.replace('mp4:', '')),
                    'tbr': int_or_none(xpath_text(mbr_video, 'bitrate')),
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': xpath_text(metadata, 'title'),
            'duration': parse_duration(xpath_text(metadata, 'endTime')),
            'creator': xpath_text(metadata, 'speaker'),
            'formats': formats,
        }
