import re

from .common import InfoExtractor


class KeekIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?keek\.com/(?:!|\w+/keeks/)(?P<videoID>\w+)'
    IE_NAME = u'keek'
    _TEST = {
        u'url': u'https://www.keek.com/ytdl/keeks/NODfbab',
        u'file': u'NODfbab.mp4',
        u'md5': u'9b0636f8c0f7614afa4ea5e4c6e57e83',
        u'info_dict': {
            u"uploader": u"ytdl", 
            u"title": u"test chars: \"'/\\\u00e4<>This is a test video for youtube-dl.For more information, contact phihag@phihag.de ."
        }
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('videoID')

        video_url = u'http://cdn.keek.com/keek/video/%s' % video_id
        thumbnail = u'http://cdn.keek.com/keek/thumbnail/%s/w100/h75' % video_id
        webpage = self._download_webpage(url, video_id)

        video_title = self._og_search_title(webpage)

        uploader = self._html_search_regex(r'<div class="user-name-and-bio">[\S\s]+?<h2>(?P<uploader>.+?)</h2>',
            webpage, u'uploader', fatal=False)

        info = {
                'id': video_id,
                'url': video_url,
                'ext': 'mp4',
                'title': video_title,
                'thumbnail': thumbnail,
                'uploader': uploader
        }
        return [info]
