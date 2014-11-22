# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor


class TeleBruxellesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telebruxelles\.be/(news|sport|dernier-jt)/?(?P<title>[^\?]+)'
    _TESTS = [{
        'url': r'http://www.telebruxelles.be/news/auditions-devant-parlement-francken-galant-tres-attendus/',
        'md5': '59439e568c9ee42fb77588b2096b214f', 
        'info_dict': {
            'id': '11942',
            'ext': 'flv',
            'title': 're:Parlement : Francken et Galant répondent aux interpellations*',
			'description': 're:Les auditions des ministres se poursuivent*'
        }
    }, {
        'url': r'http://www.telebruxelles.be/sport/basket-brussels-bat-mons-80-74/',
        'md5': '181d3fbdcf20b909309e5aef5c6c6047', 
        'info_dict': {
            'id': '10091',
            'ext': 'flv',
            'title': 'Basket : le Brussels bat Mons 80-74',
			'description': 're:Ils l\u2019on fait ! En basket, le B*'
        }
	}]

    def _real_extract(self, url):
		mobj = re.match(self._VALID_URL, url)
		title = mobj.group('title')

		webpage = self._download_webpage(url, title)
		
		article_id = self._html_search_regex(r"<article id=\"post-(\d+)\"", webpage, '0')
		title = self._html_search_regex(r'<h1 class=\"entry-title\">(.*?)</h1>', webpage, 'title')
		description = self._html_search_regex(r"property=\"og:description\" content=\"(.*?)\"", webpage, 'description', fatal=False)
		
		rtmp_url = self._html_search_regex(r"file: \"(rtmp://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}/vod/mp4:\" \+ \"\w+\" \+ \".mp4)\"", webpage, 'url')
		rtmp_url = rtmp_url.replace("\" + \"", "")

		return {
			'id': article_id,
			'title': title,
			'description': description,
			'url': rtmp_url,
			'ext': 'flv',
			'rtmp_live': True              # if rtmpdump is not called with "--live" argument, the download is blocked and can be completed
		}