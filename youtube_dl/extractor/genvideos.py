# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import requests
import urllib
from urlparse import parse_qs, urlparse


class GenVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?genvideos.(org|com)/watch(\?v=|_)(?P<id>\w+)#?'
    _TESTS = [{
        'url': 'http://genvideos.org/watch?v=kMjlhMWE5OT',
        'md5': 'f610bd838c21c083ede8a05ca18d55e2', #1080p quality
        'info_dict': {
            'id': 'kMjlhMWE5OT',
            'ext': 'mp4',
            'title': 'The Hunger Games (2012) - HD 1080p',
            'description': 'In a dystopian future, the totalitarian nation of Panem is divided between 12 districts and the Capitol. Each year two young representatives from each distri...'
        }
    }, {
        'url': 'https://genvideos.org/watch?v=Pitch_Perfect_2_2015#video=tBa-Q-WkbPqwzs34b7ArqU7VomQMb2n-RAlARWKWKTI',
        'md5': 'df4011514016747ea3478d1776ffece2', #1080p quality
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
        #TODO retrieve video url (using requests dependency for the moment)
        urls_data = requests.post(
            "https://genvideos.org/video_info/iframe",
            data={'v':video_id},
            headers={'referer': 'https://genvideos.org/'}
        ) #returns json containing the url of the video (in 360p, 720p and 1080p). For example - {"360":"\/\/html5player.org\/embed?url=https%3A%2F%2Flh3.googleusercontent.com%2FW6-SNGaDLWNyucD3pMqa1uMBapGDbtMTOtwpXrEu-w%3Dm18","720":"\/\/html5player.org\/embed?url=https%3A%2F%2Flh3.googleusercontent.com%2FW6-SNGaDLWNyucD3pMqa1uMBapGDbtMTOtwpXrEu-w%3Dm22","1080":"\/\/html5player.org\/embed?url=https%3A%2F%2Flh3.googleusercontent.com%2FW6-SNGaDLWNyucD3pMqa1uMBapGDbtMTOtwpXrEu-w%3Dm37"}
        urls_data_json = self._parse_json(urls_data.text,video_id)
        formats = []
        for quality in sorted(urls_data_json,key=lambda q:int(q)):
            formats.append({
                'url':parse_qs(urlparse(urls_data_json[quality]).query)['url'][0],
                'ext':'mp4',
                'format_id':quality
            })
        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'formats':formats
        }
