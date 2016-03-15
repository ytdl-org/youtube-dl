from __future__ import unicode_literals

from .common import InfoExtractor


class AolIE(InfoExtractor):
    IE_NAME = 'on.aol.com'
    _VALID_URL = r'(?:aol-video:|http://on\.aol\.com/video/.*-)(?P<id>[0-9]+)(?:$|\?)'

    _TESTS = [{
        'url': 'http://on.aol.com/video/u-s--official-warns-of-largest-ever-irs-phone-scam-518167793?icid=OnHomepageC2Wide_MustSee_Img',
        'md5': '18ef68f48740e86ae94b98da815eec42',
        'info_dict': {
            'id': '518167793',
            'ext': 'mp4',
            'title': 'U.S. Official Warns Of \'Largest Ever\' IRS Phone Scam',
        },
        'add_ie': ['FiveMin'],
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result('5min:%s' % video_id)


class AolFeaturesIE(InfoExtractor):
    IE_NAME = 'features.aol.com'
    _VALID_URL = r'http://features\.aol\.com/video/(?P<id>[^/?#]+)'

    _TESTS = [{
        'url': 'http://features.aol.com/video/behind-secret-second-careers-late-night-talk-show-hosts',
        'md5': '7db483bb0c09c85e241f84a34238cc75',
        'info_dict': {
            'id': '519507715',
            'ext': 'mp4',
            'title': 'What To Watch - February 17, 2016',
        },
        'add_ie': ['FiveMin'],
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        return self.url_result(self._search_regex(
            r'<script type="text/javascript" src="(https?://[^/]*?5min\.com/Scripts/PlayerSeed\.js[^"]+)"',
            webpage, '5min embed url'), 'FiveMin')
