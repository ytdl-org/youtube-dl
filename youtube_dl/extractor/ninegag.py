import json
import re

from .common import InfoExtractor


class NineGagIE(InfoExtractor):
    IE_NAME = '9gag'
    _VALID_URL = r'^https?://(?:www\.)?9gag\.tv/v/(?P<id>[0-9]+)'

    _TEST = {
        u"url": u"http://9gag.tv/v/1912",
        u"file": u"1912.mp4",
        u"info_dict": {
            u"description": u"This 3-minute video will make you smile and then make you feel untalented and insignificant. Anyway, you should share this awesomeness. (Thanks, Dino!)",
            u"title": u"\"People Are Awesome 2013\" Is Absolutely Awesome"
        },
        u'add_ie': [u'Youtube']
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        data_json = self._html_search_regex(r'''(?x)
            <div\s*id="tv-video"\s*data-video-source="youtube"\s*
                data-video-meta="([^"]+)"''', webpage, u'video metadata')

        data = json.loads(data_json)

        return {
            '_type': 'url_transparent',
            'url': data['youtubeVideoId'],
            'ie_key': 'Youtube',
            'id': video_id,
            'title': data['title'],
            'description': data['description'],
            'view_count': int(data['view_count']),
            'like_count': int(data['statistic']['like']),
            'dislike_count': int(data['statistic']['dislike']),
            'thumbnail': data['thumbnail_url'],
        }
