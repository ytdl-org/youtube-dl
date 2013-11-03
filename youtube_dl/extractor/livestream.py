import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse_urlparse,
    compat_urlparse,
    get_meta_content,
    ExtractorError,
)


class LivestreamIE(InfoExtractor):
    _VALID_URL = r'http://new.livestream.com/.*?/(?P<event_name>.*?)(/videos/(?P<id>\d+))?/?$'
    _TEST = {
        u'url': u'http://new.livestream.com/CoheedandCambria/WebsterHall/videos/4719370',
        u'file': u'4719370.mp4',
        u'md5': u'0d2186e3187d185a04b3cdd02b828836',
        u'info_dict': {
            u'title': u'Live from Webster Hall NYC',
            u'upload_date': u'20121012',
        }
    }

    def _extract_video_info(self, video_data):
        video_url = video_data.get('progressive_url_hd') or video_data.get('progressive_url')
        return {'id': video_data['id'],
                'url': video_url,
                'ext': 'mp4',
                'title': video_data['caption'],
                'thumbnail': video_data['thumbnail_url'],
                'upload_date': video_data['updated_at'].replace('-','')[:8],
                }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        event_name = mobj.group('event_name')
        webpage = self._download_webpage(url, video_id or event_name)

        if video_id is None:
            # This is an event page:
            config_json = self._search_regex(r'window.config = ({.*?});',
                webpage, u'window config')
            info = json.loads(config_json)['event']
            videos = [self._extract_video_info(video_data['data'])
                for video_data in info['feed']['data'] if video_data['type'] == u'video']
            return self.playlist_result(videos, info['id'], info['full_name'])
        else:
            og_video = self._og_search_video_url(webpage, name=u'player url')
            query_str = compat_urllib_parse_urlparse(og_video).query
            query = compat_urlparse.parse_qs(query_str)
            api_url = query['play_url'][0].replace('.smil', '')
            info = json.loads(self._download_webpage(api_url, video_id,
                                                     u'Downloading video info'))
            return self._extract_video_info(info)
