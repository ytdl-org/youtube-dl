import re
import xml.etree.ElementTree

from .common import InfoExtractor


class SpiegelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?spiegel\.de/video/[^/]*-(?P<videoID>[0-9]+)(?:\.html)?(?:#.*)?$'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<div class="module-title">(.*?)</div>',
            webpage, u'title')

        xml_url = u'http://video2.spiegel.de/flash/' + video_id + u'.xml'
        xml_code = self._download_webpage(xml_url, video_id,
                    note=u'Downloading XML', errnote=u'Failed to download XML')

        idoc = xml.etree.ElementTree.fromstring(xml_code)
        last_type = idoc[-1]
        filename = last_type.findall('./filename')[0].text
        duration = float(last_type.findall('./duration')[0].text)

        video_url = 'http://video2.spiegel.de/flash/' + filename
        video_ext = filename.rpartition('.')[2]
        info = {
            'id': video_id,
            'url': video_url,
            'ext': video_ext,
            'title': video_title,
            'duration': duration,
        }
        return [info]
