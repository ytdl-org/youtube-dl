import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    xpath_with_ns,
    determine_ext,
)


class InternetVideoArchiveIE(InfoExtractor):
    _VALID_URL = r'https?://video\.internetvideoarchive\.net/flash/players/.*?\?.*?publishedid.*?'

    _TEST = {
        u'url': u'http://video.internetvideoarchive.net/flash/players/flashconfiguration.aspx?customerid=69249&publishedid=452693&playerid=247',
        u'file': u'452693.mp4',
        u'info_dict': {
            u'title': u'SKYFALL',
            u'description': u'In SKYFALL, Bond\'s loyalty to M is tested as her past comes back to haunt her. As MI6 comes under attack, 007 must track down and destroy the threat, no matter how personal the cost.',
            u'duration': 156,
        },
    }

    @staticmethod
    def _build_url(query):
        return 'http://video.internetvideoarchive.net/flash/players/flashconfiguration.aspx?' + query

    def _real_extract(self, url):
        query = compat_urlparse.urlparse(url).query
        query_dic = compat_urlparse.parse_qs(query)
        video_id = query_dic['publishedid'][0]
        url = self._build_url(query)

        flashconfiguration_xml = self._download_webpage(url, video_id,
            u'Downloading flash configuration')
        flashconfiguration = xml.etree.ElementTree.fromstring(flashconfiguration_xml.encode('utf-8'))
        file_url = flashconfiguration.find('file').text
        file_url = file_url.replace('/playlist.aspx', '/mrssplaylist.aspx')
        info_xml = self._download_webpage(file_url, video_id,
            u'Downloading video info')
        info = xml.etree.ElementTree.fromstring(info_xml.encode('utf-8'))
        item = info.find('channel/item')

        def _bp(p):
            return xpath_with_ns(p,
                {'media': 'http://search.yahoo.com/mrss/',
                'jwplayer': 'http://developer.longtailvideo.com/trac/wiki/FlashFormats'})
        formats = []
        for content in item.findall(_bp('media:group/media:content')):
            attr = content.attrib
            f_url = attr['url']
            formats.append({
                'url': f_url,
                'ext': determine_ext(f_url),
                'width': int(attr['width']),
                'bitrate': int(attr['bitrate']),
            })
        formats = sorted(formats, key=lambda f: f['bitrate'])

        info = {
            'id': video_id,
            'title': item.find('title').text,
            'formats': formats,
            'thumbnail': item.find(_bp('media:thumbnail')).attrib['url'],
            'description': item.find('description').text,
            'duration': int(attr['duration']),
        }
        # TODO: Remove when #980 has been merged
        info.update(formats[-1])
        return info
