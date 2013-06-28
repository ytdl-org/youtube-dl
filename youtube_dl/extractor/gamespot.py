import re

from .common import InfoExtractor


class GameSpotIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?gamespot\.com/([^/]+)/videos/([^/]+)-([^/d]+)/'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(3).split("-")[-1]
        webpage = self._download_webpage(url, video_id)
        title = self._search_regex(r'<title>(.+?)</title>',
                webpage, 'video title').replace('- GameSpot.com','')
        upload_date = self._search_regex(r"'publish_date':'([^/d]+)','edid'",
                webpage, 'upload date')
        description = self._search_regex(r'<meta property="og:description" content="(.+?)" />',
                webpage, 'video Description')
        info_url = "http://www.gamespot.com/pages/video_player/xml.php?id="+str(video_id)
        info_webpage = self._download_webpage(info_url, video_id , "Downloading info webpage")
        final_url = self._search_regex(r"<URI>(.+?)</URI>",
                info_webpage, 'download url')
        thumbnail_url = self._search_regex(r'<screenGrabURI allowScaling="1" maintainAspectRatio="1">(.+?)</screenGrabURI>',
                info_webpage, 'download url')
        ext = final_url.split('.')[-1]
        return [{
            'id'          : video_id,
            'url'         : final_url,
            'ext'         : ext,
            'title'       : title,
            'thumbnail'   : thumbnail_url,
            'upload_date' : upload_date,
            'description' : description,
        }]
