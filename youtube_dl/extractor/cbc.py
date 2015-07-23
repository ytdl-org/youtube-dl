from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    url_basename,
    unescapeHTML,
    js_to_json,
    ExtractorError,
)
import re


class CBCIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cbc.ca/[^/]+/'

    _TESTS = [
        {
            'url': 'http://www.cbc.ca/news/thenational/the-real-cost-of-the-world-s-most-expensive-drug-1.3126338',
            'info_dict': {
                'id': 'if3k_n58u3hDrVX9dOXSTbtHBnSZGQpe',
                'ext': 'flv',
                'title': 'The real cost of the world\'s most expensive drug',
                'description': 'md5:407fb27bb8b10c2e1447bbad0c27e551',
            },
            'add_ie': ['ThePlatform'],
        },
        {
            'url': 'http://www.cbc.ca/player/News/ID/2672225049/',
            'info_dict': {
                'id': 'VfTVl5c2pr40a9jxAMWGIRZO8Mz4ubPZ',
                'ext': 'flv',
                'title': 'WATCH: New Earth from space image released by NASA',
                'description': 'md5:3ddd36b5d1066a067a0b0c8891a72506',
            },
            'add_ie': ['ThePlatform'],
        },
        {
            'url': 'http://www.cbc.ca/natureofthings/episodes/stonehenge-uncovered',
            'info_dict': {
                'id': 'QPnDq_piKkN5x0dH7SQF85cyJb_KOsG0',
                'ext': 'flv',
                'title': 'Stonehenge Uncovered',
            },
            'add_ie': ['ThePlatform'],
            'skip': 'Canada only',
        }
    ]

    def _real_extract(self, url):
        # from http://www.cbc.ca/i/caffeine/js/Caffeine.js
        #   TP_FEED_DOMAIN:"http://tpfeed.cbc.ca/f/h9dtGB/5akSXx4Ng_Zn?"
        #   MPX_ACCOUNT_PID:"h9dtGB"
        tp_feed_domain = "http://tpfeed.cbc.ca/f/h9dtGB/5akSXx4Ng_Zn?"
        mpx_account_id = "h9dtGB"

        name = url_basename(url)

        webpage = self._download_webpage(url, name)
        title = unescapeHTML(
            self._search_regex('<title>\s*(.+?)\s*</title>', webpage, 'title'))

        cbcapp = re.findall(
            r'CBC.APP.Caffeine.initInstance\((.+?)\);', webpage, re.DOTALL)

        clipids = []
        for jstr in cbcapp:
            vdata = self._parse_json(
                jstr, 'javascript chunk', transform_source=js_to_json)
            if 'clipId' in vdata:
                if vdata['clipId'] not in clipids:
                    clipids.append(vdata['clipId'])

        vids = []
        for cid in clipids:
            feedurl = tp_feed_domain + \
                'range=1-1&byContent=byReleases%3DbyId%253D' + cid
            feedpage = self._download_webpage(feedurl, 'feed for clip ' + cid)
            cjson = self._parse_json(
                feedpage, 'clip feed json', transform_source=js_to_json)
            for ent in cjson.get('entries', []):
                for content in ent.get('content', []):
                    # assuming multi-content is playlist or multi-part video
                    vid = {}
                    for release in content.get('releases', []):
                        if 'url' in vid:
                            self.report_warning(
                                cid + ': multi-release video? Skipping, if content is missing please file a bug report')
                            continue
                        vid['url'] = 'http://link.theplatform.com/s/' + \
                            mpx_account_id + '/' + release['pid']
                    if 'url' in vid:
                        vids.append(self.url_result(vid['url']))
        if not vids:
            raise ExtractorError('No video found', expected=True)
        if len(vids) > 1:
            return self.playlist_result(vids, name, title)
        return vids[0]
