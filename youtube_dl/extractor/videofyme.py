import re

from .common import InfoExtractor
from ..utils import (
    find_xpath_attr,
    determine_ext,
)

class VideofyMeIE(InfoExtractor):
    _VALID_URL = r'https?://(www\.videofy\.me/.+?|p\.videofy\.me/v)/(?P<id>\d+)(&|#|$)'
    IE_NAME = u'videofy.me'

    _TEST = {
        u'url': u'http://www.videofy.me/thisisvideofyme/1100701',
        u'file':  u'1100701.mp4',
        u'md5': u'c77d700bdc16ae2e9f3c26019bd96143',
        u'info_dict': {
            u'title': u'This is VideofyMe',
            u'description': None,
            u'uploader': u'VideofyMe',
            u'uploader_id': u'thisisvideofyme',
        },
        
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        config = self._download_xml('http://sunshine.videofy.me/?videoId=%s' % video_id,
                                            video_id)
        video = config.find('video')
        sources = video.find('sources')
        url_node = next(node for node in [find_xpath_attr(sources, 'source', 'id', 'HQ %s' % key) 
            for key in ['on', 'av', 'off']] if node is not None)
        video_url = url_node.find('url').text

        return {'id': video_id,
                'title': video.find('title').text,
                'url': video_url,
                'ext': determine_ext(video_url),
                'thumbnail': video.find('thumb').text,
                'description': video.find('description').text,
                'uploader': config.find('blog/name').text,
                'uploader_id': video.find('identifier').text,
                'view_count': re.search(r'\d+', video.find('views').text).group(),
                }
