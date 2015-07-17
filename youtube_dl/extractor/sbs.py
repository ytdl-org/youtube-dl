# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor


class SBSIE(InfoExtractor):
    IE_DESC = 'sbs.com.au'
    _VALID_URL = r'https?://(?:www\.)?sbs\.com\.au/(?:ondemand|news)/video/(?:single/)?(?P<id>[0-9]+)'

    _TESTS = [{
        # Original URL is handled by the generic IE which finds the iframe:
        # http://www.sbs.com.au/thefeed/blog/2014/08/21/dingo-conservation
        'url': 'http://www.sbs.com.au/ondemand/video/single/320403011771/?source=drupal&vertical=thefeed',
        'md5': '3150cf278965eeabb5b4cea1c963fe0a',
        'info_dict': {
            'id': '320403011771',
            'ext': 'mp4',
            'title': 'Dingo Conservation (The Feed)',
            'description': 'md5:f250a9856fca50d22dec0b5b8015f8a5',
            'thumbnail': 're:http://.*\.jpg',
            'duration': 308,
        },
    }, {
        'url': 'http://www.sbs.com.au/ondemand/video/320403011771/Dingo-Conservation-The-Feed',
        'only_matching': True,
    }, {
        'url': 'http://www.sbs.com.au/news/video/471395907773/The-Feed-July-9',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.sbs.com.au/ondemand/video/single/%s?context=web' % video_id, video_id)

        player_params = self._parse_json(
            self._search_regex(
                r'(?s)var\s+playerParams\s*=\s*({.+?});', webpage, 'playerParams'),
            video_id)

        urls = player_params['releaseUrls']
        theplatform_url = (urls.get('progressive') or urls.get('standard') or
                           urls.get('html') or player_params['relatedItemsURL'])

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': theplatform_url,
        }
