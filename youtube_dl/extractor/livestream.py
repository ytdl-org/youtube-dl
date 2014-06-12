from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urlparse,
    xpath_with_ns,
    compat_str,
)


class LivestreamIE(InfoExtractor):
    IE_NAME = 'livestream'
    _VALID_URL = r'http://new\.livestream\.com/.*?/(?P<event_name>.*?)(/videos/(?P<id>\d+))?/?$'
    _TEST = {
        'url': 'http://new.livestream.com/CoheedandCambria/WebsterHall/videos/4719370',
        'md5': '53274c76ba7754fb0e8d072716f2292b',
        'info_dict': {
            'id': '4719370',
            'ext': 'mp4',
            'title': 'Live from Webster Hall NYC',
            'upload_date': '20121012',
        }
    }

    def _extract_video_info(self, video_data):
        video_url = video_data.get('progressive_url_hd') or video_data.get('progressive_url')
        return {
            'id': compat_str(video_data['id']),
            'url': video_url,
            'ext': 'mp4',
            'title': video_data['caption'],
            'thumbnail': video_data['thumbnail_url'],
            'upload_date': video_data['updated_at'].replace('-', '')[:8],
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        event_name = mobj.group('event_name')
        webpage = self._download_webpage(url, video_id or event_name)

        if video_id is None:
            # This is an event page:
            config_json = self._search_regex(
                r'window.config = ({.*?});', webpage, 'window config')
            info = json.loads(config_json)['event']
            videos = [self._extract_video_info(video_data['data'])
                for video_data in info['feed']['data'] if video_data['type'] == 'video']
            return self.playlist_result(videos, info['id'], info['full_name'])
        else:
            og_video = self._og_search_video_url(webpage, 'player url')
            query_str = compat_urllib_parse_urlparse(og_video).query
            query = compat_urlparse.parse_qs(query_str)
            api_url = query['play_url'][0].replace('.smil', '')
            info = json.loads(self._download_webpage(
                api_url, video_id, 'Downloading video info'))
            return self._extract_video_info(info)


# The original version of Livestream uses a different system
class LivestreamOriginalIE(InfoExtractor):
    IE_NAME = 'livestream:original'
    _VALID_URL = r'https?://www\.livestream\.com/(?P<user>[^/]+)/video\?.*?clipId=(?P<id>.*?)(&|$)'
    _TEST = {
        'url': 'http://www.livestream.com/dealbook/video?clipId=pla_8aa4a3f1-ba15-46a4-893b-902210e138fb',
        'info_dict': {
            'id': 'pla_8aa4a3f1-ba15-46a4-893b-902210e138fb',
            'ext': 'flv',
            'title': 'Spark 1 (BitCoin) with Cameron Winklevoss & Tyler Winklevoss of Winklevoss Capital',
        },
        'params': {
            # rtmp
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        user = mobj.group('user')
        api_url = 'http://x{0}x.api.channel.livestream.com/2.0/clipdetails?extendedInfo=true&id={1}'.format(user, video_id)

        info = self._download_xml(api_url, video_id)
        item = info.find('channel').find('item')
        ns = {'media': 'http://search.yahoo.com/mrss'}
        thumbnail_url = item.find(xpath_with_ns('media:thumbnail', ns)).attrib['url']
        # Remove the extension and number from the path (like 1.jpg)
        path = self._search_regex(r'(user-files/.+)_.*?\.jpg$', thumbnail_url, 'path')

        return {
            'id': video_id,
            'title': item.find('title').text,
            'url': 'rtmp://extondemand.livestream.com/ondemand',
            'play_path': 'mp4:trans/dv15/mogulus-{0}.mp4'.format(path),
            'ext': 'flv',
            'thumbnail': thumbnail_url,
        }
