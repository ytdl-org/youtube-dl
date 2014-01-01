import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    get_element_by_attribute,
)


class ImdbIE(InfoExtractor):
    IE_NAME = u'imdb'
    IE_DESC = u'Internet Movie Database trailers'
    _VALID_URL = r'http://(?:www|m)\.imdb\.com/video/imdb/vi(?P<id>\d+)'

    _TEST = {
        u'url': u'http://www.imdb.com/video/imdb/vi2524815897',
        u'md5': u'9f34fa777ade3a6e57a054fdbcb3a068',
        u'info_dict': {
            u'id': u'2524815897',
            u'ext': u'mp4',
            u'title': u'Ice Age: Continental Drift Trailer (No. 2) - IMDb',
            u'description': u'md5:9061c2219254e5d14e03c25c98e96a81',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage('http://www.imdb.com/video/imdb/vi%s' % video_id, video_id)
        descr = get_element_by_attribute('itemprop', 'description', webpage)
        available_formats = re.findall(
            r'case \'(?P<f_id>.*?)\' :$\s+url = \'(?P<path>.*?)\'', webpage,
            flags=re.MULTILINE)
        formats = []
        for f_id, f_path in available_formats:
            f_path = f_path.strip()
            format_page = self._download_webpage(
                compat_urlparse.urljoin(url, f_path),
                u'Downloading info for %s format' % f_id)
            json_data = self._search_regex(
                r'<script[^>]+class="imdb-player-data"[^>]*?>(.*?)</script>',
                format_page, u'json data', flags=re.DOTALL)
            info = json.loads(json_data)
            format_info = info['videoPlayerObject']['video']
            formats.append({
                'format_id': f_id,
                'url': format_info['url'],
            })

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': descr,
            'thumbnail': format_info['slate'],
        }

class ImdbListIE(InfoExtractor):
    IE_NAME = u'imdb:list'
    IE_DESC = u'Internet Movie Database lists'
    _VALID_URL = r'http://www\.imdb\.com/list/(?P<id>[\da-zA-Z_-]{11})'
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        list_id = mobj.group('id')
        
        # RSS XML is sometimes malformed
        rss = self._download_webpage('http://rss.imdb.com/list/%s' % list_id, list_id, u'Downloading list RSS')
        list_title = self._html_search_regex(r'<title>(.*?)</title>', rss, u'list title')
        
        # Export is independent of actual author_id, but returns 404 if no author_id is provided.
        # However, passing dummy author_id seems to be enough.
        csv = self._download_webpage('http://www.imdb.com/list/export?list_id=%s&author_id=ur00000000' % list_id,
                                     list_id, u'Downloading list CSV')
        
        entries = []
        for item in csv.split('\n')[1:]:
            cols = item.split(',')
            if len(cols) < 2:
                continue
            item_id = cols[1][1:-1]
            if item_id.startswith('vi'):
                entries.append(self.url_result('http://www.imdb.com/video/imdb/%s' % item_id, 'Imdb'))
        
        return self.playlist_result(entries, list_id, list_title)