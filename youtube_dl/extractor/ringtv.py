import re

from .common import InfoExtractor


class RingTvIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?ringtv\.craveonline\.com/videos/video/([^/]+)'

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

