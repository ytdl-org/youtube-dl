# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class AftonbladetIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.aftonbladet\.se/abtv/articles/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://tv.aftonbladet.se/abtv/articles/36015',
        'info_dict': {
            'id': '36015',
            'ext': 'mp4',
            'title': 'Vulkanutbrott i rymden - nu släpper NASA bilderna',
            'description': 'Jupiters måne mest aktiv av alla himlakroppar',
            'timestamp': 1394142732,
            'upload_date': '20140306',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # find internal video meta data
        meta_url = 'http://aftonbladet-play.drlib.aptoma.no/video/%s.json'
        player_config = self._parse_json(self._html_search_regex(
            r'data-player-config="([^"]+)"', webpage, 'player config'), video_id)
        internal_meta_id = player_config['videoId']
        internal_meta_url = meta_url % internal_meta_id
        internal_meta_json = self._download_json(
            internal_meta_url, video_id, 'Downloading video meta data')

        # find internal video formats
        format_url = 'http://aftonbladet-play.videodata.drvideo.aptoma.no/actions/video/?id=%s'
        internal_video_id = internal_meta_json['videoId']
        internal_formats_url = format_url % internal_video_id
        internal_formats_json = self._download_json(
            internal_formats_url, video_id, 'Downloading video formats')

        formats = []
        for fmt in internal_formats_json['formats']['http']['pseudostreaming']['mp4']:
            p = fmt['paths'][0]
            formats.append({
                'url': 'http://%s:%d/%s/%s' % (p['address'], p['port'], p['path'], p['filename']),
                'ext': 'mp4',
                'width': int_or_none(fmt.get('width')),
                'height': int_or_none(fmt.get('height')),
                'tbr': int_or_none(fmt.get('bitrate')),
                'protocol': 'http',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': internal_meta_json['title'],
            'formats': formats,
            'thumbnail': internal_meta_json.get('imageUrl'),
            'description': internal_meta_json.get('shortPreamble'),
            'timestamp': int_or_none(internal_meta_json.get('timePublished')),
            'duration': int_or_none(internal_meta_json.get('duration')),
            'view_count': int_or_none(internal_meta_json.get('views')),
        }
