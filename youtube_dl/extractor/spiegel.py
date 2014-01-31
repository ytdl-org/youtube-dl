from __future__ import unicode_literals

import re

from .common import InfoExtractor


class SpiegelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/video/[^/]*-(?P<videoID>[0-9]+)(?:\.html)?(?:#.*)?$'
    _TESTS = [{
        'url': 'http://www.spiegel.de/video/vulkan-tungurahua-in-ecuador-ist-wieder-aktiv-video-1259285.html',
        'file': '1259285.mp4',
        'md5': '2c2754212136f35fb4b19767d242f66e',
        'info_dict': {
            'title': 'Vulkanausbruch in Ecuador: Der "Feuerschlund" ist wieder aktiv',
        },
    },
    {
        'url': 'http://www.spiegel.de/video/schach-wm-videoanalyse-des-fuenften-spiels-video-1309159.html',
        'file': '1309159.mp4',
        'md5': 'f2cdf638d7aa47654e251e1aee360af1',
        'info_dict': {
            'title': 'Schach-WM in der Videoanalyse: Carlsen nutzt die Fehlgriffe des Titelverteidigers',
        },
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(
            r'<div class="module-title">(.*?)</div>', webpage, 'title')

        xml_url = 'http://video2.spiegel.de/flash/' + video_id + '.xml'
        idoc = self._download_xml(
            xml_url, video_id,
            note='Downloading XML', errnote='Failed to download XML')

        formats = [
            {
                'format_id': n.tag.rpartition('type')[2],
                'url': 'http://video2.spiegel.de/flash/' + n.find('./filename').text,
                'width': int(n.find('./width').text),
                'height': int(n.find('./height').text),
                'abr': int(n.find('./audiobitrate').text),
                'vbr': int(n.find('./videobitrate').text),
                'vcodec': n.find('./codec').text,
                'acodec': 'MP4A',
            }
            for n in list(idoc)
            # Blacklist type 6, it's extremely LQ and not available on the same server
            if n.tag.startswith('type') and n.tag != 'type6'
        ]
        duration = float(idoc[0].findall('./duration')[0].text)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'duration': duration,
            'formats': formats,
        }
