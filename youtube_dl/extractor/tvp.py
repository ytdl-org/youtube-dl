from __future__ import unicode_literals

from .common import InfoExtractor


class TvpIE(InfoExtractor):
    IE_NAME = 'tvp.pl'
    _VALID_URL = r'https?://www\.tvp\.pl/.*?wideo/(?P<date>\d+)/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.tvp.pl/warszawa/magazyny/campusnews/wideo/31102013/12878238',
        'md5': '148408967a6a468953c0a75cbdaf0d7a',
        'info_dict': {
            'id': '12878238',
            'ext': 'wmv',
            'title': '31.10.2013 - Odcinek 2',
            'description': '31.10.2013 - Odcinek 2',
        },
        'skip': 'Download has to use same server IP as extraction. Therefore, a good (load-balancing) DNS resolver will make the download fail.'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_url = 'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s' % video_id
        params = self._download_json(
            json_url, video_id, "Downloading video metadata")
        video_url = params['video_url']

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'ext': 'wmv',
            'url': video_url,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
