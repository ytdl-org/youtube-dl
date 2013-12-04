import re

from .common import InfoExtractor


class SlashdotIE(InfoExtractor):
    _VALID_URL = r'https?://tv\.slashdot\.org/video/\?embed=(?P<id>.*?)(&|$)'

    _TEST = {
        u'add_ie': ['Ooyala'],
        u'url': u'http://tv.slashdot.org/video/?embed=JscHMzZDplD0p-yNLOzTfzC3Q3xzJaUz',
        u'file': u'JscHMzZDplD0p-yNLOzTfzC3Q3xzJaUz.mp4',
        u'md5': u'd2222e7a4a4c1541b3e0cf732fb26735',
        u'info_dict': {
            u'title': u' Meet the Stampede Supercomputing Cluster\'s Administrator',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        ooyala_url = self._search_regex(r'<script src="(.*?)"', webpage, 'ooyala url')
        return self.url_result(ooyala_url, 'Ooyala')
