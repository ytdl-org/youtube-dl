import re
import xml.etree.ElementTree

from .common import InfoExtractor


class SpiegelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/video/[^/]*-(?P<videoID>[0-9]+)(?:\.html)?(?:#.*)?$'
    _TESTS = [{
        u'url': u'http://www.spiegel.de/video/vulkan-tungurahua-in-ecuador-ist-wieder-aktiv-video-1259285.html',
        u'file': u'1259285.mp4',
        u'md5': u'2c2754212136f35fb4b19767d242f66e',
        u'info_dict': {
            u"title": u"Vulkanausbruch in Ecuador: Der \"Feuerschlund\" ist wieder aktiv"
        }
    },
    {
        u'url': u'http://www.spiegel.de/video/schach-wm-videoanalyse-des-fuenften-spiels-video-1309159.html',
        u'file': u'1309159.mp4',
        u'md5': u'f2cdf638d7aa47654e251e1aee360af1',
        u'info_dict': {
            u'title': u'Schach-WM in der Videoanalyse: Carlsen nutzt die Fehlgriffe des Titelverteidigers'
        }
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(
            r'<div class="module-title">(.*?)</div>', webpage, u'title')

        xml_url = u'http://video2.spiegel.de/flash/' + video_id + u'.xml'
        xml_code = self._download_webpage(
            xml_url, video_id,
            note=u'Downloading XML', errnote=u'Failed to download XML')

        idoc = xml.etree.ElementTree.fromstring(xml_code)

        formats = [
            {
                'format_id': n.tag.rpartition('type')[2],
                'url': u'http://video2.spiegel.de/flash/' + n.find('./filename').text,
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
        formats.sort(key=lambda f: f['vbr'])
        duration = float(idoc[0].findall('./duration')[0].text)

        info = {
            'id': video_id,
            'title': video_title,
            'duration': duration,
            'formats': formats,
        }
        return info
