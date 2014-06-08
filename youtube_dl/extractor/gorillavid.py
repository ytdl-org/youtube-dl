# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

class GorillaVidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www.)?gorillavid.in/(?:embed-)?(?P<id>\w+)(?:\-\d+x\d+)?.html'
    _TEST = {
        'url': "http://gorillavid.in/kdk7i5r1p5ye.html",
        'md5': '5a01b05ed3da82a10c6659e954b80108',
        'info_dict': {
            'id': 'kdk7i5r1p5ye',
            'ext': 'flv',
            'title': 'Full House 1x16 - But Seriously, Folks.avi',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r"name=['\"]fname['\"]\s+value=['\"](.*?)['\"]", webpage, u"video title")

        # download embed page again with cookies to get url
        embed_url = "http://gorillavid.in/embed-{0}-960x480.html".format(video_id)
        webpage = self._download_webpage(embed_url, video_id, note=u'Downloading webpage again (with cookie)')
        url = self._html_search_regex(r'file:\s+["\'](http://.*?video.\w{3})["\']', webpage, url)

        info_dict = {
            'id': video_id,
            'title': title,
            'url': url,
        }

        return info_dict
