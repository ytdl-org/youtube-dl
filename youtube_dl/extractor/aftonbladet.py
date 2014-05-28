# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class AftonbladetIE(InfoExtractor):
    _VALID_URL = r'^http://tv\.aftonbladet\.se/webbtv.+?(?P<video_id>article[0-9]+)\.ab(?:$|[?#])'
    _TEST = {
        'url': 'http://tv.aftonbladet.se/webbtv/nyheter/vetenskap/rymden/article36015.ab',
        'info_dict': {
            'id': 'article36015',
            'ext': 'mp4',
            'title': 'Vulkanutbrott i rymden - nu släpper NASA bilderna',
            'description': 'Jupiters måne mest aktiv av alla himlakroppar',
            'timestamp': 1394142732,
            'upload_date': '20140306',
        },
    }

    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)

        video_id = mobj.group('video_id')
        webpage = self._download_webpage(url, video_id)

        # find internal video meta data
        meta_url = 'http://aftonbladet-play.drlib.aptoma.no/video/%s.json'
        internal_meta_id = self._html_search_regex(
            r'data-aptomaId="([\w\d]+)"', webpage, 'internal_meta_id')
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
                'width': fmt['width'],
                'height': fmt['height'],
                'tbr': fmt['bitrate'],
                'protocol': 'http',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': internal_meta_json['title'],
            'formats': formats,
            'thumbnail': internal_meta_json['imageUrl'],
            'description': internal_meta_json['shortPreamble'],
            'timestamp': internal_meta_json['timePublished'],
            'duration': internal_meta_json['duration'],
            'view_count': internal_meta_json['views'],
        }
