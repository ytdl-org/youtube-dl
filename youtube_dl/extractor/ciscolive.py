# coding: utf-8
from __future__ import unicode_literals

from ..compat import compat_urllib_parse_urlencode
from .common import InfoExtractor
from ..utils import smuggle_url


class CiscoLiveIE(InfoExtractor):
    IE_NAME = 'ciscolive'
    _VALID_URL = r'https://ciscolive.cisco.com/on-demand-library/\??.*?#/session/(?P<id>.+)'
    _TEST = {
        'url': 'https://ciscolive.cisco.com/on-demand-library/?#/session/1423353499155001FoSs',
        'md5': 'c98acf395ed9c9f766941c70f5352e22',
        'info_dict': {
            'id': '5803694304001',
            'ext': 'mp4',
            'title': '13 Smart Automations to Monitor Your Cisco IOS Network',
            'timestamp': 1530305395,
            'uploader_id': '5647924234001',
            'upload_date': '20180629'
        }
    }

    # These appear to be constant across all Cisco Live presentations
    # and are not tied to any user session or event
    RAINFOCUS_SESSION_URL = 'https://events.rainfocus.com/api/session'
    RAINFOCUS_APIPROFILEID = 'Na3vqYdAlJFSxhYTYQGuMbpafMqftalz'
    RAINFOCUS_WIDGETID = 'n6l4Lo05R8fiy3RpUBm447dZN8uNWoye'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=%s'

    def _real_extract(self, url):
        session_id = self._match_id(url)
        session_info_headers = {
            'Origin': 'https://ciscolive.cisco.com',
            'rfApiProfileId': self.RAINFOCUS_APIPROFILEID,
            'rfWidgetId': self.RAINFOCUS_WIDGETID
        }
        session_info_args = {
            'url_or_request': self.RAINFOCUS_SESSION_URL,
            'video_id': session_id,
            'headers': session_info_headers,
            'data': compat_urllib_parse_urlencode({'id': session_id})
        }
        session_info = self._download_json(**session_info_args)
        brightcove_id = session_info['items'][0]['videos'][0]['url']
        video_title = session_info['items'][0]['title']

        return self.url_result(
            smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % brightcove_id,
                        {'title': video_title}),
            'BrightcoveNew', brightcove_id, video_title)
