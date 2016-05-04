from __future__ import unicode_literals

from .common import InfoExtractor

class AbcGoIE(InfoExtractor):
    IE_NAME = 'abc.go.com'
    _VALID_URL = r'http://abc.go.com/shows/(?P<id>.*)'
    _TEST = {
        'url': 'http://abc.go.com/shows/marvels-agents-of-shield/episode-guide/season-03/17-the-team',
        'info_dict': {
            'id': '0_ebiua3ib',
            'ext': 'mp4',
            'title': 'The Team',
            'description': 'S.H.I.E.L.D. learns more about Hive\'s powers.',
            'uploader_id': 'KMCMigrator',
            'timestamp': 1461160081,
            'upload_date': '20160420',
        },
        'params': {
            'skip_download': True
        }
    }

    PARTNER_ID='585231'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_id = self._html_search_regex(r'vp:video="VDKA(.*?)"', webpage,
            'id')

        return {
            '_type': 'url',
            'url': 'kaltura:%s:%s' % (self.PARTNER_ID, video_id),
            'ie_key': 'Kaltura',
        }
