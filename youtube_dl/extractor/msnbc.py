# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class MSNBCIE(InfoExtractor):
    _VALID_URL = r'http://www\.msnbc\.com/(?P<showname>[a-z0-9-]+)/watch/(?P<id>[a-z0-9-]+)'

    _TESTS = [{
        'url': 'http://www.msnbc.com/morning-joe/watch/american-trains-iraqis-in-fight-against-isis-465258051578',
        'info_dict': {
            'id': 'n_mj_vandyke_150616_647133',
            'title': 'American trains Iraqis in fight against ISIS',
            'description': 'md5:6432ea377a7f0bc6981d4c4fc48d4c4e',
            'timestamp': 1434451583,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        guid = self._html_search_meta('nv:videoId', webpage, 'guid')

        playlist_json = self._download_json('http://feed.theplatform.com/f/7wvmTC/msnbc_video-p-test?form=json&byGuid=%s' % (guid), guid)

        entry = playlist_json['entries'][0]

        thumbnails = [{
            'url': thumb['plfile$url'],
            'width': thumb['plfile$width'],
            'height': thumb['plfile$height'],
        } for thumb in entry['media$thumbnails']]

        for content_item in entry['media$content']:
            return {
                '_type': 'url_transparent',
                'ie_key': 'ThePlatform',
                'id': guid,
                'title': entry['title'],
                'description': entry['description'],
                'timestamp': entry['media$availableDate'] / 1000,
                'thumbnails': thumbnails,
                'url': content_item['plfile$url'],
            }
