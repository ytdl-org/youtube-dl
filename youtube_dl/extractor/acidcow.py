from __future__ import unicode_literals

from .common import InfoExtractor


class acidcowIE(InfoExtractor):
    """
    InfoExtractor for acid.cow
    This class should be used to handle videos. Another class (TODO) will be
    used to implement playlists or other content.
    """
    # _VALID_URL = r'https?://app.matter.online/tracks/((?P<id>\d+)-(?P<title>\S+))/?'
    # VALID_URL = r'https?://acidcow.com/video/([0-9]+-(?P<title>\S+))/?'
    # # r'https://cdn.acidcow.com/pics/%s/video/(\S+)' % video_id, video_id
    # r'<video src="https://cdn.acidcow.com/pics/([0-9]+/(?P<title>\S+))"/>',

    # _VALID_URL = r'https?://acidcow\.com/video/[0-9]+\S+'
    _VALID_URL = r'https?://acidcow\.com/video/(?P<id>\d+)-\S+'

    _TESTS = {
        # TODO: Implement

    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        '''
        webpage = self._download_webpage(
            r'https://cdn\.acidcow\.com/pics/[0-9]+/video/\S', video_id
        )
        '''
        webpage = self._download_webpage(
            "https://acidcow.com/video/116642-that_was_really_close.html", video_id
        )

        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        '''
        download_url = self._html_search_regex(

            r'<video src="https://cdn\.acidcow\.com/pics/[0-9]+/video/\S+" .+',

            webpage, "download_url"
        )
        '''
        download_url = self._html_search_regex(

            r'(https://cdn\.acidcow\.com/pics/[0-9]+/video/\S+\.mp4)',

            webpage, "download_url"
        )
        return {
            'id': video_id,
            'url': download_url,
            'title': title
        }
