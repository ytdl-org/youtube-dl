from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unescapeHTML,
)


class FlickrIE(InfoExtractor):
    """Information Extractor for Flickr videos"""
    _VALID_URL = r'(?:https?://)?(?:www\.|secure\.)?flickr\.com/photos/(?P<uploader_id>[\w\-_@]+)/(?P<id>\d+).*'
    _TEST = {
        'url': 'http://www.flickr.com/photos/forestwander-nature-pictures/5645318632/in/photostream/',
        'file': '5645318632.mp4',
        'md5': '6fdc01adbc89d72fc9c4f15b4a4ba87b',
        'info_dict': {
            "description": "Waterfalls in the Springtime at Dark Hollow Waterfalls. These are located just off of Skyline Drive in Virginia. They are only about 6/10 of a mile hike but it is a pretty steep hill and a good climb back up.", 
            "uploader_id": "forestwander-nature-pictures", 
            "title": "Dark Hollow Waterfalls"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        video_uploader_id = mobj.group('uploader_id')
        webpage_url = 'http://www.flickr.com/photos/' + video_uploader_id + '/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        secret = self._search_regex(r"photo_secret: '(\w+)'", webpage, 'secret')

        first_url = 'https://secure.flickr.com/apps/video/video_mtl_xml.gne?v=x&photo_id=' + video_id + '&secret=' + secret + '&bitrate=700&target=_self'
        first_xml = self._download_webpage(first_url, video_id, 'Downloading first data webpage')

        node_id = self._html_search_regex(r'<Item id="id">(\d+-\d+)</Item>',
            first_xml, 'node_id')

        second_url = 'https://secure.flickr.com/video_playlist.gne?node_id=' + node_id + '&tech=flash&mode=playlist&bitrate=700&secret=' + secret + '&rd=video.yahoo.com&noad=1'
        second_xml = self._download_webpage(second_url, video_id, 'Downloading second data webpage')

        self.report_extraction(video_id)

        mobj = re.search(r'<STREAM APP="(.+?)" FULLPATH="(.+?)"', second_xml)
        if mobj is None:
            raise ExtractorError('Unable to extract video url')
        video_url = mobj.group(1) + unescapeHTML(mobj.group(2))

        return [{
            'id':          video_id,
            'url':         video_url,
            'ext':         'mp4',
            'title':       self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail':   self._og_search_thumbnail(webpage),
            'uploader_id': video_uploader_id,
        }]
