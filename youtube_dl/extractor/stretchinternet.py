from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class StretchInternetIE(InfoExtractor):
    _VALID_URL = r'https?://portal\.stretchinternet\.com/[^/]+/portal\.htm\?.*?\beventId=(?P<id>\d+)'
    _TEST = {
        'url': 'https://portal.stretchinternet.com/umary/portal.htm?eventId=313900&streamType=video',
        'info_dict': {
            'id': '313900',
            'ext': 'mp4',
            'title': 'Augustana (S.D.) Baseball vs University of Mary',
            'description': 'md5:7578478614aae3bdd4a90f578f787438',
            'timestamp': 1490468400,
            'upload_date': '20170325',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        stream = self._download_json(
            'https://neo-client.stretchinternet.com/streamservice/v1/media/stream/v%s'
            % video_id, video_id)

        video_url = 'https://%s' % stream['source']

        event = self._download_json(
            'https://neo-client.stretchinternet.com/portal-ws/getEvent.json',
            video_id, query={
                'clientID': 99997,
                'eventID': video_id,
                'token': 'asdf',
            })['event']

        title = event.get('title') or event['mobileTitle']
        description = event.get('customText')
        timestamp = int_or_none(event.get('longtime'))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'timestamp': timestamp,
            'url': video_url,
        }
