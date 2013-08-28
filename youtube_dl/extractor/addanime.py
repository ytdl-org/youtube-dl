import re

from .common import InfoExtractor
from ..utils import (
    compat_HTTPError,
    compat_str,
    compat_urllib_parse,
    compat_urllib_parse_urlparse,

    ExtractorError,
)


class AddAnimeIE(InfoExtractor):

    _VALID_URL = r'^http://(?:\w+\.)?add-anime\.net/watch_video.php\?(?:.*?)v=(?P<video_id>[\w_]+)(?:.*)'
    IE_NAME = u'AddAnime'
    _TEST = {
        u'url': u'http://www.add-anime.net/watch_video.php?v=24MR3YO5SAS9',
        u'file': u'24MR3YO5SAS9.flv',
        u'md5': u'1036a0e0cd307b95bd8a8c3a5c8cfaf1',
        u'info_dict': {
            u"description": u"One Piece 606",
            u"title": u"One Piece 606"
        }
    }

    def _real_extract(self, url):
        try:
            mobj = re.match(self._VALID_URL, url)
            video_id = mobj.group('video_id')
            webpage = self._download_webpage(url, video_id)
        except ExtractorError as ee:
            if not isinstance(ee.cause, compat_HTTPError):
                raise

            redir_webpage = ee.cause.read().decode('utf-8')
            action = self._search_regex(
                r'<form id="challenge-form" action="([^"]+)"',
                redir_webpage, u'Redirect form')
            vc = self._search_regex(
                r'<input type="hidden" name="jschl_vc" value="([^"]+)"/>',
                redir_webpage, u'redirect vc value')
            av = re.search(
                r'a\.value = ([0-9]+)[+]([0-9]+)[*]([0-9]+);',
                redir_webpage)
            if av is None:
                raise ExtractorError(u'Cannot find redirect math task')
            av_res = int(av.group(1)) + int(av.group(2)) * int(av.group(3))

            parsed_url = compat_urllib_parse_urlparse(url)
            av_val = av_res + len(parsed_url.netloc)
            confirm_url = (
                parsed_url.scheme + u'://' + parsed_url.netloc +
                action + '?' +
                compat_urllib_parse.urlencode({
                    'jschl_vc': vc, 'jschl_answer': compat_str(av_val)}))
            self._download_webpage(
                confirm_url, video_id,
                note=u'Confirming after redirect')
            webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r"var normal_video_file = '(.*?)';",
                                       webpage, u'video file URL')
        video_title = self._og_search_title(webpage)
        video_description = self._og_search_description(webpage)

        return {
            '_type': 'video',
            'id':  video_id,
            'url': video_url,
            'ext': 'flv',
            'title': video_title,
            'description': video_description
        }
