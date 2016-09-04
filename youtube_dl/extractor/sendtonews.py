# coding: utf-8
from __future__ import unicode_literals

import re

from .jwplatform import JWPlatformBaseIE
from ..utils import (
    float_or_none,
    parse_iso8601,
    update_url_query,
)


class SendtoNewsIE(JWPlatformBaseIE):
    _VALID_URL = r'https?://embed\.sendtonews\.com/player2/embedplayer\.php\?.*\bSC=(?P<id>[0-9A-Za-z-]+)'

    _TEST = {
        # From http://cleveland.cbslocal.com/2016/05/16/indians-score-season-high-15-runs-in-blowout-win-over-reds-rapid-reaction/
        'url': 'http://embed.sendtonews.com/player2/embedplayer.php?SC=GxfCe0Zo7D-175909-5588&type=single&autoplay=on&sound=YES',
        'info_dict': {
            'id': 'GxfCe0Zo7D-175909-5588'
        },
        'playlist_count': 9,
        # test the first video only to prevent lengthy tests
        'playlist': [{
            'info_dict': {
                'id': '198180',
                'ext': 'mp4',
                'title': 'Recap: CLE 5, LAA 4',
                'description': '8/14/16: Naquin, Almonte lead Indians in 5-4 win',
                'duration': 57.343,
                'thumbnail': 're:https?://.*\.jpg$',
                'upload_date': '20160815',
                'timestamp': 1471221961,
            },
        }],
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    _URL_TEMPLATE = '//embed.sendtonews.com/player2/embedplayer.php?SC=%s'

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(r'''(?x)<script[^>]+src=([\'"])
            (?:https?:)?//embed\.sendtonews\.com/player/responsiveembed\.php\?
                .*\bSC=(?P<SC>[0-9a-zA-Z-]+).*
            \1>''', webpage)
        if mobj:
            sc = mobj.group('SC')
            return cls._URL_TEMPLATE % sc

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        data_url = update_url_query(
            url.replace('embedplayer.php', 'data_read.php'),
            {'cmd': 'loadInitial'})
        playlist_data = self._download_json(data_url, playlist_id)

        entries = []
        for video in playlist_data['playlistData'][0]:
            info_dict = self._parse_jwplayer_data(
                video['jwconfiguration'],
                require_title=False, rtmp_params={'no_resume': True})

            thumbnails = []
            if video.get('thumbnailUrl'):
                thumbnails.append({
                    'id': 'normal',
                    'url': video['thumbnailUrl'],
                })
            if video.get('smThumbnailUrl'):
                thumbnails.append({
                    'id': 'small',
                    'url': video['smThumbnailUrl'],
                })
            info_dict.update({
                'title': video['S_headLine'],
                'description': video.get('S_fullStory'),
                'thumbnails': thumbnails,
                'duration': float_or_none(video.get('SM_length')),
                'timestamp': parse_iso8601(video.get('S_sysDate'), delimiter=' '),
            })
            entries.append(info_dict)

        return self.playlist_result(entries, playlist_id)
