# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..compat import (
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
)


class PandoraTVIE(InfoExtractor):
    _VALID_URL = r'http://(?:.+?\.)?channel.pandora.tv/channel/video.ptv\?'
    _TESTS = [{
        'url': 'http://jp.channel.pandora.tv/channel/video.ptv?c1=&prgid=53294230&ch_userid=mikakim&ref=main&lot=cate_01_2',
        'info_dict': {
            'description': '\u982d\u3092\u64ab\u3067\u3066\u304f\u308c\u308b\uff1f',
            'ext': 'mp4',
            'id': '53294230',
            'title': '\u982d\u3092\u64ab\u3067\u3066\u304f\u308c\u308b\uff1f',
            'upload_date': '20151218',
        }
    }]


    def _real_extract(self, url):
        qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        video_id = qs.get('prgid', [None])[0]
        user_id = qs.get('ch_userid', [None])[0]
        if any(not f for f in (video_id, user_id,)):
            raise ExtractorError('Invalid URL', expected=True)

        data_url ='http://m.pandora.tv/?c=view&m=viewJsonApi&ch_userid={userid}&prgid={prgid}'.format(userid=user_id,prgid=video_id)
        data = self._download_json(data_url, video_id)
        info = data['data']['rows']['vod_play_info']['result']

        formats = []
        for format_id in sorted([k for k in info if k.startswith('v') and k.endswith('Url') and info[k]]):
            formats.append({
                'format_id': format_id,
                'url': info[format_id],
                'ext': 'mp4',
                'height': int(format_id[1:-3]),
            })

        return {
            'description': info['body'],
            'thumbnail': info['thumbnail'],
            'formats': formats,
            'id': video_id,
            'title': info['subject'],
            'upload_date': info['fid'][:8],
            'view_count': info['hit'],
        }
