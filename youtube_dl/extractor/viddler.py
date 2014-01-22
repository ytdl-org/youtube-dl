import json
import re

from .common import InfoExtractor


class ViddlerIE(InfoExtractor):
    _VALID_URL = r'(?P<domain>https?://(?:www\.)?viddler\.com)/(?:v|embed|player)/(?P<id>[a-z0-9]+)'
    _TEST = {
        u"url": u"http://www.viddler.com/v/43903784",
        u'file': u'43903784.mp4',
        u'md5': u'fbbaedf7813e514eb7ca30410f439ac9',
        u'info_dict': {
            u"title": u"Video Made Easy",
            u"uploader": u"viddler",
            u"duration": 100.89,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        embed_url = mobj.group('domain') + u'/embed/' + video_id
        webpage = self._download_webpage(embed_url, video_id)

        video_sources_code = self._search_regex(
            r"(?ms)sources\s*:\s*(\{.*?\})", webpage, u'video URLs')
        video_sources = json.loads(video_sources_code.replace("'", '"'))

        formats = [{
            'url': video_url,
            'format': format_id,
        } for video_url, format_id in video_sources.items()]

        title = self._html_search_regex(
            r"title\s*:\s*'([^']*)'", webpage, u'title')
        uploader = self._html_search_regex(
            r"authorName\s*:\s*'([^']*)'", webpage, u'uploader', fatal=False)
        duration_s = self._html_search_regex(
            r"duration\s*:\s*([0-9.]*)", webpage, u'duration', fatal=False)
        duration = float(duration_s) if duration_s else None
        thumbnail = self._html_search_regex(
            r"thumbnail\s*:\s*'([^']*)'",
            webpage, u'thumbnail', fatal=False)

        return {
            '_type': 'video',
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'duration': duration,
            'formats': formats,
        }
