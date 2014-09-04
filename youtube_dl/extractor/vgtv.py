# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
  ExtractorError
)

class VGTVIE(InfoExtractor):
  # Because of the #! in the URL structure we need to add ' before and after given URL.
  # Or else it will cry: -bash: !/video/100495/lars-og-lars-sesong-6-episode-6-lakselus: event not found
  _VALID_URL = r'http://(?:www\.)?vgtv\.no/#!/(?:.*)/(?P<id>[0-9]+)/(?P<title>[^?#]*)'
  _TEST = {
    'url': 'http://www.vgtv.no/#!/video/84196/hevnen-er-soet-episode-10-abu',
    'md5': 'b8be7a234cebb840c0d512c78013e02f',
    'info_dict': {
      'id': '84196',
      'ext': 'mp4',
      'title': 'Hevnen er søt episode 10: Abu',
      'description': 'md5:e25e4badb5f544b04341e14abdc72234',
      'timestamp': 1404626400,
      'upload_date': '20140706'
    }
  }

  def _real_extract(self, url):
    mobj = re.match(self._VALID_URL, url)
    video_id = mobj.group('id')

    # Download JSON file containing video info.
    data = self._download_json('http://svp.vg.no/svp/api/v1/vgtv/assets/%s?appName=vgtv-website' % video_id, video_id, 'Downloading media JSON')

    # Known streamType: vod, live, wasLive
    # Will it even be possible to add support for live streams?
    if data['streamType'] != 'vod':
      raise ExtractorError('Stream type \'%s\' is not yet supported.' % data['streamType'], expected=True)

    # Add access token to image or it will fail.
    thumbnail = data['images']['main'] + '?t[]=900x506q80'

    formats = []

    # Most videos are in MP4, but some are either HLS or HDS.
    # Don't want to support HDS.
    if data['streamUrls']['mp4'] is not None:
      formats.append({
        'url': data['streamUrls']['mp4'],
        'format_id': 'mp4',
        'ext': 'mp4'
      })
    elif data['streamUrls']['hls'] is not None:
      self.to_screen(u'No MP4 URL found, using m3u8. This may take some extra time.')
      formats.append({
        'url': data['streamUrls']['hls'],
        'format_id': 'm3u8',
        'ext': 'mp4'
      })
    else:
      raise ExtractorError('No download URL found for video: %s.' % video_id, expected=True)

    return {
      'id': video_id,
      'title': data['title'],
      'description': data['description'],
      'thumbnail': thumbnail,
      'timestamp': data['published'],
      'duration': data['duration'],
      'view_count': data['displays'],
      'formats': formats,
    }