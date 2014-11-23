# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TeleBruxellesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?telebruxelles\.be/(news|sport|dernier-jt)/?(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'http://www.telebruxelles.be/news/auditions-devant-parlement-francken-galant-tres-attendus/',
        'md5': '59439e568c9ee42fb77588b2096b214f',
        'info_dict': {
            'id': '11942',
            'display_id': 'auditions-devant-parlement-francken-galant-tres-attendus',
            'ext': 'flv',
            'title': 'Parlement : Francken et Galant répondent aux interpellations de l’opposition',
            'description': 're:Les auditions des ministres se poursuivent*'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }, {
        'url': 'http://www.telebruxelles.be/sport/basket-brussels-bat-mons-80-74/',
        'md5': '181d3fbdcf20b909309e5aef5c6c6047',
        'info_dict': {
            'id': '10091',
            'display_id': 'basket-brussels-bat-mons-80-74',
            'ext': 'flv',
            'title': 'Basket : le Brussels bat Mons 80-74',
            'description': 're:^Ils l\u2019on fait ! En basket, le B*',
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        article_id = self._html_search_regex(
            r"<article id=\"post-(\d+)\"", webpage, 'article ID')
        title = self._html_search_regex(
            r'<h1 class=\"entry-title\">(.*?)</h1>', webpage, 'title')
        description = self._og_search_description(webpage)

        rtmp_url = self._html_search_regex(
            r"file: \"(rtmp://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}/vod/mp4:\" \+ \"\w+\" \+ \".mp4)\"",
            webpage, 'RTMP url')
        rtmp_url = rtmp_url.replace("\" + \"", "")

        return {
            'id': article_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'url': rtmp_url,
            'ext': 'flv',
            'rtmp_live': True  # if rtmpdump is not called with "--live" argument, the download is blocked and can be completed
        }
