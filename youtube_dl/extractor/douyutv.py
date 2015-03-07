# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
)

class DouyutvIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?douyutv\.com/(?P<id>[A-Za-z0-9]+)'

    '''
    show_status: 1 直播中 ，2 没有直播
    '''

    _TEST = {
        'url': 'http://www.douyutv.com/iseven',
        'info_dict': {
            'id': 'iseven',
            'title': '清晨醒脑！T-ara根本停不下来！',
            'ext': 'flv',
            'thumbnail': 're:^https?://.*\.jpg$',
            'is_live': True,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info_url = 'http://www.douyutv.com/api/client/room/' + video_id

        config = self._download_json(info_url, video_id)

        error_code = config.get('error')
        show_status = config['data'].get('show_status')
        if error_code is not 0:
            raise ExtractorError('Server reported error %i' % error_code,
                                 expected=True)

        if show_status == '2':
            raise ExtractorError('The live show has not yet started',
                                 expected=True)

        title = config['data'].get('room_name')
        rtmp_url = config['data'].get('rtmp_url')
        rtmp_live = config['data'].get('rtmp_live')
        thumbnail = config['data'].get('room_src') 

        url = rtmp_url+'/'+rtmp_live

        return {
            'id': video_id,
            'title': title,
            'ext':'flv',
            'url': url,
            'thumbnail': thumbnail,
            'is_live': True,
            # TODO more properties (see youtube_dl/extractor/common.py)
        }