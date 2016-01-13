# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor


CBC_CAFFEINE_MODULES_URL = 'http://www.cbc.ca/i/caffeine/js/Caffeine.modules.js'


class CBCIE(InfoExtractor):
    IE_DESC = 'cbc.ca'
    _VALID_URL = r'https?://(?:www\.)?cbc\.ca/.*/episodes/(?P<id>season-\d+/.+)'

    _TESTS = [{
        'url': 'http://www.cbc.ca/22minutes/episodes/season-23/episode-197',
        'md5': '9108d19314a116778932b874caf9bc91',
        'info_dict': {
            'id': 'season-23/episode-197',
            'ext': 'mp4',
            'title': '22 Minutes - S23E01 - Episode 1',
            'description': 'md5:03e943f67d535a48522b5bb4ba7cf812',
            'thumbnail': 're:http://.*\.jpg',
            'duration': 1315,
            'timestamp': 1444177800,
            'upload_date': '20151007',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        episode_page = self._download_webpage(url, video_id)

        clip_id = self._search_regex(
            r"CBC.APP.Caffeine.initInstance\({'clipId':\s*'(\d+)'",
            episode_page,
            'Clip ID'
        )

        caffeine_js = self._download_webpage(CBC_CAFFEINE_MODULES_URL, video_id)

        caffeine_content_url = self._search_regex(
            r'(http://tpfeed.cbc.ca/[a-zA-Z0-9/]+\?byContent=byReleases%3DbyId%253D)',
            caffeine_js,
            'Caffeine content URL'
        )

        caffeine_media_url = self._search_regex(
            r'(http://tpfeed.cbc.ca/[a-zA-Z0-9/_]+\?)"',
            caffeine_js,
            'Caffeine media URL'
        )

        mpx_account_id = self._search_regex(
            r'MPX_ACCOUNT_PID:"([a-zA-Z0-9/]+)"',
            caffeine_js,
            'MPX account ID'
        )

        caffeine_content = self._download_json(
            caffeine_content_url + clip_id + '&fields=content',
            video_id
        )
        media_id = caffeine_content['entries'][0]['content'][0]['releases'][0]['mediaId'].split('/')[-1]

        caffeine_media = self._download_json(
            caffeine_media_url + 'q=*&byGuid=' + media_id,
            video_id
        )

        episode_info = caffeine_media['entries'][0]
        from pprint import pprint
        pprint(episode_info)
        
        thumbnails = []
        for thumbnail in episode_info['thumbnails']:
            thumbnails.append(
                {
                    'url': thumbnail['url'],
                    'width': thumbnail['width'],
                    'height': thumbnail['height'],
                }
            )

        theplatform_url = 'http://player.theplatform.com/p/{mpx_account_id}/default_prod_vms/embed/select/media/{pid}'.format(
            mpx_account_id=mpx_account_id,
            pid=episode_info['pid']
        )

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'title': '{cbc$show} - S{cbc$seasonNumber}E{cbc$episodeNumber} - {title}'.format(**episode_info),
            'description': episode_info['description'],
            'timestamp': episode_info['pubDate']/1000,
            'url': theplatform_url,
            'thumbnails': thumbnails,
        }
