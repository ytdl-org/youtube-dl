from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import str_to_int


class MovieFapIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?moviefap\.com/videos/(?P<id>[0-9a-f]+)/(?P<name>[a-z-_]+)'
    _TESTS = [{
        # normal, multi-format video
        'url': 'http://www.moviefap.com/videos/be9867c9416c19f54a4a/experienced-milf-amazing-handjob.html',
        'md5': '26624b4e2523051b550067d547615906',
        'info_dict': {
            'id': 'be9867c9416c19f54a4a',
            'ext': 'mp4',
            'title': 'Experienced MILF Amazing Handjob',
            'description': 'Experienced MILF giving an Amazing Handjob',
            'thumbnail': 'http://img.moviefap.com/a16:9w990r/thumbs/be/322032-20l.jpg',
            'uploader_id': 'darvinfred06',
            'display_id': 'experienced-milf-amazing-handjob',
            'categories': ['Amateur', 'Masturbation', 'Mature', 'Flashing']
        }
    }, {
        # quirky single-format case where the extension is given as fid, but the video is really an flv
        'url': 'http://www.moviefap.com/videos/e5da0d3edce5404418f5/jeune-couple-russe.html',
        'md5': 'fa56683e291fc80635907168a743c9ad',
        'info_dict': {
            'id': 'e5da0d3edce5404418f5',
            'ext': 'flv',
            'title': 'Jeune Couple Russe',
            'description': 'Amateur',
            'thumbnail': 'http://pic.moviefap.com/thumbs/e5/949-18l.jpg',
            'uploader_id': 'whiskeyjar',
            'display_id': 'jeune-couple-russe',
            'categories': ['Amateur', 'Teen']
        }
    }]

    @staticmethod
    def __get_thumbnail_data(xml):

        """
        Constructs a list of video thumbnails from timeline preview images.
        :param xml: the information XML document to parse
        """

        timeline = xml.find('timeline')
        if timeline is None:
            # not all videos have the data - ah well
            return []

        # get the required information from the XML
        width = str_to_int(timeline.find('imageWidth').text)
        height = str_to_int(timeline.find('imageHeight').text)
        first = str_to_int(timeline.find('imageFirst').text)
        last = str_to_int(timeline.find('imageLast').text)
        pattern = timeline.find('imagePattern').text

        # generate the list of thumbnail information dicts
        thumbnails = []
        for i in range(first, last + 1):
            thumbnails.append({
                'url': pattern.replace('#', str(i)),
                'width': width,
                'height': height
            })
        return thumbnails

    def _real_extract(self, url):

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # find and retrieve the XML document detailing video download URLs
        info_url = self._html_search_regex(r'flashvars\.config = escape\("(.+?)"', webpage, 'player parameters')
        xml = self._download_xml(info_url, video_id)

        info = {
            'id': video_id,
            'title': self._html_search_regex(r'<div id="view_title"><h1>(.*?)</h1>', webpage, 'title'),
            'display_id': re.compile(self._VALID_URL).match(url).group('name'),
            'thumbnails': self.__get_thumbnail_data(xml),
            'thumbnail': xml.find('startThumb').text,
            'description': self._html_search_regex(r'name="description" value="(.*?)"', webpage, 'description', fatal=False),
            'uploader_id': self._html_search_regex(r'name="username" value="(.*?)"', webpage, 'uploader_id', fatal=False),
            'view_count': str_to_int(self._html_search_regex(r'<br>Views <strong>([0-9]+)</strong>', webpage, 'view_count, fatal=False')),
            'average_rating': float(self._html_search_regex(r'Current Rating<br> <strong>(.*?)</strong>', webpage, 'average_rating', fatal=False)),
            'comment_count': str_to_int(self._html_search_regex(r'<span id="comCount">([0-9]+)</span>', webpage, 'comment_count', fatal=False)),
            'age_limit': 18,
            'webpage_url': self._html_search_regex(r'name="link" value="(.*?)"', webpage, 'webpage_url', fatal=False),
            'categories': self._html_search_regex(r'</div>\s*(.*?)\s*<br>', webpage, 'categories', fatal=False).split(', ')
        }

        # find and add the format
        if xml.find('videoConfig') is not None:
            info['ext'] = xml.find('videoConfig').find('type').text
        else:
            info['ext'] = 'flv'  # guess...

        # work out the video URL(s)
        if xml.find('videoLink') is not None:
            # single format available
            info['url'] = xml.find('videoLink').text
        else:
            # multiple formats available
            info['formats'] = []

            # N.B. formats are already in ascending order of quality
            for item in xml.find('quality').findall('item'):
                info['formats'].append({
                    'url': item.find('videoLink').text,
                    'resolution': item.find('res').text  # 480p etc.
                })

        return info
