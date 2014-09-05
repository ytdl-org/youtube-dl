# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
  ExtractorError
)

class DBTVIE(InfoExtractor):
  _VALID_URL = r'http://dbtv.no/(?P<id>[0-9]+)/?(?P<slug>.*)$'
  _TEST = {
    'url': 'http://dbtv.no/3649835190001#Skulle_teste_ut_fornøyelsespark,_men_kollegaen_var_bare_opptatt_av_bikinikroppen',
    'md5': 'b89953ed25dacb6edb3ef6c6f430f8bc',
    'info_dict': {
      'id': '3649835190001',
      'ext': 'mp4',
      'title': 'Skulle teste ut fornøyelsespark, men kollegaen var bare opptatt av bikinikroppen',
      'description': 'md5:d681bf2bb7dd3503892cedb9c2d0e6f2',
      'thumbnail': 'http://gfx.dbtv.no/thumbs/still/33100.jpg',
      'timestamp': 1404039863,
      'upload_date': '20140629',
      'duration': 69544,
    }
  }

  def _real_extract(self, url):
    mobj = re.match(self._VALID_URL, url)
    video_id = mobj.group('id')

    # Download JSON file containing video info.
    data = self._download_json('http://api.dbtv.no/discovery/%s' % video_id, video_id, 'Downloading media JSON')
    # We only want the first video in the JSON API file.
    video = data['playlist'][0]

    # Check for full HD video, else use the standard video URL
    for i in range(0, len(video['renditions'])):
      if int(video['renditions'][i]['width']) == 1280:
        video_url = video['renditions'][i]['URL']
        break
      else:
        video_url = video['URL']

    # Add access token to image or it will fail.
    thumbnail = video['splash']

    # Duration int.
    duration = int(video['length'])

    # Timestamp is given in milliseconds.
    timestamp = float(str(video['publishedAt'])[0:-3])

    formats = []

    # Video URL.
    if video['URL'] is not None:
      formats.append({
        'url': video_url,
        'format_id': 'mp4',
        'ext': 'mp4'
      })
    else:
      raise ExtractorError('No download URL found for video: %s.' % video_id, expected=True)

    return {
      'id': video_id,
      'title': video['title'],
      'description': video['desc'],
      'thumbnail': thumbnail,
      'timestamp': timestamp,
      'duration': duration,
      'view_count': video['views'],
      'formats': formats,
    }
