from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    unescapeHTML,
)


class WistiaIE(InfoExtractor):
    _VALID_URL = r'(?:wistia:|https?://(?:fast\.)?wistia\.(?:net|com)/embed/(?:iframe|medias)/)(?P<id>[a-z0-9]+)'
    _API_URL = 'http://fast.wistia.com/embed/medias/%s.json'
    _IFRAME_URL = 'http://fast.wistia.net/embed/iframe/%s'

    _TESTS = [{
        'url': 'http://fast.wistia.net/embed/iframe/sh7fpupwlt',
        'md5': 'cafeb56ec0c53c18c97405eecb3133df',
        'info_dict': {
            'id': 'sh7fpupwlt',
            'ext': 'mov',
            'title': 'Being Resourceful',
            'description': 'a Clients From Hell Video Series video from worldwidewebhosting',
            'upload_date': '20131204',
            'timestamp': 1386185018,
            'duration': 117,
        },
    }, {
        'url': 'wistia:sh7fpupwlt',
        'only_matching': True,
    }, {
        # with hls video
        'url': 'wistia:807fafadvk',
        'only_matching': True,
    }, {
        'url': 'http://fast.wistia.com/embed/iframe/sh7fpupwlt',
        'only_matching': True,
    }, {
        'url': 'http://fast.wistia.net/embed/medias/sh7fpupwlt.json',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        match = re.search(
            r'<(?:meta[^>]+?content|iframe[^>]+?src)=(["\'])(?P<url>(?:https?:)?//(?:fast\.)?wistia\.(?:net|com)/embed/iframe/.+?)\1', webpage)
        if match:
            return unescapeHTML(match.group('url'))

        match = re.search(r'(?:id=["\']wistia_|data-wistia-?id=["\']|Wistia\.embed\(["\'])(?P<id>[^"\']+)', webpage)
        if match:
            return 'wistia:%s' % match.group('id')

        match = re.search(
            r'''(?sx)
                <script[^>]+src=(["'])(?:https?:)?//fast\.wistia\.com/assets/external/E-v1\.js\1[^>]*>.*?
                <div[^>]+class=(["']).*?\bwistia_async_(?P<id>[a-z0-9]+)\b.*?\2
            ''', webpage)
        if match:
            return 'wistia:%s' % match.group('id')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data_json = self._download_json(
            self._API_URL % video_id, video_id,
            # Some videos require this.
            headers={
                'Referer': url if url.startswith('http') else self._IFRAME_URL % video_id,
            })

        if data_json.get('error'):
            raise ExtractorError(
                'Error while getting the playlist', expected=True)

        data = data_json['media']
        title = data['name']

        formats = []
        thumbnails = []
        for a in data['assets']:
            aurl = a.get('url')
            if not aurl:
                continue
            astatus = a.get('status')
            atype = a.get('type')
            if (astatus is not None and astatus != 2) or atype in ('preview', 'storyboard'):
                continue
            elif atype in ('still', 'still_image'):
                thumbnails.append({
                    'url': aurl,
                    'width': int_or_none(a.get('width')),
                    'height': int_or_none(a.get('height')),
                })
            else:
                aext = a.get('ext')
                is_m3u8 = a.get('container') == 'm3u8' or aext == 'm3u8'
                formats.append({
                    'format_id': atype,
                    'url': aurl,
                    'tbr': int_or_none(a.get('bitrate')),
                    'vbr': int_or_none(a.get('opt_vbitrate')),
                    'width': int_or_none(a.get('width')),
                    'height': int_or_none(a.get('height')),
                    'filesize': int_or_none(a.get('size')),
                    'vcodec': a.get('codec'),
                    'container': a.get('container'),
                    'ext': 'mp4' if is_m3u8 else aext,
                    'protocol': 'm3u8' if is_m3u8 else None,
                    'preference': 1 if atype == 'original' else None,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': data.get('seoDescription'),
            'formats': formats,
            'thumbnails': thumbnails,
            'duration': float_or_none(data.get('duration')),
            'timestamp': int_or_none(data.get('createdAt')),
        }
