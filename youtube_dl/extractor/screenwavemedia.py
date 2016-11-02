# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
    js_to_json,
)


class ScreenwaveMediaIE(InfoExtractor):
    _VALID_URL = r'(?:https?:)?//player\d?\.screenwavemedia\.com/(?:play/)?[a-zA-Z]+\.php\?.*\bid=(?P<id>[A-Za-z0-9-]+)'
    EMBED_PATTERN = r'src=(["\'])(?P<url>(?:https?:)?//player\d?\.screenwavemedia\.com/(?:play/)?[a-zA-Z]+\.php\?.*\bid=.+?)\1'
    _TESTS = [{
        'url': 'http://player.screenwavemedia.com/play/play.php?playerdiv=videoarea&companiondiv=squareAd&id=Cinemassacre-19911',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        playerdata = self._download_webpage(
            'http://player.screenwavemedia.com/player.php?id=%s' % video_id,
            video_id, 'Downloading player webpage')

        vidtitle = self._search_regex(
            r'\'vidtitle\'\s*:\s*"([^"]+)"', playerdata, 'vidtitle').replace('\\/', '/')

        playerconfig = self._download_webpage(
            'http://player.screenwavemedia.com/player.js',
            video_id, 'Downloading playerconfig webpage')

        videoserver = self._search_regex(r'SWMServer\s*=\s*"([\d\.]+)"', playerdata, 'videoserver')

        sources = self._parse_json(
            js_to_json(
                re.sub(
                    r'(?s)/\*.*?\*/', '',
                    self._search_regex(
                        r'sources\s*:\s*(\[[^\]]+?\])', playerconfig,
                        'sources',
                    ).replace(
                        "' + thisObj.options.videoserver + '",
                        videoserver
                    ).replace(
                        "' + playerVidId + '",
                        video_id
                    )
                )
            ),
            video_id, fatal=False
        )

        # Fallback to hardcoded sources if JS changes again
        if not sources:
            self.report_warning('Falling back to a hardcoded list of streams')
            sources = [{
                'file': 'http://%s/vod/%s_%s.mp4' % (videoserver, video_id, format_id),
                'type': 'mp4',
                'label': format_label,
            } for format_id, format_label in (
                ('low', '144p Low'), ('med', '160p Med'), ('high', '360p High'), ('hd1', '720p HD1'))]
            sources.append({
                'file': 'http://%s/vod/smil:%s.smil/playlist.m3u8' % (videoserver, video_id),
                'type': 'hls',
            })

        formats = []
        for source in sources:
            file_ = source.get('file')
            if not file_:
                continue
            if source.get('type') == 'hls':
                formats.extend(self._extract_m3u8_formats(file_, video_id, ext='mp4'))
            else:
                format_id = self._search_regex(
                    r'_(.+?)\.[^.]+$', file_, 'format id', default=None)
                if not self._is_valid_url(file_, video_id, format_id or 'video'):
                    continue
                format_label = source.get('label')
                height = int_or_none(self._search_regex(
                    r'^(\d+)[pP]', format_label, 'height', default=None))
                formats.append({
                    'url': file_,
                    'format_id': format_id,
                    'format': format_label,
                    'ext': source.get('type'),
                    'height': height,
                })
        self._sort_formats(formats, field_preference=('height', 'width', 'tbr', 'format_id'))

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
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
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
