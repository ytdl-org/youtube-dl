import itertools
import re

from .common import SearchInfoExtractor
from ..utils import (
    compat_urllib_parse,
)


class GoogleSearchIE(SearchInfoExtractor):
    IE_DESC = u'Google Video search'
    _MORE_PAGES_INDICATOR = r'id="pnnext" class="pn"'
    _MAX_RESULTS = 1000
    IE_NAME = u'video.google:search'
    _SEARCH_KEY = 'gvsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        res = {
            '_type': 'playlist',
            'id': query,
            'entries': []
        }

        for pagenum in itertools.count(1):
            result_url = u'http://www.google.com/search?tbm=vid&q=%s&start=%s&hl=en' % (compat_urllib_parse.quote_plus(query), pagenum*10)
            webpage = self._download_webpage(result_url, u'gvsearch:' + query,
                                             note='Downloading result page ' + str(pagenum))

            for mobj in re.finditer(r'<h3 class="r"><a href="([^"]+)"', webpage):
                e = {
                    '_type': 'url',
                    'url': mobj.group(1)
                }
                res['entries'].append(e)

            if (pagenum * 10 > n) or not re.search(self._MORE_PAGES_INDICATOR, webpage):
                return res
