# encoding: utf-8
import re
import json

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    RegexNotFoundError,
)

class TvpIE(InfoExtractor):
    IE_NAME = u'tvp.pl'
    _VALID_URL = r'https?://www\.tvp\.pl/.*?wideo/(?P<date>\d+)/(?P<id>\d+)'
    _INFO_URL = 'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s'


    _TEST = {
        u'url': u'http://www.tvp.pl/warszawa/magazyny/campusnews/wideo/31102013/12878238',
        u'file': u'31.10.2013-12878238.wmv',
        u'info_dict': {
            u'title': u'31.10.2013',
            u'description': u'31.10.2013',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id, "Downloading video webpage")
        json_params = self._download_webpage(self._INFO_URL % video_id, video_id, "Downloading video metadata")

        try:
            params = json.loads(json_params)
        except:
            raise ExtractorError(u'Invalid JSON')

        self.report_extraction(video_id)
        try:
            video_url = params['video_url']
        except KeyError:
            raise ExtractorError('Missing JSON parameter: ' + sys.exc_info()[1])

        try:
            title = self._og_search_title(webpage)
        except RegexNotFoundError:
            title = video_id
        info = {
            'id': video_id,
            'title': title,
            'ext': 'wmv',
            'url': video_url,
        }
        try:
            info['description'] = self._og_search_description(webpage)
            info['thumbnail'] = self._og_search_thumbnail(webpage)
        except RegexNotFoundError:
            pass

        return info
