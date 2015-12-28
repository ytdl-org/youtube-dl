from __future__ import unicode_literals

import re

from .common import InfoExtractor


class RingTVIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?ringtv\.craveonline\.com/(?P<type>news|videos/video)/(?P<id>[^/?#]+)'
    _TEST = {
        "url": "http://ringtv.craveonline.com/news/310833-luis-collazo-says-victor-ortiz-better-not-quit-on-jan-30",
        "md5": "d25945f5df41cdca2d2587165ac28720",
        "info_dict": {
            'id': '857645',
            'ext': 'mp4',
            "title": 'Video: Luis Collazo says Victor Ortiz "better not quit on Jan. 30" - Ring TV',
            "description": 'Luis Collazo is excited about his Jan. 30 showdown with fellow former welterweight titleholder Victor Ortiz at Barclays Center in his hometown of Brooklyn. The SuperBowl week fight headlines a Golden Boy Live! card on Fox Sports 1.',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id').split('-')[0]
        webpage = self._download_webpage(url, video_id)

        if mobj.group('type') == 'news':
            video_id = self._search_regex(
                r'''(?x)<iframe[^>]+src="http://cms\.springboardplatform\.com/
                        embed_iframe/[0-9]+/video/([0-9]+)/''',
                webpage, 'real video ID')
        title = self._og_search_title(webpage)
        description = self._html_search_regex(
            r'addthis:description="([^"]+)"',
            webpage, 'description', fatal=False)
        final_url = "http://ringtv.craveonline.springboardplatform.com/storage/ringtv.craveonline.com/conversion/%s.mp4" % video_id
        thumbnail_url = "http://ringtv.craveonline.springboardplatform.com/storage/ringtv.craveonline.com/snapshots/%s.jpg" % video_id

        return {
            'id': video_id,
            'url': final_url,
            'title': title,
            'thumbnail': thumbnail_url,
            'description': description,
        }
