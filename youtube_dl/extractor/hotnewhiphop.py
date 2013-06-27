import re
import base64

from .common import InfoExtractor


class HotNewHipHopIE(InfoExtractor):
    _VALID_URL = r'http://www\.hotnewhiphop.com/.*\.(?P<id>.*)\.html'

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        webpage_src = self._download_webpage(url, video_id)

        video_url_base64 = self._search_regex(r'data-path="(.*?)"',
            webpage_src, u'video URL', fatal=False)

        if video_url_base64 == None:
            video_url = self._search_regex(r'"contentUrl" content="(.*?)"', webpage_src,
                u'video URL')
            return self.url_result(video_url, ie='Youtube')

        video_url = base64.b64decode(video_url_base64).decode('utf-8')

        video_title = self._html_search_regex(r"<title>(.*)</title>",
            webpage_src, u'title')
        
        # Getting thumbnail and if not thumbnail sets correct title for WSHH candy video.
        thumbnail = self._html_search_regex(r'"og:image" content="(.*)"',
            webpage_src, u'thumbnail', fatal=False)

        results = [{
                    'id': video_id,
                    'url' : video_url,
                    'title' : video_title,
                    'thumbnail' : thumbnail,
                    'ext' : 'mp3',
                    }]
        return results