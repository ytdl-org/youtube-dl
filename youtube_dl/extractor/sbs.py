# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import remove_end


class SBSIE(InfoExtractor):
    IE_DESC = 'sbs.com.au'
    _VALID_URL = r'https?://(?:www\.)?sbs\.com\.au/ondemand/video/(?:single/)?(?P<id>[0-9]+)'

    _TESTS = [{
        # Original URL is handled by the generic IE which finds the iframe:
        # http://www.sbs.com.au/thefeed/blog/2014/08/21/dingo-conservation
        'url': 'http://www.sbs.com.au/ondemand/video/single/320403011771/?source=drupal&vertical=thefeed',
        'md5': '3150cf278965eeabb5b4cea1c963fe0a',
        'info_dict': {
            'id': '320403011771',
            'ext': 'mp4',
            'title': 'Dingo Conservation',
            'description': 'Dingoes are on the brink of extinction; most of the animals we think are dingoes are in fact crossbred with wild dogs. This family run a dingo conservation park to prevent their extinction',
            'thumbnail': 're:http://.*\.jpg',
        },
        'add_ies': ['generic'],
    }, {
        'url': 'http://www.sbs.com.au/ondemand/video/320403011771/Dingo-Conservation-The-Feed',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # the video is in the following iframe
        iframe_url = 'http://www.sbs.com.au/ondemand/video/single/' + video_id + '?context=web'
        webpage = self._download_webpage(iframe_url, video_id)

        player_params = self._search_regex(
            r'(?s)(playerParams.+?releaseUrls.+?\n)',
            webpage, 'playerParams')
        player_params_js = self._search_regex(
            r'({.*})',
            player_params, 'player_param_js')

        player_params_json = self._parse_json(player_params_js, video_id)

        theplatform_url = player_params_json.get('releaseUrls')['progressive'] or player_params_json.get('releaseUrls')['standard']

        title = remove_end(self._og_search_title(webpage, default=video_id, fatal=False), ' (The Feed)')
        description = self._html_search_meta('description', webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': theplatform_url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
