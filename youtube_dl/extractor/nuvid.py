import re

from .common import InfoExtractor

class NuvidIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www|m)\.nuvid\.com/video/(?P<videoid>\d+)'
    _TEST = {
        u'url': u'http://m.nuvid.com/video/1310741/',
        u'file': u'1310741.mp4',
        u'md5': u'eab207b7ac4fccfb4e23c86201f11277',
        u'info_dict': {
            u"title": u"Horny babes show their awesome bodeis and",
            u"age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('videoid')

        # Get webpage content
        murl = url.replace('//www.', '//m.')
        webpage = self._download_webpage(murl, video_id)

        video_title = self._html_search_regex(r'<div class="title">\s+<h2[^>]*>([^<]+)</h2>', webpage, 'video_title').strip()

        video_url = 'http://m.nuvid.com'+self._html_search_regex(r'href="(/mp4/[^"]+)"[^>]*data-link_type="mp4"', webpage, 'video_url')

        video_thumb = self._html_search_regex(r'href="(/thumbs/[^"]+)"[^>]*data-link_type="thumbs"', webpage, 'video_thumb')

        info = {'id': video_id,
                'url': video_url,
                'title': video_title,
                'thumbnail': video_thumb,
                'ext': 'mp4',
                'age_limit': 18}

        return [info]
