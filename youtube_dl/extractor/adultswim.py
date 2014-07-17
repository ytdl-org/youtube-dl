# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

class AdultSwimIE(InfoExtractor):
    _VALID_URL = r'https?://video\.adultswim\.com/(?P<path>.+?)(?:\.html)?(?:\?.*)?(?:#.*)?$'
    _TEST = {
        'url': 'http://video.adultswim.com/rick-and-morty/close-rick-counters-of-the-rick-kind.html?x=y#title',
        'playlist': [
            {
                'md5': '4da359ec73b58df4575cd01a610ba5dc',
                'info_dict': {
                    'id': '8a250ba1450996e901453d7f02ca02f5',
                    'ext': 'flv',
                    'title': 'Rick and Morty Close Rick-Counters of the Rick Kind part 1',
                    'description': 'Rick has a run in with some old associates, resulting in a fallout with Morty. You got any chips, broh?',
                    'uploader': 'Rick and Morty',
                    'thumbnail': 'http://i.cdn.turner.com/asfix/repository/8a250ba13f865824013fc9db8b6b0400/thumbnail_267549017116827057.jpg'
                }
            },
            {
                'md5': 'ffbdf55af9331c509d95350bd0cc1819',
                'info_dict': {
                    'id': '8a250ba1450996e901453d7f4bd102f6',
                    'ext': 'flv',
                    'title': 'Rick and Morty Close Rick-Counters of the Rick Kind part 2',
                    'description': 'Rick has a run in with some old associates, resulting in a fallout with Morty. You got any chips, broh?',
                    'uploader': 'Rick and Morty',
                    'thumbnail': 'http://i.cdn.turner.com/asfix/repository/8a250ba13f865824013fc9db8b6b0400/thumbnail_267549017116827057.jpg'
                }
            },
            {
                'md5': 'b92409635540304280b4b6c36bd14a0a',
                'info_dict': {
                    'id': '8a250ba1450996e901453d7fa73c02f7',
                    'ext': 'flv',
                    'title': 'Rick and Morty Close Rick-Counters of the Rick Kind part 3',
                    'description': 'Rick has a run in with some old associates, resulting in a fallout with Morty. You got any chips, broh?',
                    'uploader': 'Rick and Morty',
                    'thumbnail': 'http://i.cdn.turner.com/asfix/repository/8a250ba13f865824013fc9db8b6b0400/thumbnail_267549017116827057.jpg'
                }
            },
            {
                'md5': 'e8818891d60e47b29cd89d7b0278156d',
                'info_dict': {
                    'id': '8a250ba1450996e901453d7fc8ba02f8',
                    'ext': 'flv',
                    'title': 'Rick and Morty Close Rick-Counters of the Rick Kind part 4',
                    'description': 'Rick has a run in with some old associates, resulting in a fallout with Morty. You got any chips, broh?',
                    'uploader': 'Rick and Morty',
                    'thumbnail': 'http://i.cdn.turner.com/asfix/repository/8a250ba13f865824013fc9db8b6b0400/thumbnail_267549017116827057.jpg'
                }
            }
        ]
    }

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
        title = self._og_search_title(webpage)

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
                    # The bitrate may not be a number (for example: 'iphone')
                    'tbr': int(bitrate) if bitrate.isdigit() else None,
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
