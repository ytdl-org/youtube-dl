# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TMZIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tmz\.com/videos/(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://www.tmz.com/videos/0_okj015ty/',
        'md5': '791204e3bf790b1426cb2db0706184c0',
        'info_dict': {
            'id': '0_okj015ty',
            'url': 'http://tmz.vo.llnwd.net/o28/2014-03/13/0_okj015ty_0_rt8ro3si_2.mp4',
            'ext': 'mp4',
            'title': 'Kim Kardashian\'s Boobs Unlock a Mystery!',
            'description': 'Did Kim Kardasain try to one-up Khloe by one-upping Kylie???  Or is she just showing off her amazing boobs?',
            'thumbnail': 'http://cdnbakmi.kaltura.com/p/591531/sp/59153100/thumbnail/entry_id/0_okj015ty/version/100002/acv/182/width/640',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        return {
            'id': video_id,
            'url': self._html_search_meta('VideoURL', webpage, fatal=True),
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._html_search_meta('ThumbURL', webpage),
        }
