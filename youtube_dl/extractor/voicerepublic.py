from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    sanitized_Request,
)


class VoiceRepublicIE(InfoExtractor):
    _VALID_URL = r'https?://voicerepublic\.com/(?:talks|embed)/(?P<id>[0-9a-z-]+)'
    _TESTS = [{
        'url': 'http://voicerepublic.com/talks/watching-the-watchers-building-a-sousveillance-state',
        'md5': '0554a24d1657915aa8e8f84e15dc9353',
        'info_dict': {
            'id': '2296',
            'display_id': 'watching-the-watchers-building-a-sousveillance-state',
            'ext': 'm4a',
            'title': 'Watching the Watchers: Building a Sousveillance State',
            'description': 'md5:715ba964958afa2398df615809cfecb1',
            'thumbnail': 're:^https?://.*\.(?:png|jpg)$',
            'duration': 1800,
            'view_count': int,
        }
    }, {
        'url': 'http://voicerepublic.com/embed/watching-the-watchers-building-a-sousveillance-state',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        req = sanitized_Request(
            compat_urlparse.urljoin(url, '/talks/%s' % display_id))
        # Older versions of Firefox get redirected to an "upgrade browser" page
        req.add_header('User-Agent', 'youtube-dl')
        webpage = self._download_webpage(req, display_id)

        if '>Queued for processing, please stand by...<' in webpage:
            raise ExtractorError(
                'Audio is still queued for processing', expected=True)

        config = self._search_regex(
            r'(?s)return ({.+?});\s*\n', webpage,
            'data', default=None)
        data = self._parse_json(config, display_id, fatal=False) if config else None
        if data:
            title = data['title']
            description = data.get('teaser')
            talk_id = data.get('talk_id') or display_id
            talk = data['talk']
            duration = int_or_none(talk.get('duration'))
            formats = [{
                'url': compat_urlparse.urljoin(url, talk_url),
                'format_id': format_id,
                'ext': determine_ext(talk_url) or format_id,
                'vcodec': 'none',
            } for format_id, talk_url in talk['links'].items()]
        else:
            title = self._og_search_title(webpage)
            description = self._html_search_regex(
                r"(?s)<div class='talk-teaser'[^>]*>(.+?)</div>",
                webpage, 'description', fatal=False)
            talk_id = self._search_regex(
                [r"id='jc-(\d+)'", r"data-shareable-id='(\d+)'"],
                webpage, 'talk id', default=None) or display_id
            duration = None
            player = self._search_regex(
                r"class='vr-player jp-jplayer'([^>]+)>", webpage, 'player')
            formats = [{
                'url': compat_urlparse.urljoin(url, talk_url),
                'format_id': format_id,
                'ext': determine_ext(talk_url) or format_id,
                'vcodec': 'none',
            } for format_id, talk_url in re.findall(r"data-([^=]+)='([^']+)'", player)]
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        view_count = int_or_none(self._search_regex(
            r"class='play-count[^']*'>\s*(\d+) plays",
            webpage, 'play count', fatal=False))

        return {
            'id': talk_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
