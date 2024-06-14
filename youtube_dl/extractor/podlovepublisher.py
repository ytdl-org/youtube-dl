# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor

import datetime
import time
import re


class PodlovePublisherIE(InfoExtractor):
    _VALID_URL = r'''(?:https?:)?//.+?/?podlove_action=pwp4_config'''

    _TESTS = [{
        'url': 'https://not-safe-for-work.de/nsfw099-kanzlerkind-sebastian/?podlove_action=pwp4_config',
        'md5': 'b123c265e73b3cd814f052de5bbd21c3',
        'info_dict': {
            'id': 'NSFW099 Kanzlerkind Sebastian',
            'ext': 'mp3',
            'title': 'NSFW099 Kanzlerkind Sebastian',
            'description': 'Uuuuund da sind wir wieder, keine 10 Monate nachdem wir das letzte Mal gesendet haben. Und bedenkt, dass solche Sendezyklen im Kern gut für Euch sind. So oder so haben wir uns einiges zu erzählen, auch wenn wir zunehmend aus der alten Brachialität rauszuwachsen scheinen. Dafür mehr Blick in die Zeit und dann und wann auch ins Internet.',
            'duration': 11723,
            'series': 'Not Safe For Work'
        }
    }, {
        'url': 'https://cre.fm/cre218-diamanten?podlove_action=pwp4_config',
        'md5': 'a6251c173c01ee0447ce55ee7c63e8c8',
        'info_dict': {
            'id': 'CRE218 Diamanten',
            'ext': 'mp3',
            'title': 'CRE218 Diamanten',
            'description': 'Diamanten faszinieren die Menschen und seit einem Jahrhundert symbolisieren sie Luxus und Perfektion wie kein anderes Material. Nachdem Diamanten zunächst nur aus der Erde gegraben wurden können Diamanten mit technischen Verfahren in sogar besserer Form hergestellt werden und spielen in Forschung und Industrie eine wichtige Rolle. Ich spreche mit Physiker und und Podcaster Reinhard Remfort über seinen persönlichen Weg zum Thema und über die Physik, Struktur, Eigenschaften und Anwendungen, die Diamanten  heute ermöglichen und in Zukunft noch ermöglichen könnten.',
            'duration': 10905,
            'series': 'CRE: Technik, Kultur, Gesellschaft'
        }
    }, {
        'url': 'http://einschlafen-podcast.de/podcast/ep-433-st-pauli-und-kant/?podlove_action=pwp4_config',
        'md5': '5d4b0d463a647d564abe8ff8bcecc272',
        'info_dict': {
            'id': 'EP 433 ~ St. Pauli und Kant',
            'ext': 'mp3',
            'title': 'EP 433 ~ St. Pauli und Kant',
            'description': 'Vor 200 (in Worten: zweihundert!) Episoden habe ich von einem Fussballspiel berichtet, bei dem zwei unserer langjährigen Spieler den FC St. Pauli verlassen haben. In Episode 233 ging es nämlich um das letzte Heimspiel von Marius Ebbers und Florian Bruns. Mein Hörer Berthold hatte mich auf diese Episode aufmerksam gemacht, und interessanterweise hat uns beim letzten Heimspiel wieder ein langjähriger Spieler verlassen: Bernd Nehrig. Und genau wie Bruns und Ebbers hat er in seinem letzten Spiel ein Tor gemacht! Was für eine Geschichte :)',
            'duration': 3195,
            'series': 'Einschlafen Podcast'
        }
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(r'(?:https?:)?//.+?/?podlove_action=pwp4_config', webpage)
        if mobj:
            return mobj.group(0)
        else:
            return None

    def _real_extract(self, url):
        player_data = self._download_json(url, None)

        duration_secs = None
        if 'duration' in player_data:
            dur_ptime = time.strptime(player_data.get('duration').split('.')[0], '%H:%M:%S')
            duration_secs = datetime.timedelta(hours=dur_ptime.tm_hour, minutes=dur_ptime.tm_min, seconds=dur_ptime.tm_sec).total_seconds()

        formats = []
        for audioformat in player_data.get('audio'):
            result_format = {}
            if 'url' not in audioformat:
                # url is mandatory
                continue
            else:
                result_format['url'] = audioformat.get('url')

            if 'size' in audioformat:
                result_format['filesize'] = int(audioformat['size'])

            result_format['format_id'] = audioformat.get('mimeType')
            result_format['format'] = audioformat.get('title')

            formats.append(result_format)

        self._sort_formats(formats)

        return {
            'id': player_data.get('title'),
            'title': player_data.get('title'),
            'episode': player_data.get('title'),
            'description': player_data.get('summary'),
            'formats': formats,
            'duration': duration_secs,
            'series': player_data.get('show', {}).get('title')
        }
