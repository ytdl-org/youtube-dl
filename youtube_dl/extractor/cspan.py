import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)

class CSpanIE(InfoExtractor):
    _VALID_URL = r'http://www.c-spanvideo.org/program/(.*)'
    _TEST = {
        u'url': u'http://www.c-spanvideo.org/program/HolderonV',
        u'file': u'315139.flv',
        u'md5': u'74a623266956f69e4df0068ab6c80fe4',
        u'info_dict': {
            u"title": u"Attorney General Eric Holder on Voting Rights Act Decision"
        },
        u'skip': u'Requires rtmpdump'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        prog_name = mobj.group(1)
        webpage = self._download_webpage(url, prog_name)
        video_id = self._search_regex(r'programid=(.*?)&', webpage, 'video id')
        data = compat_urllib_parse.urlencode({'programid': video_id,
                                              'dynamic':'1'})
        info_url = 'http://www.c-spanvideo.org/common/services/flashXml.php?' + data
        video_info = self._download_webpage(info_url, video_id, u'Downloading video info')

        self.report_extraction(video_id)

        title = self._html_search_regex(r'<string name="title">(.*?)</string>',
                                        video_info, 'title')
        description = self._html_search_regex(r'<meta (?:property="og:|name=")description" content="(.*?)"',
                                              webpage, 'description',
                                              flags=re.MULTILINE|re.DOTALL)

        url = self._search_regex(r'<string name="URL">(.*?)</string>',
                                 video_info, 'video url')
        url = url.replace('$(protocol)', 'rtmp').replace('$(port)', '443')
        path = self._search_regex(r'<string name="path">(.*?)</string>',
                            video_info, 'rtmp play path')

        return {'id': video_id,
                'title': title,
                'ext': 'flv',
                'url': url,
                'play_path': path,
                'description': description,
                'thumbnail': self._og_search_thumbnail(webpage),
                }
