from .common import InfoExtractor
from ..utils import escape_url

import re

class VierIE (InfoExtractor):
  _VALID_URL = r'(?:http://)?www.vier.be/(?P<program>.*)/videos/(.+?)/(?P<id>\d*)'
  _TEST = {
      'url': 'http://www.vier.be/planb/videos/het-wordt-warm-de-moestuin/16129',
      'md5': 'bf48f4eb998cbde44ecd02fc42c51149',
      'info_dict': {
          'id': '16129',
          'ext': 'mp4',
          'title': 'Het wordt warm in De Moestuin',
          'description': 'De vele uren werk eisen hun tol. Wim droomt van assistentie...',
      },
  }

  def _real_extract (self, url):
    mobj = re.match (self._VALID_URL, url)

    program = mobj.group ('program')
    video_id = mobj.group ('id')

    webpage = self._download_webpage (url, video_id)

    title = self._html_search_regex(r'<meta property="og:title" content="(.+?)" />', webpage, u'title')
    description = self._html_search_regex (r'<meta property="og:description" content="(.+?)" />', webpage, u'description')
    vod_id =  self._html_search_regex(r'"filename" : "(.+?)"', webpage, u'playlist URL')
    url = escape_url ("http://vod.streamcloud.be/vier_vod/mp4:_definst_/" + vod_id + ".mp4/playlist.m3u8")

    return {
        'id': video_id,
        'title': title,
        'description': description,
        'formats': self._extract_m3u8_formats(url, video_id, 'mp4'),
    }

class VierVideosIE (InfoExtractor):
  _VALID_URL = r'http://www.vier.be/(?P<program>.*)/videos(\?page=(?P<page>\d*))?$'
  _TESTS = [{
    'url': 'http://www.vier.be/demoestuin/videos',
    'info_dict': {
      'id': 'demoestuin page(0)',
    },
    'playlist_mincount': 20,
  },
  {
    'url': 'http://www.vier.be/demoestuin/videos?page=6',
    'info_dict': {
      'id': 'demoestuin page(6)',
    },
    'playlist_mincount': 20,
  }]

  def _real_extract (self, url):
    mobj = re.match (self._VALID_URL, url)

    program = mobj.group ('program')
    page = mobj.group ('page')
    if page == None:
      page = 0

    videos_id = program + " page(" + str (page) + ")"
    videos_page = self._download_webpage (url, videos_id, note='Retrieving videos page')

    return {
        '_type': 'playlist',
        'id': videos_id,
        'entries': [{
            '_type': 'url',
            'url': "http://www.vier.be/" + eurl[0],
            'ie_key': 'Vier',
          } for eurl in re.findall (r'<h3><a href="(.+?)">(.+?)</a></h3>', videos_page)]
        }
