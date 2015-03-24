from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    find_xpath_attr,
    int_or_none,
)


class VideofyMeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.videofy\.me/.+?|p\.videofy\.me/v)/(?P<id>\d+)(&|#|$)'
    IE_NAME = 'videofy.me'

    _TEST = {
        'url': 'http://www.videofy.me/thisisvideofyme/1100701',
        'md5': 'c77d700bdc16ae2e9f3c26019bd96143',
        'info_dict': {
            'id': '1100701',
            'ext': 'mp4',
            'title': 'This is VideofyMe',
            'description': None,
            'uploader': 'VideofyMe',
            'uploader_id': 'thisisvideofyme',
            'view_count': int,
        },

    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        config = self._download_xml('http://sunshine.videofy.me/?videoId=%s' % video_id,
                                    video_id)
        video = config.find('video')
        sources = video.find('sources')
        url_node = next(node for node in [find_xpath_attr(sources, 'source', 'id', 'HQ %s' % key)
                                          for key in ['on', 'av', 'off']] if node is not None)
        video_url = url_node.find('url').text
        view_count = int_or_none(self._search_regex(
            r'([0-9]+)', video.find('views').text, 'view count', fatal=False))

        return {
            'id': video_id,
            'title': video.find('title').text,
            'url': video_url,
            'thumbnail': video.find('thumb').text,
            'description': video.find('description').text,
            'uploader': config.find('blog/name').text,
            'uploader_id': video.find('identifier').text,
            'view_count': view_count,
        }
