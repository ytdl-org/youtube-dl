import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TumblrIE(InfoExtractor):
    _VALID_URL = r'http://(?P<blog_name>.*?)\.tumblr\.com/((post)|(video))/(?P<id>\d*)/(.*?)'
    _TEST = {
        u'url': u'http://tatianamaslanydaily.tumblr.com/post/54196191430/orphan-black-dvd-extra-behind-the-scenes',
        u'file': u'54196191430.mp4',
        u'md5': u'479bb068e5b16462f5176a6828829767',
        u'info_dict': {
            u"title": u"tatiana maslany news"
        }
    }

    def _real_extract(self, url):
        m_url = re.match(self._VALID_URL, url)
        video_id = m_url.group('id')
        blog = m_url.group('blog_name')

        url = 'http://%s.tumblr.com/post/%s/' % (blog, video_id)
        webpage = self._download_webpage(url, video_id)

        re_video = r'src=\\x22(?P<video_url>http://%s\.tumblr\.com/video_file/%s/(.*?))\\x22 type=\\x22video/(?P<ext>.*?)\\x22' % (blog, video_id)
        video = re.search(re_video, webpage)
        if video is None:
           raise ExtractorError(u'Unable to extract video')
        video_url = video.group('video_url')
        ext = video.group('ext')

        video_thumbnail = self._search_regex(r'posters(.*?)\[\\x22(?P<thumb>.*?)\\x22',
            webpage, u'thumbnail', fatal=False)  # We pick the first poster
        if video_thumbnail: video_thumbnail = video_thumbnail.replace('\\', '')

        # The only place where you can get a title, it's not complete,
        # but searching in other places doesn't work for all videos
        video_title = self._html_search_regex(r'<title>(?P<title>.*?)(?: \| Tumblr)?</title>',
            webpage, u'title', flags=re.DOTALL)

        return [{'id': video_id,
                 'url': video_url,
                 'title': video_title,
                 'thumbnail': video_thumbnail,
                 'ext': ext
                 }]
