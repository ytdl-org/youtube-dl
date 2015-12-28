from __future__ import unicode_literals

from .common import InfoExtractor


class FoxgayIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?foxgay\.com/videos/(?:\S+-)?(?P<id>\d+)\.shtml'
    _TEST = {
        'url': 'http://foxgay.com/videos/fuck-turkish-style-2582.shtml',
        'md5': '80d72beab5d04e1655a56ad37afe6841',
        'info_dict': {
            'id': '2582',
            'ext': 'mp4',
            'title': 'md5:6122f7ae0fc6b21ebdf59c5e083ce25a',
            'description': 'md5:5e51dc4405f1fd315f7927daed2ce5cf',
            'age_limit': 18,
            'thumbnail': 're:https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>(?P<title>.*?)</title>',
            webpage, 'title', fatal=False)
        description = self._html_search_regex(
            r'<div class="ico_desc"><h2>(?P<description>.*?)</h2>',
            webpage, 'description', fatal=False)

        # Find the URL for the iFrame which contains the actual video.
        iframe = self._download_webpage(
            self._html_search_regex(r'iframe src="(?P<frame>.*?)"', webpage, 'video frame'),
            video_id)
        video_url = self._html_search_regex(
            r"v_path = '(?P<vid>http://.*?)'", iframe, 'url')
        thumb_url = self._html_search_regex(
            r"t_path = '(?P<thumb>http://.*?)'", iframe, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'description': description,
            'thumbnail': thumb_url,
            'age_limit': 18,
        }
