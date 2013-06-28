import re

from .common import InfoExtractor


class RingTVIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?ringtv\.craveonline\.com/videos/video/([^/]+)'
    _TEST = {
        u"url": u"http://ringtv.craveonline.com/videos/video/746619-canelo-alvarez-talks-about-mayweather-showdown",
        u"file": u"746619.mp4",
        u"md5": u"7c46b4057d22de32e0a539f017e64ad3",
        u"info_dict": {
            u"title": u"Canelo Alvarez talks about Mayweather showdown",
            u"description": u"Saul \\\"Canelo\\\" Alvarez spoke to the media about his Sept. 14 showdown with Floyd Mayweather after their kick-off presser in NYC. Canelo is motivated and confident that he will have the speed and gameplan to beat the pound-for-pound king."
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1).split('-')[0]
        webpage = self._download_webpage(url, video_id)
        title = self._search_regex(r'<title>(.+?)</title>',
        		webpage, 'video title').replace(' | RingTV','')
        description = self._search_regex(r'<div class="blurb">(.+?)</div>',
        		webpage, 'Description')
        final_url = "http://ringtv.craveonline.springboardplatform.com/storage/ringtv.craveonline.com/conversion/%s.mp4" %(str(video_id))
        thumbnail_url = "http://ringtv.craveonline.springboardplatform.com/storage/ringtv.craveonline.com/snapshots/%s.jpg" %(str(video_id))
        ext = final_url.split('.')[-1]
        return [{
            'id'          : video_id,
            'url'         : final_url,
            'ext'         : ext,
            'title'       : title,
            'thumbnail'   : thumbnail_url,
            'description' : description,
        }]

