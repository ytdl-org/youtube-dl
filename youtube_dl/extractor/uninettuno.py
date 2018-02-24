from __future__ import unicode_literals
from .common import InfoExtractor
class UninettunoIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?uninettuno\.tv/Video.aspx\?v\=(?P<id>\w+)'
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage_url = 'https://www.uninettuno.tv/Video.aspx?v=' + video_id
        webpage = self._download_webpage(webpage_url, video_id)
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'[{sources: [{ file: "//(.+?)" ,type: "mp4" }]', webpage, u'video URL')
        return [{
            'id':        video_id,
            'url':       video_url,
            'ext':       'mp4',
            'title':     self._og_search_title(webpage),
        }]
