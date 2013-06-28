import re
import xml.etree.ElementTree

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)

class GameSpotIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?gamespot\.com/([^/]+)/videos/([^/]+)-([^/d]+)/'
    _TEST = {
        u"url": u"http://www.gamespot.com/arma-iii/videos/arma-iii-community-guide-sitrep-i-6410818/",
        u"file": u"6410818.mp4",
        u"md5": u"5569d64ca98db01f0177c934fe8c1e9b",
        u"info_dict": {
            u"title": u"Arma III - Community Guide: SITREP I",
            u"upload_date": u"20130627", 
        }
    }


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(3).split("-")[-1]
        info_url = "http://www.gamespot.com/pages/video_player/xml.php?id="+str(video_id)
        info_xml = self._download_webpage(info_url, video_id)
        doc = xml.etree.ElementTree.fromstring(info_xml)
        clip_el = doc.find('./playList/clip')

        video_url = clip_el.find('./URI').text
        title = clip_el.find('./title').text
        ext = video_url.rpartition('.')[2]
        thumbnail_url = clip_el.find('./screenGrabURI').text
        view_count = int(clip_el.find('./views').text)
        upload_date = unified_strdate(clip_el.find('./postDate').text)

        return [{
            'id'          : video_id,
            'url'         : video_url,
            'ext'         : ext,
            'title'       : title,
            'thumbnail'   : thumbnail_url,
            'upload_date' : upload_date,
            'view_count'  : view_count,
        }]
