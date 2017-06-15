# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
)

import re


class MirrorIE(InfoExtractor):
    _VALID_URL = (r'https?://(?:www\.)?(?:mirror\.co\.uk)/.*')

    _TESTS = [{
        'url': 'http://www.mirror.co.uk/news/uk-news/grenfell-tower-block-fire-london-10619120?service=responsive',
        'md5': 'e8c52bcdf5180884b4e4d3159de3a40b',
        'info_dict': {
            'id': '5470567455001',
            'ext': 'mp4',
            'title': 'Blaze at Grenfell Tower continues 11 hours on',
            'timestamp': 1497433370,
            'uploader_id': '4221396001',
            'upload_date': '20170614'
        }
    }, {
        'url': 'http://www.mirror.co.uk/tv/tv-news/tim-brown-grenfell-fire-us-10627790',
        'md5': 'cd8e2ee6a57b043d9612321d8b4d07be',
        'info_dict': {
            'id': '5472207456001',
            'ext': 'mp4',
            'title': 'Structural engineer who warned of cladding fire dangers explains Grenfell Tower fire',
            'timestamp': 1497527486,
            'uploader_id': '4221396001',
            'upload_date': '20170615',
            'description': 'Structural engineer who warned of cladding fire dangers explains what made Grenfell Tower a death trap'
        }
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, '', 'Downloading webpage')

        mobj = re.search(r'<meta[^<]+?property=[\'"]+videoUrl[\'"]+.+?content=[\'"](?P<video_url>.+?brightcove\.com/\d+/(?P<account_id>[^/]+)/\d+/\d+/\2_\d+_(?P<video_id>[^.]+)\.mp4)', webpage)

        if mobj is None:
            raise ExtractorError('Video does not exist', expected=True)

        account_id = mobj.group('account_id')
        video_id = mobj.group('video_id')
        video_url = mobj.group('video_url')

        player_id = self._search_regex(
            r'(&l?s?quot?;)+playerId\1+:\1+(?P<player_id>[a-zA-Z0-9]+)\1+,',
            webpage, 'player id', group='player_id'
        )

        player_url = 'http://players.brightcove.net/%s/%s_default/index.html?videoId=%s' % (account_id, player_id, video_id)
        info = None
        try:
            info = self.url_result(
                player_url, 'BrightcoveNew', video_id
            )
        except:
            info = {
                'id': video_id,
                'title': self._search_regex(
                    r'(&l?s?quot?;)videoTitle\1+:\1(?P<video_title>[^&]+)\1[^}]+%s' % video_id,
                    webpage, 'video title', group='video_title'
                ),
                'url': video_url
            }
        return info
