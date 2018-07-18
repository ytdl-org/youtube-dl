from __future__ import unicode_literals

from .common import InfoExtractor


class SlutloadIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?slutload\.com/video/[^/]+/(?P<id>[^/]+)/?$'
    _TEST = {
        'url': 'http://www.slutload.com/video/virginie-baisee-en-cam/TD73btpBqSxc/',
        'md5': '868309628ba00fd488cf516a113fd717',
        'info_dict': {
            'id': 'TD73btpBqSxc',
            'ext': 'mp4',
            'title': 'virginie baisee en cam',
            'age_limit': 18,
            'thumbnail': r're:https?://.*?\.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(
            r'<h1><strong>([^<]+)</strong>',
            webpage, 'title').strip()
        video_url = self._html_search_regex(
            r'(?s)<video id=["\']desktop-player["\'].+?<source src=["\']([^"\']+)["\']',
            webpage, 'video URL')
        thumbnail = self._html_search_regex(
            r'(?s)<video id=["\']desktop-player["\'].+?poster=["\']([^"\']+)["\']',
            webpage, 'thumbnail, fatal=False'
        )

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'thumbnail': thumbnail,
            'age_limit': 18
        }


class SlutloadMobileIE(InfoExtractor):
    _VALID_URL = r'^https?://mobile\.slutload\.com/video/[^/]+/(?P<id>[^/]+)/?$'
    _TEST = {
        'url': 'http://mobile.slutload.com/video/virginie-baisee-en-cam/TD73btpBqSxc/',
        'md5': '868309628ba00fd488cf516a113fd717',
        'info_dict': {
            'id': 'TD73btpBqSxc',
            'ext': 'mp4',
            'age_limit': 18,
            'title': 'virginie baisee en cam',
            'thumbnail': r're:https?://.*?\.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(
            r'<div class=["\']videoHd[^"\']+["\']>([^<]+)</div>',
            webpage, 'title').strip()
        video_url = self._html_search_regex(
            r'(?s)<video id=["\']html5video["\'].+?src=["\']([^"\']+)["\']',
            webpage, 'video URL')
        thumbnail = self._html_search_regex(
            r'(?s)<video id=["\']html5video["\'].+?poster=["\']([^"\']+)["\']',
            webpage, 'thumbnail, fatal=False'
        )

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'thumbnail': thumbnail,
            'age_limit': 18
        }
