from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_urllib_parse,
)
from ..utils import (
    xpath_with_ns,
)


class InternetVideoArchiveIE(InfoExtractor):
    _VALID_URL = r'https?://video\.internetvideoarchive\.net/flash/players/.*?\?.*?publishedid.*?'

    _TEST = {
        'url': 'http://video.internetvideoarchive.net/flash/players/flashconfiguration.aspx?customerid=69249&publishedid=452693&playerid=247',
        'info_dict': {
            'id': '452693',
            'ext': 'mp4',
            'title': 'SKYFALL',
            'description': 'In SKYFALL, Bond\'s loyalty to M is tested as her past comes back to haunt her. As MI6 comes under attack, 007 must track down and destroy the threat, no matter how personal the cost.',
            'duration': 152,
        },
    }

    @staticmethod
    def _build_url(query):
        return 'http://video.internetvideoarchive.net/flash/players/flashconfiguration.aspx?' + query

    @staticmethod
    def _clean_query(query):
        NEEDED_ARGS = ['publishedid', 'customerid']
        query_dic = compat_urlparse.parse_qs(query)
        cleaned_dic = dict((k, v[0]) for (k, v) in query_dic.items() if k in NEEDED_ARGS)
        # Other player ids return m3u8 urls
        cleaned_dic['playerid'] = '247'
        cleaned_dic['videokbrate'] = '100000'
        return compat_urllib_parse.urlencode(cleaned_dic)

    def _real_extract(self, url):
        query = compat_urlparse.urlparse(url).query
        query_dic = compat_urlparse.parse_qs(query)
        video_id = query_dic['publishedid'][0]
        url = self._build_url(query)

        flashconfiguration = self._download_xml(url, video_id,
                                                'Downloading flash configuration')
        file_url = flashconfiguration.find('file').text
        file_url = file_url.replace('/playlist.aspx', '/mrssplaylist.aspx')
        # Replace some of the parameters in the query to get the best quality
        # and http links (no m3u8 manifests)
        file_url = re.sub(r'(?<=\?)(.+)$',
                          lambda m: self._clean_query(m.group()),
                          file_url)
        info = self._download_xml(file_url, video_id,
                                  'Downloading video info')
        item = info.find('channel/item')

        def _bp(p):
            return xpath_with_ns(
                p,
                {
                    'media': 'http://search.yahoo.com/mrss/',
                    'jwplayer': 'http://developer.longtailvideo.com/trac/wiki/FlashFormats',
                }
            )
        formats = []
        for content in item.findall(_bp('media:group/media:content')):
            attr = content.attrib
            f_url = attr['url']
            width = int(attr['width'])
            bitrate = int(attr['bitrate'])
            format_id = '%d-%dk' % (width, bitrate)
            formats.append({
                'format_id': format_id,
                'url': f_url,
                'width': width,
                'tbr': bitrate,
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': item.find('title').text,
            'formats': formats,
            'thumbnail': item.find(_bp('media:thumbnail')).attrib['url'],
            'description': item.find('description').text,
            'duration': int(attr['duration']),
        }
