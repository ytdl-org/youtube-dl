# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    xpath_text
)


class EuropaIE(InfoExtractor):
    _VALID_URL = r'https?://ec\.europa\.eu/avservices/video/player\.cfm\?(?:[^&]|&(?!ref))*ref=(?P<id>[A-Za-z0-9]+)'
    _TEST = {
        'url': 'http://ec.europa.eu/avservices/video/player.cfm?ref=I107758',
        'md5': '728cca2fd41d5aa7350cec1141fbe620',
        'info_dict': {
            'id': 'I107758',
            'ext': 'mp4',
            'title': 'TRADE - Wikileaks on TTIP',
            'description': 'NEW  LIVE EC Midday press briefing of 11/08/2015',
            'thumbnail': 're:^http://defiris\.ec\.streamcloud\.be/findmedia/18/107758/THUMB_[0-9A-Z]+\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        query = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        lang = query.get('sitelang', ['en'])[0]

        playlist = self._download_xml('http://ec.europa.eu/avservices/video/player/playlist.cfm?ID=' + video_id, video_id)
        videos = {}
        formats = []

        for item in playlist.findall('info/title/item'):
            videos[xpath_text(item, 'lg')] = {'title': xpath_text(item, 'label').strip()}

        for item in playlist.findall('info/description/item'):
            videos[xpath_text(item, 'lg')]['description'] = xpath_text(item, 'label').strip()

        for item in playlist.findall('files/file'):
            lg = xpath_text(item, 'lg')
            vid = videos[lg]
            vid['format_note'] = xpath_text(item, 'lglabel')
            vid['url'] = xpath_text(item, 'url')

            if lg == lang:
                vid['language_preference'] = 10

            formats.append(vid)

        formats.reverse()
        def_video = videos.get(lang, videos['int'])

        return {
            'id': video_id,
            'title': def_video['title'],
            'description': def_video['description'],
            'thumbnail': xpath_text(playlist, 'info/thumburl', 'thumburl'),
            'formats': formats
        }
