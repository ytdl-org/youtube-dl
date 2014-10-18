from __future__ import unicode_literals

import re
import datetime

from .common import InfoExtractor


class WatchIndianPornIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?(?P<url>watchindianporn\.net/video/.+?-(?P<id>[A-z0-9]+).html)$'
    _TEST = {
        'url': 'http://www.watchindianporn.net/video/desi-dancer-namrata-stripping-completely-nude-and-dancing-on-a-hot-number-dW2mtctxJfs.html',
        'md5': '9afb80675550406ed9a63ac2819ef69d',
        'info_dict': {
            'id': 'dW2mtctxJfs',
            'ext': 'mp4',
            'upload_date': '20140213',
            'uploader': 'Don',
            'title': 'Desi dancer namrata stripping completely nude and dancing on a hot number'
        }
    }

    def _real_extract(self, url):

        mobj = re.match(self._VALID_URL, url)

        video_id = self._match_id(url)
        url = "http://www." + mobj.group('url')

        webpage = self._download_webpage(url, video_id)

        ftm = '%B %d, %Y'
        date = self._html_search_regex(r'class="aup">Added: <strong>(.*?)</strong>', webpage, 'date')
        d = datetime.datetime.strptime(date, ftm)
        upload_date = d.strftime('%Y%m%d')

        title = self._html_search_regex(r'<h2 class="he2"><span>(.*?)</span>', webpage, 'title')
        video_url = self._html_search_regex(r'var playlist = \[ \{ url: escape\(\'(.*?)\'\) \} \]', webpage, 'video_url')
        thumbnail = self._html_search_regex(r'<img src="(.*?/default.jpg)"', webpage, 'thumbnail')
        uploader = self._html_search_regex(r'class="aupa">(.*?)</a>', webpage, 'uploader')
        categories = re.findall(r'http://www.watchindianporn.net/search/video/(?:.+?)"><span>(.*?)</span>', webpage)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'categories': categories
        }
