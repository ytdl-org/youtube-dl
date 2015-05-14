# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class ScreenwaveMediaIE(InfoExtractor):
    _VALID_URL = r'http://player\d?\.screenwavemedia\.com/(?:play/)?[a-zA-Z]+\.php\?[^"]*\bid=(?P<id>.+)'

    _TESTS = [{
        'url': 'http://player.screenwavemedia.com/play/play.php?playerdiv=videoarea&companiondiv=squareAd&id=Cinemassacre-19911',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        playerdata = self._download_webpage(
            'http://player.screenwavemedia.com/play/player.php?id=%s' % video_id,
            video_id, 'Downloading player webpage')

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
            r'src="(http://player\d?\.screenwavemedia\.com/(?:play/)?[a-zA-Z]+\.php\?[^"]*\bid=.+?)"',
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
