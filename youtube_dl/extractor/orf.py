# coding: utf-8
from __future__ import unicode_literals

import json
import re
import calendar
import datetime

from .common import InfoExtractor
from ..utils import (
    HEADRequest,
    unified_strdate,
    ExtractorError,
)


class ORFTVthekIE(InfoExtractor):
    IE_NAME = 'orf:tvthek'
    IE_DESC = 'ORF TVthek'
    _VALID_URL = r'https?://tvthek\.orf\.at/(?:programs/.+?/episodes|topics?/.+?|program/[^/]+)/(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://tvthek.orf.at/program/Aufgetischt/2745173/Aufgetischt-Mit-der-Steirischen-Tafelrunde/8891389',
        'playlist': [{
            'md5': '2942210346ed779588f428a92db88712',
            'info_dict': {
                'id': '8896777',
                'ext': 'mp4',
                'title': 'Aufgetischt: Mit der Steirischen Tafelrunde',
                'description': 'md5:c1272f0245537812d4e36419c207b67d',
                'duration': 2668,
                'upload_date': '20141208',
            },
        }],
        'skip': 'Blocked outside of Austria / Germany',
    }, {
        'url': 'http://tvthek.orf.at/topic/Im-Wandel-der-Zeit/8002126/Best-of-Ingrid-Thurnher/7982256',
        'playlist': [{
            'md5': '68f543909aea49d621dfc7703a11cfaf',
            'info_dict': {
                'id': '7982259',
                'ext': 'mp4',
                'title': 'Best of Ingrid Thurnher',
                'upload_date': '20140527',
                'description': 'Viele Jahre war Ingrid Thurnher das "Gesicht" der ZIB 2. Vor ihrem Wechsel zur ZIB 2 im jahr 1995 moderierte sie unter anderem "Land und Leute", "Österreich-Bild" und "Niederösterreich heute".',
            }
        }],
        '_skip': 'Blocked outside of Austria / Germany',
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        data_json = self._search_regex(
            r'initializeAdworx\((.+?)\);\n', webpage, 'video info')
        all_data = json.loads(data_json)

        def get_segments(all_data):
            for data in all_data:
                if data['name'] in (
                        'Tracker::EPISODE_DETAIL_PAGE_OVER_PROGRAM',
                        'Tracker::EPISODE_DETAIL_PAGE_OVER_TOPIC'):
                    return data['values']['segments']

        sdata = get_segments(all_data)
        if not sdata:
            raise ExtractorError('Unable to extract segments')

        def quality_to_int(s):
            m = re.search('([0-9]+)', s)
            if m is None:
                return -1
            return int(m.group(1))

        entries = []
        for sd in sdata:
            video_id = sd['id']
            formats = [{
                'preference': -10 if fd['delivery'] == 'hls' else None,
                'format_id': '%s-%s-%s' % (
                    fd['delivery'], fd['quality'], fd['quality_string']),
                'url': fd['src'],
                'protocol': fd['protocol'],
                'quality': quality_to_int(fd['quality']),
            } for fd in sd['playlist_item_array']['sources']]

            # Check for geoblocking.
            # There is a property is_geoprotection, but that's always false
            geo_str = sd.get('geoprotection_string')
            if geo_str:
                try:
                    http_url = next(
                        f['url']
                        for f in formats
                        if re.match(r'^https?://.*\.mp4$', f['url']))
                except StopIteration:
                    pass
                else:
                    req = HEADRequest(http_url)
                    self._request_webpage(
                        req, video_id,
                        note='Testing for geoblocking',
                        errnote=((
                            'This video seems to be blocked outside of %s. '
                            'You may want to try the streaming-* formats.')
                            % geo_str),
                        fatal=False)

            self._sort_formats(formats)

            upload_date = unified_strdate(sd['created_date'])
            entries.append({
                '_type': 'video',
                'id': video_id,
                'title': sd['header'],
                'formats': formats,
                'description': sd.get('description'),
                'duration': int(sd['duration_in_seconds']),
                'upload_date': upload_date,
                'thumbnail': sd.get('image_full_url'),
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': playlist_id,
        }


class ORFOE1IE(InfoExtractor):
    IE_NAME = 'orf:oe1'
    IE_DESC = 'Radio Österreich 1'
    _VALID_URL = r'http://oe1\.orf\.at/(?:programm/|konsole.*?#\?track_id=)(?P<id>[0-9]+)'

    # Audios on ORF radio are only available for 7 days, so we can't add tests.
    _TEST = {
        'url': 'http://oe1.orf.at/konsole?show=on_demand#?track_id=394211',
        'only_matching': True,
    }

    def _real_extract(self, url):
        show_id = self._match_id(url)
        data = self._download_json(
            'http://oe1.orf.at/programm/%s/konsole' % show_id,
            show_id
        )

        timestamp = datetime.datetime.strptime('%s %s' % (
            data['item']['day_label'],
            data['item']['time']
        ), '%d.%m.%Y %H:%M')
        unix_timestamp = calendar.timegm(timestamp.utctimetuple())

        return {
            'id': show_id,
            'title': data['item']['title'],
            'url': data['item']['url_stream'],
            'ext': 'mp3',
            'description': data['item'].get('info'),
            'timestamp': unix_timestamp
        }


class ORFFM4IE(InfoExtractor):
    IE_NAME = 'orf:fm4'
    IE_DESC = 'radio FM4'
    _VALID_URL = r'http://fm4\.orf\.at/7tage/?#(?P<date>[0-9]+)/(?P<show>\w+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_date = mobj.group('date')
        show_id = mobj.group('show')

        data = self._download_json(
            'http://audioapi.orf.at/fm4/json/2.0/broadcasts/%s/4%s' % (show_date, show_id),
            show_id
        )

        def extract_entry_dict(info, title, subtitle):
            return {
                'id': info['loopStreamId'].replace('.mp3', ''),
                'url': 'http://loopstream01.apa.at/?channel=fm4&id=%s' % info['loopStreamId'],
                'title': title,
                'description': subtitle,
                'duration': (info['end'] - info['start']) / 1000,
                'timestamp': info['start'] / 1000,
                'ext': 'mp3'
            }

        entries = [extract_entry_dict(t, data['title'], data['subtitle']) for t in data['streams']]

        return {
            '_type': 'playlist',
            'id': show_id,
            'title': data['title'],
            'description': data['subtitle'],
            'entries': entries
        }
