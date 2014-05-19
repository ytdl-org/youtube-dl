# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

class AdultSwimIE(InfoExtractor):
    _VALID_URL = r'https?://video\.adultswim\.com/(?P<path>.+?)(?:\.html)?(?:\?.*)?(?:#.*)?$'
    _TEST = {
        'url': 'http://video.adultswim.com/rick-and-morty/close-rick-counters-of-the-rick-kind.html?x=y#title',
        'md5': '4a90c63a07537ec9383175b330dfeab4',
        'info_dict': {
            'id': '8a250ba1450996e901453d7e9caf02f3',
            'title': 'Rick and Morty Close Rick-Counters of the Rick Kind',
            'description': 'Rick has a run in with some old associates, resulting in a fallout with Morty. You got any chips, broh?',
        }
    }

    _available_formats = ['150', '640', '3500']

    _video_extensions = {
        '3500': 'flv',
        '640': 'mp4',
        '150': 'mp4',
        'ipad': 'm3u8',
        'iphone': 'm3u8'
    }
    _video_dimensions = {
        '3500': (1280, 720),
        '640': (480, 270),
        '150': (320, 180)
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_path = mobj.group('path')

        webpage = self._download_webpage(url, video_path)
        episode_id = self._html_search_regex(r'<link rel="video_src" href="http://i\.adultswim\.com/adultswim/adultswimtv/tools/swf/viralplayer.swf\?id=([0-9a-f]+?)"\s*/?\s*>', webpage, 'episode_id')
        title = self._html_search_regex(r'<meta property="og:title" content="\s*(.*?)\s*"\s*/?\s*>', webpage, 'title')

        index_url = 'http://asfix.adultswim.com/asfix-svc/episodeSearch/getEpisodesByIDs?networkName=AS&ids=%s' % episode_id
        idoc = self._download_xml(index_url, title, 'Downloading episode index', 'Unable to download episode index')

        episode_el = idoc.find('.//episode')
        show_title = episode_el.attrib.get('collectionTitle')
        episode_title = episode_el.attrib.get('title')
        thumbnail = episode_el.attrib.get('thumbnailUrl')
        description = episode_el.find('./description').text.strip()

        entries = []
        segment_els = episode_el.findall('./segments/segment')

        for part_num, segment_el in enumerate(segment_els):
            segment_id = segment_el.attrib.get('id')
            segment_title = '%s %s part %d' % (show_title, episode_title, part_num + 1)
            thumbnail = segment_el.attrib.get('thumbnailUrl')
            duration = segment_el.attrib.get('duration')

            segment_url = 'http://asfix.adultswim.com/asfix-svc/episodeservices/getCvpPlaylist?networkName=AS&id=%s' % segment_id
            idoc = self._download_xml(segment_url, segment_title, 'Downloading segment information', 'Unable to download segment information')

            formats = []
            file_els = idoc.findall('.//files/file')

            for file_el in file_els:
                bitrate = file_el.attrib.get('bitrate')
                type = file_el.attrib.get('type')
                width, height = self._video_dimensions.get(bitrate, (None, None))
                formats.append({
                    'format_id': '%s-%s' % (bitrate, type),
                    'url': file_el.text,
                    'ext': self._video_extensions.get(bitrate, 'mp4'),
                    'tbr': bitrate,
                    'height': height,
                    'width': width
                })

            self._sort_formats(formats)

            entries.append({
                'id': segment_id,
                'title': segment_title,
                'formats': formats,
                'uploader': show_title,
                'thumbnail': thumbnail,
                'duration': duration,
                'description': description
            })

        return {
            '_type': 'playlist',
            'id': episode_id,
            'display_id': video_path,
            'entries': entries,
            'title': '%s %s' % (show_title, episode_title),
            'description': description,
            'thumbnail': thumbnail
        }
