# coding: utf-8
from __future__ import unicode_literals

import re
from ..utils import unified_timestamp
from .youtube import YoutubeIE

from .common import InfoExtractor


class YuJaIE(InfoExtractor):
    # url needs subdomain and either auth or node
    _VALID_URL = r'https?://(?P<subdomain>[a-z0-9]+)\.yuja\.com/V/(?:Watch|Video)\?v=(?P<id>[0-9]+)(?:.*)&a=(?P<auth>[0-9]+)'
    _TESTS = [{
        'url': 'https://usm.yuja.com/V/Watch?v=256594&node=1155827&a=0',
        'md5': '4bf9ffa3be86e320c85fcb7fe5918fc3',
        'info_dict': {
            'id': '256594',
            'ext': 'mp4',
            'title': 'Expect To Pursue What Matters',
            'thumbnail': 'https://usm.yuja.com/P/DataPage/BroadcastsThumb/218886',
            'description': '',
            'timestamp': 1542230582,
            'upload_date': '20181114',
            'duration': 107.416
        }
    }, {
        'url': 'https://ncvps.yuja.com/V/Video?v=578523&node=2618907&a=244955112&autoplay=1',
        'md5': '6cbcfffd905672e4224b54727d6e84b0',
        'info_dict': {
            'id': '578523',
            'ext': 'mp4',
            'title': 'Intro to NCVPS New Helpdesk 2019-2020',
            'thumbnail': 'https://ncvps.yuja.com/P/DataPage/BroadcastsThumb/532754',
            'description': 'This video provides a general overview of what customers need to know for the new NCVPS Helpdesk. ',
            'timestamp': 1576600000,
            'upload_date': '20191217',
            'duration': 236.167
        }
    }, {
        # youtube embed
        'url': 'https://mayvillestate.yuja.com/V/Watch?v=325580&node=1589970&a=96633478',
        'info_dict': {
            'id': '7YU95IGxOi8',
            'ext': 'mp4',
            'title': '125 Years of Personal Service',
            'upload_date': '20160420',
            'uploader_id': 'MayvilleStateUniv',
            'uploader': 'MayvilleStateUniv'
        }
    }]

    def _real_extract(self, url):
        subdomain, video_id, auth_id = re.match(self._VALID_URL, url).groups()

        # for some URLs, auth ID is 0 and another auth ID must be resolved from the node ID
        if auth_id == '0':
            _NODE_REGEX = r'https?://(?P<subdomain>[a-z0-9]+)\.yuja\.com/V/(?:Watch|Video)\?v=(?P<id>[0-9]+)(?:.*)&node=(?P<node>[0-9]+)'
            subdomain, video_id, node_id = re.match(_NODE_REGEX, url).groups()
            # get new link using node ID
            direct_link = self._download_json('https://%s.yuja.com/P/Data/VideoJSON?video=%i&node=%i&checkUser=true&a=%s'
                                              % (subdomain, int(video_id), int(node_id), int(auth_id)), video_id, query={})['video']['directLink']
            auth_id = re.match(self._VALID_URL, direct_link).group('auth')

        data = self._download_json('https://%s.yuja.com/P/Data/VideoJSON?video=%i&a=%i&getPlayerType=true'
                                   % (subdomain, int(video_id), int(auth_id)), video_id, query={})['video']

        # for YouTube embeds
        if data.get('youtubeCode'):
            return self.url_result(data.get('youtubeCode'), YoutubeIE.ie_key())

        formats = []
        if data.get('videoHLSLink'):
            formats.append({
                'format_id': 'mp4_hls',
                'url': data.get('videoHLSLink'),
                'protocol': 'm3u8',
                'ext': 'mp4',
            })

        if data.get('videoLinkMp4'):
            formats.append({
                'format_id': 'mp4',
                'url': data.get('videoLinkMp4'),
                'ext': 'mp4',
            })

        return {
            'id': video_id,
            'title': data.get('videoTitle'),
            # 'url': data.get('videoLinkMp4'),
            'formats': formats,
            'thumbnail': 'https://%s.yuja.com%s' % (subdomain, data.get('thumbImage')),
            'description': data.get('description'),
            'timestamp': unified_timestamp(data.get('postedDate')),
            # 'automatic_captions': TODO: add captions
            'duration': float(data.get('duration'))
        }
