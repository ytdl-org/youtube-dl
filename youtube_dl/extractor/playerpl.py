# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    qualities,
    parse_duration,
    parse_iso8601,
    unescapeHTML,
)


class PlayerPLIE(InfoExtractor):
    IE_NAME = 'player.pl'
    _VALID_URL = r'http://player\.pl/[a-z\-]+/[A-Za-z,0-9\-]+/[A-Za-z,0-9\-]+,(?P<id>\d+)\.html'

    _TESTS = [{
        'url': 'http://player.pl/programy-online/agencja-odcinki,1137/odcinek-1,zaginiony-brylant,S00E01,16830.html',
        'info_dict': {
            'id': '16830',
            'ext': 'mp4',
            'duration': 2665,
            'title': 'Zaginiony brylant',
            'description': 'Nasz agent, "Piękny Lolo", znalazł się w potrzasku. W trakcie wykonywania zadania musiał ukryć się w szafie. Nikt nie może go przyłapać na przeszukiwaniu willi bogatej rozwódki. Jego zadaniem jest odnaleźć zaginiony brylant należący do jej byłóego męża. Niestety zjawia się gosposia, która utrudnia ucieczką z mieszkania. To dopiero początek, bo w drugiej willi czeka go dramatyczna przeprawa \r\nz prawdziwym drapieżnikiem.\r\n',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_url = ('http://player.pl/api/'
            '?platform=ConnectedTV&terminal=Samsung&format=json&v=2.0&authKey=ba786b315508f0920eca1c34d65534cd'
            '&type=episode&id=%s&sort=newest&m=getItem&deviceScreenHeight=1080&deviceScreenWidth=1920') % (video_id)

        get_quality = qualities(['Bardzo niska', 'Niska', 'Średnia', 'Standard', 'Wysoka', 'Bardzo wysoka', 'HD'])

        result = self._download_json(json_url, video_id)
        if result['status'] != 'success':
            raise ExtractorError('Player.pl returned an error: %r' % (result))
        if not result['item']:
            raise ExtractorError('Player.pl returned success, but item is empty', expected=True)

        thumbnails = None # [{ 'url': thumb['url'] } for thumb in result['item'].get('thumbnail', ())] # XXX: relative URLs, but relative to what?

        formats = []
        for stream in result['item']['videos']['main']['video_content']:
            stream_url = self._download_webpage(stream['url'], video_id, 'Downloading "%s" stream URL' % (stream['profile_name']))
            formats.append({
                'url': stream_url,
                'quality': get_quality(stream['profile_name']),
                'resolution': stream['profile_name'],
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': result['item']['title'] or ('%s: S%sE%s' % (result['item']['serie_title'], result['item']['season'] or '1', result['item']['episode'])),
            'description': unescapeHTML(result['item'].get('lead')),
            'duration': parse_duration(result['item']['run_time']),
            'timestamp': parse_iso8601(result['item']['start_date'] + ':00', delimiter=' '), # XXX: timezone='Europe/Warsaw'
            'formats': formats,
            'thumbnail': thumbnails,
        }
