import json
import re

from .common import InfoExtractor


class TvpIE(InfoExtractor):
    IE_NAME = u'tvp.pl'
    _VALID_URL = r'https?://www\.tvp\.pl/.*?wideo/(?P<date>\d+)/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.tvp.pl/warszawa/magazyny/campusnews/wideo/31102013/12878238',
        u'md5': u'148408967a6a468953c0a75cbdaf0d7a',
        u'file': u'12878238.wmv',
        u'info_dict': {
            u'title': u'31.10.2013 - Odcinek 2',
            u'description': u'31.10.2013 - Odcinek 2',
        },
        u'skip': u'Download has to use same server IP as extraction. Therefore, a good (load-balancing) DNS resolver will make the download fail.'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        json_url = 'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s' % video_id
        json_params = self._download_webpage(
            json_url, video_id, u"Downloading video metadata")

        params = json.loads(json_params)
        self.report_extraction(video_id)
        video_url = params['video_url']

        title = self._og_search_title(webpage, fatal=True)
        return {
            'id': video_id,
            'title': title,
            'ext': 'wmv',
            'url': video_url,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
