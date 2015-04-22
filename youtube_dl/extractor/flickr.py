from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request
from ..utils import (
    ExtractorError,
    find_xpath_attr,
)


class FlickrIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|secure\.)?flickr\.com/photos/(?P<uploader_id>[\w\-_@]+)/(?P<id>\d+).*'
    _TEST = {
        'url': 'http://www.flickr.com/photos/forestwander-nature-pictures/5645318632/in/photostream/',
        'md5': '6fdc01adbc89d72fc9c4f15b4a4ba87b',
        'info_dict': {
            'id': '5645318632',
            'ext': 'mp4',
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
        req = compat_urllib_request.Request(webpage_url)
        req.add_header(
            'User-Agent',
            # it needs a more recent version
            'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20150101 Firefox/38.0 (Chrome)')
        webpage = self._download_webpage(req, video_id)

        secret = self._search_regex(r'secret"\s*:\s*"(\w+)"', webpage, 'secret')

        first_url = 'https://secure.flickr.com/apps/video/video_mtl_xml.gne?v=x&photo_id=' + video_id + '&secret=' + secret + '&bitrate=700&target=_self'
        first_xml = self._download_xml(first_url, video_id, 'Downloading first data webpage')

        node_id = find_xpath_attr(
            first_xml, './/{http://video.yahoo.com/YEP/1.0/}Item', 'id',
            'id').text

        second_url = 'https://secure.flickr.com/video_playlist.gne?node_id=' + node_id + '&tech=flash&mode=playlist&bitrate=700&secret=' + secret + '&rd=video.yahoo.com&noad=1'
        second_xml = self._download_xml(second_url, video_id, 'Downloading second data webpage')

        self.report_extraction(video_id)

        stream = second_xml.find('.//STREAM')
        if stream is None:
            raise ExtractorError('Unable to extract video url')
        video_url = stream.attrib['APP'] + stream.attrib['FULLPATH']

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'uploader_id': video_uploader_id,
        }
