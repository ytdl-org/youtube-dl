# encoding: utf-8
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class CinemassacreIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?(?P<url>cinemassacre\.com/(?P<date_Y>[0-9]{4})/(?P<date_m>[0-9]{2})/(?P<date_d>[0-9]{2})/.+?)(?:[/?].*)?'
    _TESTS = [{
        u'url': u'http://cinemassacre.com/2012/11/10/avgn-the-movie-trailer/',
        u'file': u'19911.flv',
        u'info_dict': {
            u'upload_date': u'20121110',
            u'title': u'“Angry Video Game Nerd: The Movie” – Trailer',
            u'description': u'md5:fb87405fcb42a331742a0dce2708560b',
        },
        u'params': {
            # rtmp download
            u'skip_download': True,
        },
    },
    {
        u'url': u'http://cinemassacre.com/2013/10/02/the-mummys-hand-1940',
        u'file': u'521be8ef82b16.flv',
        u'info_dict': {
            u'upload_date': u'20131002',
            u'title': u'The Mummy’s Hand (1940)',
        },
        u'params': {
            # rtmp download
            u'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        webpage_url = u'http://' + mobj.group('url')
        webpage = self._download_webpage(webpage_url, None) # Don't know video id yet
        video_date = mobj.group('date_Y') + mobj.group('date_m') + mobj.group('date_d')
        mobj = re.search(r'src="(?P<embed_url>http://player\.screenwavemedia\.com/play/(?:embed|player)\.php\?id=(?:Cinemassacre-)?(?P<video_id>.+?))"', webpage)
        if not mobj:
            raise ExtractorError(u'Can\'t extract embed url and video id')
        playerdata_url = mobj.group(u'embed_url')
        video_id = mobj.group(u'video_id')

        video_title = self._html_search_regex(r'<title>(?P<title>.+?)\|',
            webpage, u'title')
        video_description = self._html_search_regex(r'<div class="entry-content">(?P<description>.+?)</div>',
            webpage, u'description', flags=re.DOTALL, fatal=False)
        if len(video_description) == 0:
            video_description = None

        playerdata = self._download_webpage(playerdata_url, video_id)
        base_url = self._html_search_regex(r'\'streamer\': \'(?P<base_url>rtmp://.*?)/(?:vod|Cinemassacre)\'',
            playerdata, u'base_url')
        base_url += '/Cinemassacre/'
        # Important: The file names in playerdata are not used by the player and even wrong for some videos
        sd_file = 'Cinemassacre-%s_high.mp4' % video_id
        hd_file = 'Cinemassacre-%s.mp4' % video_id
        video_thumbnail = 'http://image.screenwavemedia.com/Cinemassacre/Cinemassacre-%s_thumb_640x360.jpg' % video_id

        formats = [
            {
                'url': base_url + sd_file,
                'ext': 'flv',
                'format': 'sd',
                'format_id': 'sd',
            },
            {
                'url': base_url + hd_file,
                'ext': 'flv',
                'format': 'hd',
                'format_id': 'hd',
            },
        ]

        info = {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail': video_thumbnail,
        }
        # TODO: Remove when #980 has been merged
        info.update(formats[-1])
        return info
