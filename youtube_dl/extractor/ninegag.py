from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NineGagIE(InfoExtractor):
    IE_NAME = '9gag'
    _VALID_URL = r'^https?://(?:www\.)?9gag\.tv/v/(?P<id>[0-9]+)'

    _TEST = {
        "url": "http://9gag.tv/v/1912",
        "info_dict": {
            "id": "1912",
            "ext": "mp4",
            "description": "This 3-minute video will make you smile and then make you feel untalented and insignificant. Anyway, you should share this awesomeness. (Thanks, Dino!)",
            "title": "\"People Are Awesome 2013\" Is Absolutely Awesome",
            "view_count": int,
            "thumbnail": "re:^https?://",
        },
        'add_ie': ['Youtube']
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        youtube_id = self._html_search_regex(
            r'(?s)id="jsid-video-post-container".*?data-external-id="([^"]+)"',
            webpage, 'video ID')
        description = self._html_search_regex(
            r'(?s)<div class="video-caption">.*?<p>(.*?)</p>', webpage,
            'description', fatal=False)
        view_count_str = self._html_search_regex(
            r'<p><b>([0-9][0-9,]*)</b> views</p>', webpage, 'view count',
            fatal=False)
        view_count = (
            None if view_count_str is None
            else int(view_count_str.replace(',', '')))

        return {
            '_type': 'url_transparent',
            'url': youtube_id,
            'ie_key': 'Youtube',
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': description,
            'view_count': view_count,
            'thumbnail': self._og_search_thumbnail(webpage),
        }
