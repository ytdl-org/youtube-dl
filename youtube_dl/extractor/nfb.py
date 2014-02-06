from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    compat_urllib_parse,
)


class NFBIE(InfoExtractor):
    IE_NAME = 'nfb'
    IE_DESC = 'National Film Board of Canada'
    _VALID_URL = r'https?://(?:www\.)?(nfb|onf)\.ca/film/(?P<id>[\da-z_-]+)'

    _TEST = {
        'url': 'https://www.nfb.ca/film/qallunaat_why_white_people_are_funny',
        'info_dict': {
            'id': 'qallunaat_why_white_people_are_funny',
            'ext': 'mp4',
            'title': 'Qallunaat! Why White People Are Funny ',
            'description': 'md5:836d8aff55e087d04d9f6df554d4e038',
            'duration': 3128,
            'uploader': 'Mark Sandiford',
            'uploader_id': 'mark-sandiford',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage('https://www.nfb.ca/film/%s' % video_id, video_id, 'Downloading film page')

        uploader_id = self._html_search_regex(r'<a class="director-link" href="/explore-all-directors/([^/]+)/"',
            page, 'director id', fatal=False)
        uploader = self._html_search_regex(r'<em class="director-name" itemprop="name">([^<]+)</em>',
            page, 'director name', fatal=False)

        request = compat_urllib_request.Request('https://www.nfb.ca/film/%s/player_config' % video_id,
            compat_urllib_parse.urlencode({'getConfig': 'true'}).encode('ascii'))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('X-NFB-Referer', 'http://www.nfb.ca/medias/flash/NFBVideoPlayer.swf')

        config = self._download_xml(request, video_id, 'Downloading player config XML')

        thumbnail = config.find("./player/stream/media[@type='posterImage']/assets/asset[@quality='high']/default/url").text
        video = config.find("./player/stream/media[@type='video']")
        duration = int(video.get('duration'))
        title = video.find('title').text
        description = video.find('description').text

        # It seems assets always go from lower to better quality, so no need to sort
        formats = [{
            'url': x.find('default/streamerURI').text + '/',
            'play_path': x.find('default/url').text,
            'rtmp_live': False,
            'ext': 'mp4',
            'format_id': x.get('quality'),
        } for x in video.findall('assets/asset')]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
        }