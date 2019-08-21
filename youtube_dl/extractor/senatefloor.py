# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor


class SenateFloorGranicusIE(InfoExtractor):
    """extractor for videos at https://www.senate.gov/floor/ hosted by
    granicus.com
    granicus.com urls are present in content at urls like
    https://floor.senate.gov/videos/3385/player
    which is the iframe src url for the embedded video at
    https://floor.senate.gov/MediaPlayer.php?view_id=2&clip_id=3388 )
    """

    _VALID_URL = r'https?://(?:archive-media.granicus.com.*?/OnDemand/[0-9a-z-]+/(?P<id>[0-9a-z-]+_[0-9a-f-]+).mp4|floor.senate.gov/(?:.*?[?]view_id=(?:[0-9]+)&clip_id=(?P<clip_id>[0-9]+).*|videos/[0-9]+/player))'
    _TESTS = [
        {'url': 'http://archive-media.granicus.com:443/OnDemand/senate/senate_ff605d76-86c3-4e8d-9991-9f32efd782de.mp4',
         'info_dict': {
             'id': 'senate_ff605d76-86c3-4e8d-9991-9f32efd782de',
             'ext': 'mp4',
             'title': 'The United States Senate'}
         },
        {'url': 'https://floor.senate.gov/videos/3385/player',
         'info_dict': {
             'id': 'senate_ff605d76-86c3-4e8d-9991-9f32efd782de',
             'ext': 'mp4',
             'title': 'Senate Floor Proceedings - 2019-08-13'}
         },
        {'url': 'https://floor.senate.gov/MediaPlayer.php?view_id=2&clip_id=3385',
         'info_dict': {
             'id': 'senate_ff605d76-86c3-4e8d-9991-9f32efd782de',
             'ext': 'mp4',
             'title': 'Senate Floor Proceedings - 2019-08-13'}
         },
        {'url': 'http://floor.senate.gov/ASX.php?view_id=2&clip_id=3385&sn=floor.senate.gov',
         'info_dict': {
             'id': 'senate_ff605d76-86c3-4e8d-9991-9f32efd782de',
             'ext': 'mp4',
             'title': 'Senate Floor Proceedings - 2019-08-13'}
         }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        title = 'The United States Senate'

        m = re.match(self._VALID_URL, url)
        if m and m.group('clip_id'):
            # https://floor.senate.gov/MediaPlayer.php?view_id=2&clip_id=3385
            # http://floor.senate.gov/ASX.php?view_id=2&clip_id=894&sn=floor.senate.gov
            return {
                '_type': 'url',
                'url': 'https://floor.senate.gov/videos/{}/player'.format(m.group('clip_id')),
            }
        elif url.endswith('player'):
            # https://floor.senate.gov/videos/3385/player
            webpage = self._download_webpage(url, video_id)
            title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title',
                                            default=title)
            video_id = self._html_search_regex(
                r'src="//archive-stream.granicus.com/OnDemand/_definst_/mp4:[0-9a-z-]+/(?P<id>[0-9a-z-]+_[0-9a-f-]+).mp4',
                webpage, 'id')
            return {
                '_type': 'url_transparent',
                'url': 'http://archive-media.granicus.com:443/OnDemand/{}/{}.mp4'.format(video_id.split('_')[0], video_id),
                'id': video_id,
                'title': title,
            }
        # we found an mp4!
        return {
            'url': url,
            'id': video_id,
            'title': title
            # TODO more properties? (see youtube_dl/extractor/common.py)
        }
