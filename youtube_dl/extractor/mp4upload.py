# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re

class MP4UploadIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mp4upload\.com/embed-(?P<id>[a-z0-9]+).html'
    _TEST = {
        'url': 'https://mp4upload.com/embed-4d25ernqkj91.html',
        'info_dict': {
            'id': '4d25ernqkj91',
            'ext': 'mp4',
            'title': '4d25ernqkj91'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = video_id

        # Needed for both port and full video id
        videohotlink = re.findall(r'\|video\|(.*?)\|(.*?)\|', webpage)

        # All the info we actually need in its order
        subdomain = re.search(r'\|([^\|]*?)\|complete\|', webpage).group(1)
        port = [x[1] for x in videohotlink][0]
        fullid = [x[0] for x in videohotlink][0]

        # Compile full domain
        theurl = "https://"+subdomain+".mp4upload.com:"+port+"/d/"+fullid+"/video.mp4"

        return {
            'id': video_id,
            'title': title,
            'url': theurl
        }