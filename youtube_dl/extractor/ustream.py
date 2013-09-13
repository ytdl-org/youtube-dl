import json
import re

from .common import InfoExtractor
from ..utils import (
    compat_urlparse,
    compat_html_parser,
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

# More robust than regular expressions

class ChannelParser(compat_html_parser.HTMLParser):
    """
    <meta name="ustream:channel_id" content="1234">
    """
    channel_id = None

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        values = dict(attrs)
        if values.get('name') != 'ustream:channel_id':
            return
        value = values.get('content', '')
        if value.isdigit():
            self.channel_id = value

class SocialstreamParser(compat_html_parser.HTMLParser):
    """
    <li class="content123 video" data-content-id="123" data-length="1452"
        data-href="/recorded/123" data-og-url="/recorded/123">
    """
    def __init__(self):
        compat_html_parser.HTMLParser.__init__(self)
        self.content_ids = []

    def handle_starttag(self, tag, attrs):
        if tag != 'li':
            return
        for (attr, value) in attrs:
            if attr == 'data-content-id' and value.isdigit():
                self.content_ids.append(value)

class UstreamChannelIE(InfoExtractor):
    _VALID_URL = r'https?://www\.ustream\.tv/channel/(?P<slug>.+)'
    IE_NAME = u'ustream:channel'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        slug = m.group('slug')

        p = ChannelParser()
        p.feed(self._download_webpage(url, slug))
        p.close()
        channel_id = p.channel_id

        p = SocialstreamParser()
        BASE = 'http://www.ustream.tv'
        next_url = '/ajax/socialstream/videos/%s/1.json' % channel_id
        while next_url:
            reply = json.loads(self._download_webpage(compat_urlparse.urljoin(BASE, next_url), channel_id))
            p.feed(reply['data'])
            next_url = reply['nextUrl']
        p.close()
        video_ids = p.content_ids

        urls = ['http://www.ustream.tv/recorded/' + vid for vid in video_ids]
        url_entries = [self.url_result(eurl, 'Ustream') for eurl in urls]
        return self.playlist_result(url_entries, channel_id)
