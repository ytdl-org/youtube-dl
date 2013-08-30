import re
import json

from .common import InfoExtractor
from ..utils import (
    clean_html,
    get_element_by_id,
)


class TechTVMITIE(InfoExtractor):
    IE_NAME = u'techtv.mit.edu'
    _VALID_URL = r'https?://techtv\.mit\.edu/(videos|embeds)/(?P<id>\d+)'

    _TEST = {
        u'url': u'http://techtv.mit.edu/videos/25418-mit-dna-learning-center-set',
        u'file': u'25418.mp4',
        u'md5': u'1f8cb3e170d41fd74add04d3c9330e5f',
        u'info_dict': {
            u'title': u'MIT DNA Learning Center Set',
            u'description': u'md5:82313335e8a8a3f243351ba55bc1b474',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        raw_page = self._download_webpage(
            'http://techtv.mit.edu/videos/%s' % video_id, video_id)
        clean_page = re.compile(u'<!--.*?-->', re.S).sub(u'', raw_page)

        base_url = self._search_regex(r'ipadUrl: \'(.+?cloudfront.net/)',
            raw_page, u'base url')
        formats_json = self._search_regex(r'bitrates: (\[.+?\])', raw_page,
            u'video formats')
        formats = json.loads(formats_json)
        formats = sorted(formats, key=lambda f: f['bitrate'])

        title = get_element_by_id('edit-title', clean_page)
        description = clean_html(get_element_by_id('edit-description', clean_page))
        thumbnail = self._search_regex(r'playlist:.*?url: \'(.+?)\'',
            raw_page, u'thumbnail', flags=re.DOTALL)

        return {'id': video_id,
                'title': title,
                'url': base_url + formats[-1]['url'].replace('mp4:', ''),
                'ext': 'mp4',
                'description': description,
                'thumbnail': thumbnail,
                }


class MITIE(TechTVMITIE):
    IE_NAME = u'video.mit.edu'
    _VALID_URL = r'https?://video\.mit\.edu/watch/(?P<title>[^/]+)'

    _TEST = {
        u'url': u'http://video.mit.edu/watch/the-government-is-profiling-you-13222/',
        u'file': u'21783.mp4',
        u'md5': u'7db01d5ccc1895fc5010e9c9e13648da',
        u'info_dict': {
            u'title': u'The Government is Profiling You',
            u'description': u'md5:ad5795fe1e1623b73620dbfd47df9afd',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        page_title = mobj.group('title')
        webpage = self._download_webpage(url, page_title)
        self.to_screen('%s: Extracting %s url' % (page_title, TechTVMITIE.IE_NAME))
        embed_url = self._search_regex(r'<iframe .*?src="(.+?)"', webpage,
            u'embed url')
        return self.url_result(embed_url, ie='TechTVMIT')
