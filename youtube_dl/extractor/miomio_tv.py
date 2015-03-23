# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class MiomioTvIE(InfoExtractor):
    IE_NAME = 'miomio.tv'
    _VALID_URL = r'https?://(?:www\.)?miomio\.tv/watch/cc(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.miomio.tv/watch/cc179734/',
        'md5': '48de02137d0739c15b440a224ad364b9',
        'info_dict': {
            'id': '179734',
            'title': u'\u624b\u7ed8\u52a8\u6f2b\u9b3c\u6ce3\u4f46\u4e01\u5168\u7a0b\u753b\u6cd5',
            'ext': 'flv'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<meta\s+name="description"\s+content="\s*([^"]*)\s*"', webpage, 'title')
        ref_path = self._search_regex(r'src="(/mioplayer/.*?)"', webpage, 'ref_path')
        referer = 'http://www.miomio.tv{}'.format(ref_path)
        xml_config = self._search_regex(r'flashvars="type=sina&amp;(.*?)&amp;cid=', webpage, 'xml config')
        self._request_webpage("http://www.miomio.tv/mioplayer/mioplayerconfigfiles/xml.php?id={}&r=cc{}".format(id, 945), video_id)
        xml_url = 'http://www.miomio.tv/mioplayer/mioplayerconfigfiles/sina.php?{}'.format(xml_config)
        vidconfig = self._download_xml(xml_url, video_id)

        file_els = vidconfig.findall('.//durl')

        entries = []

        for file_el in file_els:
            segment_id = file_el.find('order').text.strip()
            segment_title = '_'.join([title, segment_id])
            segment_duration = file_el.find('length').text.strip()
            segment_url = file_el.find('url').text.strip()

            entries.append({
                'id': segment_id,
                'title': segment_title,
                'duration': segment_duration,
                'url': segment_url
            })

        http_headers = {
            'Referer': referer,
            'Accept-Language': 'en,en-US;q=0.7,de;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        if len(entries) == 1:
            return {
                'id': video_id,
                'title': title,
                'url': entries[0]['url'],
                'http_headers': http_headers
            }

        return {
            '_type': 'multi_video',
            'id': video_id,
            'title': title,
            'entries': entries,
            'http_headers': http_headers
        }
