import re
import random

from .common import InfoExtractor


class VideoPremiumIE(InfoExtractor):
    _VALID_URL = r'(?:https?://)?(?:www\.)?videopremium\.(?:tv|me)/(?P<id>\w+)(?:/.*)?'
    _TEST = {
        u'url': u'http://videopremium.tv/4w7oadjsf156',
        u'file': u'4w7oadjsf156.f4v',
        u'info_dict': {
            u"title": u"youtube-dl_test_video____a_________-BaW_jenozKc.mp4.mp4"
        },
        u'params': {
            u'skip_download': True,
        },
        u'skip': u'Test file has been deleted.',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://videopremium.tv/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        if re.match(r"^<html><head><script[^>]*>window.location\s*=", webpage):
            # Download again, we need a cookie
            webpage = self._download_webpage(
                webpage_url, video_id,
                note=u'Downloading webpage again (with cookie)')

        video_title = self._html_search_regex(
            r'<h2(?:.*?)>\s*(.+?)\s*<', webpage, u'video title')

        return {
            'id':          video_id,
            'url':         "rtmp://e%d.md.iplay.md/play" % random.randint(1, 16),
            'play_path':   "mp4:%s.f4v" % video_id,
            'page_url':    "http://videopremium.tv/" + video_id,
            'player_url':  "http://videopremium.tv/uplayer/uppod.swf",
            'ext':         'f4v',
            'title':       video_title,
        }
