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
        u'md5': u'f9bb7ede54d1229c9846e197b4737e06',
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
        u'md5': u'91b248e1e2473d5bff55d6010518111f',
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
        url = self._html_search_regex(r'\'streamer\': \'(?P<url>[^\']+)\'', playerdata, u'url')
        player_url = self._html_search_regex(r'\'flashplayer\': \'(?P<player_url>[^\']+)\'', playerdata, u'player_url')
        if playerdata.find('hd: { file:') != -1:
            page_url = 'http://cinemassacre.com'
        else:
            page_url = re.split(r'(?<=[^/])/([^/]|$)', player_url)[0]
        sd_file = self._html_search_regex(r'\'file\': \'(?P<sd_file>[^\']+)\'', playerdata, u'sd_file')
        hd_file = self._html_search_regex(r'"?hd"?: { \'?file\'?: "(?P<hd_file>[^"]+)"', playerdata, u'hd_file')
        video_thumbnail = self._html_search_regex(r'\'image\': \'(?P<thumbnail>[^\']+)\'', playerdata, u'thumbnail', fatal=False)

        formats = [
            {
                'url': url,
                'player_url': player_url,
                'page_url': page_url,
                'play_path': 'mp4:' + sd_file,
                'tc_url': url,
                'ext': 'flv',
                'format': 'sd',
                'format_id': 'sd',
            },
            {
                'url': url,
                'player_url': player_url,
                'page_url': page_url,
                'play_path': 'mp4:' + hd_file,
                'tc_url': url,
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
