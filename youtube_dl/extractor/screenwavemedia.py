# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class ScreenwaveMediaIE(InfoExtractor):
    _VALID_URL = r'http://player\.screenwavemedia\.com/play/[a-zA-Z]+\.php\?[^"]*\bid=(?P<id>.+)'

    _TESTS = [{
        'url': 'http://player.screenwavemedia.com/play/play.php?playerdiv=videoarea&companiondiv=squareAd&id=Cinemassacre-19911',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        playerdata = self._download_webpage(url, video_id, 'Downloading player webpage')

        vidtitle = self._search_regex(
            r'\'vidtitle\'\s*:\s*"([^"]+)"', playerdata, 'vidtitle').replace('\\/', '/')
        vidurl = self._search_regex(
            r'\'vidurl\'\s*:\s*"([^"]+)"', playerdata, 'vidurl').replace('\\/', '/')

        videolist_url = None

        mobj = re.search(r"'videoserver'\s*:\s*'(?P<videoserver>[^']+)'", playerdata)
        if mobj:
            videoserver = mobj.group('videoserver')
            mobj = re.search(r'\'vidid\'\s*:\s*"(?P<vidid>[^\']+)"', playerdata)
            vidid = mobj.group('vidid') if mobj else video_id
            videolist_url = 'http://%s/vod/smil:%s.smil/jwplayer.smil' % (videoserver, vidid)
        else:
            mobj = re.search(r"file\s*:\s*'(?P<smil>http.+?/jwplayer\.smil)'", playerdata)
            if mobj:
                videolist_url = mobj.group('smil')

        if videolist_url:
            videolist = self._download_xml(videolist_url, video_id, 'Downloading videolist XML')
            formats = []
            baseurl = vidurl[:vidurl.rfind('/') + 1]
            for video in videolist.findall('.//video'):
                src = video.get('src')
                if not src:
                    continue
                file_ = src.partition(':')[-1]
                width = int_or_none(video.get('width'))
                height = int_or_none(video.get('height'))
                bitrate = int_or_none(video.get('system-bitrate'), scale=1000)
                format = {
                    'url': baseurl + file_,
                    'format_id': src.rpartition('.')[0].rpartition('_')[-1],
                }
                if width or height:
                    format.update({
                        'tbr': bitrate,
                        'width': width,
                        'height': height,
                    })
                else:
                    format.update({
                        'abr': bitrate,
                        'vcodec': 'none',
                    })
                formats.append(format)
        else:
            formats = [{
                'url': vidurl,
            }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': vidtitle,
            'formats': formats,
        }


class CinemassacreIE(InfoExtractor):
    _VALID_URL = 'https?://(?:www\.)?cinemassacre\.com/(?P<date_y>[0-9]{4})/(?P<date_m>[0-9]{2})/(?P<date_d>[0-9]{2})/(?P<display_id>[^?#/]+)'
    _TESTS = [
        {
            'url': 'http://cinemassacre.com/2012/11/10/avgn-the-movie-trailer/',
            'md5': 'fde81fbafaee331785f58cd6c0d46190',
            'info_dict': {
                'id': 'Cinemassacre-19911',
                'ext': 'mp4',
                'upload_date': '20121110',
                'title': '“Angry Video Game Nerd: The Movie” – Trailer',
                'description': 'md5:fb87405fcb42a331742a0dce2708560b',
            },
        },
        {
            'url': 'http://cinemassacre.com/2013/10/02/the-mummys-hand-1940',
            'md5': 'd72f10cd39eac4215048f62ab477a511',
            'info_dict': {
                'id': 'Cinemassacre-521be8ef82b16',
                'ext': 'mp4',
                'upload_date': '20131002',
                'title': 'The Mummy’s Hand (1940)',
            },
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        video_date = mobj.group('date_y') + mobj.group('date_m') + mobj.group('date_d')

        webpage = self._download_webpage(url, display_id)

        playerdata_url = self._search_regex(
            r'src="(http://player\.screenwavemedia\.com/play/[a-zA-Z]+\.php\?[^"]*\bid=.+?)"',
            webpage, 'player data URL')
        video_title = self._html_search_regex(
            r'<title>(?P<title>.+?)\|', webpage, 'title')
        video_description = self._html_search_regex(
            r'<div class="entry-content">(?P<description>.+?)</div>',
            webpage, 'description', flags=re.DOTALL, fatal=False)
        video_thumbnail = self._og_search_thumbnail(webpage)

        return {
            '_type': 'url_transparent',
            'display_id': display_id,
            'title': video_title,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail': video_thumbnail,
            'url': playerdata_url,
        }


class TeamFourIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?teamfourstar\.com/video/(?P<id>[a-z0-9\-]+)/?'
    _TEST = {
        'url': 'http://teamfourstar.com/video/a-moment-with-tfs-episode-4/',
        'info_dict': {
            'id': 'TeamFourStar-5292a02f20bfa',
            'ext': 'mp4',
            'upload_date': '20130401',
            'description': 'Check out this and more on our website: http://teamfourstar.com\nTFS Store: http://sharkrobot.com/team-four-star\nFollow on Twitter: http://twitter.com/teamfourstar\nLike on FB: http://facebook.com/teamfourstar',
            'title': 'A Moment With TFS Episode 4',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        playerdata_url = self._search_regex(
            r'src="(http://player\.screenwavemedia\.com/play/[a-zA-Z]+\.php\?[^"]*\bid=.+?)"',
            webpage, 'player data URL')

        video_title = self._html_search_regex(
            r'<div class="heroheadingtitle">(?P<title>.+?)</div>',
            webpage, 'title')
        video_date = unified_strdate(self._html_search_regex(
            r'<div class="heroheadingdate">(?P<date>.+?)</div>',
            webpage, 'date', fatal=False))
        video_description = self._html_search_regex(
            r'(?s)<div class="postcontent">(?P<description>.+?)</div>',
            webpage, 'description', fatal=False)
        video_thumbnail = self._og_search_thumbnail(webpage)

        return {
            '_type': 'url_transparent',
            'display_id': display_id,
            'title': video_title,
            'description': video_description,
            'upload_date': video_date,
            'thumbnail': video_thumbnail,
            'url': playerdata_url,
        }
