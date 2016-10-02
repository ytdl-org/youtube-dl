# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    parse_iso8601,
    xpath_text,
)


class PhilharmonieDeParisIE(InfoExtractor):
    IE_DESC = 'Philharmonie de Paris'
    _VALID_URL = r'https?://live\.philharmoniedeparis\.fr/(?:[Cc]oncert/|misc/Playlist\.ashx\?id=)(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://live.philharmoniedeparis.fr/concert/1032066.html',
        'info_dict': {
            'id': '1032066',
            'ext': 'flv',
            'title': 'md5:d1f5585d87d041d07ce9434804bc8425',
            'timestamp': 1428179400,
            'upload_date': '20150404',
            'duration': 6592.278,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }, {
        'url': 'http://live.philharmoniedeparis.fr/Concert/1030324.html',
        'only_matching': True,
    }, {
        'url': 'http://live.philharmoniedeparis.fr/misc/Playlist.ashx?id=1030324&track=&lang=fr',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        concert = self._download_xml(
            'http://live.philharmoniedeparis.fr/misc/Playlist.ashx?id=%s' % video_id,
            video_id).find('./concert')

        formats = []
        info_dict = {
            'id': video_id,
            'title': xpath_text(concert, './titre', 'title', fatal=True),
            'formats': formats,
        }

        fichiers = concert.find('./fichiers')
        stream = fichiers.attrib['serveurstream']
        for fichier in fichiers.findall('./fichier'):
            info_dict['duration'] = float_or_none(fichier.get('timecodefin'))
            for quality, (format_id, suffix) in enumerate([('lq', ''), ('hq', '_hd')]):
                format_url = fichier.get('url%s' % suffix)
                if not format_url:
                    continue
                formats.append({
                    'url': stream,
                    'play_path': format_url,
                    'ext': 'flv',
                    'format_id': format_id,
                    'width': int_or_none(concert.get('largeur%s' % suffix)),
                    'height': int_or_none(concert.get('hauteur%s' % suffix)),
                    'quality': quality,
                })
        self._sort_formats(formats)

        date, hour = concert.get('date'), concert.get('heure')
        if date and hour:
            info_dict['timestamp'] = parse_iso8601(
                '%s-%s-%sT%s:00' % (date[0:4], date[4:6], date[6:8], hour))
        elif date:
            info_dict['upload_date'] = date

        return info_dict
