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

        title = None
        description = None
        thumbnail = None
        duration = None
        formats = []

        def extract_thumbnail(media):
            thumbnails = {}
            for asset in media.findall('assets/asset'):
                thumbnails[asset.get('quality')] = asset.find('default/url').text
            if not thumbnails:
                return None
            if 'high' in thumbnails:
                return thumbnails['high']
            return list(thumbnails.values())[0]

        for media in config.findall('./player/stream/media'):
            if media.get('type') == 'posterImage':
                thumbnail = extract_thumbnail(media)
            elif media.get('type') == 'video':
                duration = int(media.get('duration'))
                title = media.find('title').text
                description = media.find('description').text
                # It seems assets always go from lower to better quality, so no need to sort
                for asset in media.findall('assets/asset'):
                    for x in asset:
                        formats.append({
                            'url': x.find('streamerURI').text,
                            'app': x.find('streamerURI').text.split('/', 3)[3],
                            'play_path': x.find('url').text,
                            'rtmp_live': False,
                            'ext': 'mp4',
                            'format_id': '%s-%s' % (x.tag, asset.get('quality')),
                        })

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
