from __future__ import unicode_literals

from .common import InfoExtractor


class KarriereVideosIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?karrierevideos\.at/berufsvideos/([a-z-]+)/(?P<id>[a-z-]+)'
    _TEST = {
        'url': 'http://www.karrierevideos.at/berufsvideos/mittlere-hoehere-schulen/altenpflegerin',
        'info_dict': {
            'id': 'altenpflegerin',
            'ext': 'mp4',
            'title': 'AltenpflegerIn',
            'thumbnail': 're:^http://.*\.png\?v=[0-9]+',
            'description': 'md5:dbadd1259fde2159a9b28667cb664ae2'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        description = self._html_search_regex(
            r'<div class="leadtext">\n{0,}?\s{0,}<p>(.*?)</p>',
            webpage, 'description')

        playlist = self._html_search_regex(r'/config/video/(.*?)\.xml', webpage, 'playlist')
        playlist = self._download_xml(
            'http://www.karrierevideos.at/player-playlist.xml.php?p=' + playlist,
            video_id)

        namespace = 'http://developer.longtailvideo.com/trac/wiki/FlashFormats'

        item = playlist.find('tracklist/item')
        streamer = item.find('{%s}streamer' % namespace).text

        return {
            'id': video_id,
            'title': self._html_search_meta('title', webpage),
            'description': description,
            'thumbnail': 'http://www.karrierevideos.at' + self._html_search_meta('thumbnail', webpage),
            'protocol': 'rtmp',
            'url': streamer.replace('rtmpt', 'http'),
            'play_path': 'mp4:' + item.find('{%s}file' % namespace).text,
            'tc_url': streamer,
            'ext': 'mp4'
        }
