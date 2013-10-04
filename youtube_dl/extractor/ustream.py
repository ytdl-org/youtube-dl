import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    get_meta_content,
)


class UstreamIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/recorded/(?P<videoID>\d+)'
    IE_NAME = u'ustream'
    _TEST = {
        u'url': u'http://www.ustream.tv/recorded/20274954',
        u'file': u'20274954.flv',
        u'md5': u'088f151799e8f572f84eb62f17d73e5c',
        u'info_dict': {
            u"uploader": u"Young Americans for Liberty", 
            u"title": u"Young Americans for Liberty February 7, 2012 2:28 AM"
        }
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        video_url = u'http://tcdn.ustream.tv/video/%s' % video_id
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'data-title="(?P<title>.+)"',
            webpage, u'title')

        uploader = self._html_search_regex(r'data-content-type="channel".*?>(?P<uploader>.*?)</a>',
            webpage, u'uploader', fatal=False, flags=re.DOTALL)

        thumbnail = self._html_search_regex(r'<link rel="image_src" href="(?P<thumb>.*?)"',
            webpage, u'thumbnail', fatal=False)

        info = {
                'id': video_id,
                'url': video_url,
                'ext': 'flv',
                'title': video_title,
                'uploader': uploader,
                'thumbnail': thumbnail,
               }
        return info

class UstreamChannelIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/channel/(?P<slug>.+)'
    IE_NAME = u'ustream:channel'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        slug = m.group('slug')
        webpage = self._download_webpage(url, slug)
        channel_id = get_meta_content('ustream:channel_id', webpage)

        BASE = 'http://www.ustream.tv'
        next_url = '/ajax/socialstream/videos/%s/1.json' % channel_id
        video_ids = []
        while next_url:
            reply = json.loads(self._download_webpage(compat_urlparse.urljoin(BASE, next_url), channel_id))
            video_ids.extend(re.findall(r'data-content-id="(\d.*)"', reply['data']))
            next_url = reply['nextUrl']

        urls = ['http://www.ustream.tv/recorded/' + vid for vid in video_ids]
        url_entries = [self.url_result(eurl, 'Ustream') for eurl in urls]
        return self.playlist_result(url_entries, channel_id)
