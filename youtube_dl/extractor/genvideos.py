# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import requests
import json
import urllib
from urlparse import parse_qs, urlparse


class GenVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?genvideos.org/watch\?v=(?P<id>\w+)#?' #Tests only the basic url format. Example - https://genvideos.org/watch?v=kMjlhMWE5OT
    # TODO check for other possible url formats also
    # For example
    # * http://genvideos.com/watch_kMjlhMWE5OT.html#video=tBa-Q-WkbPqwzs34b7ArqU7VomQMb2n-RAlARWKWKTI
    # * http://genvideos.org/watch_kMjlhMWE5OT.html#video=tBa-Q-WkbPqwzs34b7ArqU7VomQMb2n-RAlARWKWKTI
    _TESTS = [{
        'url': 'http://genvideos.org/watch?v=kMjlhMWE5OT',
        'md5': '666118ec1176f14259bb9f11c74bea83',
        'info_dict': {
            'id': 'kMjlhMWE5OT',
            'ext': 'mp4',
            'title': 'The Hunger Games (2012) - HD 1080p',
            'description': 'In a dystopian future, the totalitarian nation of Panem is divided between 12 districts and the Capitol. Each year two young representatives from each distri...'
            #'thumbnail': 're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }, {
        'url': 'https://genvideos.org/watch?v=Pitch_Perfect_2_2015#video=tBa-Q-WkbPqwzs34b7ArqU7VomQMb2n-RAlARWKWKTI',
        'md5': '441b5c9f0445724b0f6f9d6e5498e577',
        'info_dict':{
            'id': 'Pitch_Perfect_2_2015',
            'ext': 'mp4',
            'title': 'Pitch Perfect 2 (2015) - HD 1080p',
            'description': 'The Bellas are back, and they are better than ever. After being humiliated in front of none other than the President of the United States of America, the Bel...'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        #TODO retrieve video url
        urls_data = requests.post(
            "https://genvideos.org/video_info/iframe",
            data={'v':video_id},
            headers={'referer': 'https://genvideos.org/'}
        ) #returns json containing the url of the video (in 360p, 720p and 1080p).
        #For example - {"360":"\/\/html5player.org\/embed?url=https%3A%2F%2Flh3.googleusercontent.com%2FW6-SNGaDLWNyucD3pMqa1uMBapGDbtMTOtwpXrEu-w%3Dm18","720":"\/\/html5player.org\/embed?url=https%3A%2F%2Flh3.googleusercontent.com%2FW6-SNGaDLWNyucD3pMqa1uMBapGDbtMTOtwpXrEu-w%3Dm22","1080":"\/\/html5player.org\/embed?url=https%3A%2F%2Flh3.googleusercontent.com%2FW6-SNGaDLWNyucD3pMqa1uMBapGDbtMTOtwpXrEu-w%3Dm37"}
        urls_data_json = json.loads(urls_data.text)
        _360p_url = parse_qs(urlparse(urls_data_json['360']).query)['url'][0]
        #_360p_url = urllib.urlopen(_360p_redirect_url).geturl()
        # TODO : return all possible formats instead of just 360p

        return {
            'id': video_id,
            'title': title,
            'url': _360p_url,
            'ext': 'mp4',
            'description': self._og_search_description(webpage),
            #'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
