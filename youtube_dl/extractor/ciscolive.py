# coding: utf-8
from __future__ import unicode_literals

import re
from ..compat import compat_urllib_parse_urlencode
from .common import InfoExtractor
from ..utils import smuggle_url


class CiscoLiveIE(InfoExtractor):
    IE_NAME = 'ciscolive'
    _VALID_URL = r'https://ciscolive.cisco.com/on-demand-library/\??(?P<query>[^#]+)#/(?:session/(?P<id>.+))?$'
    _TESTS = [{
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
    }, {
        'url': 'https://ciscolive.cisco.com/on-demand-library/?search.event=ciscoliveus2018&search.technicallevel=scpsSkillLevel_aintroductory&search.focus=scpsSessionFocus_designAndDeployment#/',
        'md5': '993d4cf051f6174059328b1dce8e94bd',
        'info_dict': {
            'id': '5803751616001',
            'ext': 'mp4',
            'timestamp': 1530316421,
            'title': 'DevNet Panel-Applying Design Thinking to Building Products in Cisco',
            'uploader_id': '5647924234001',
            'upload_date': '20180629',
        }
    }, {
        'url': 'https://ciscolive.cisco.com/on-demand-library/?search.technology=scpsTechnology_applicationDevelopment&search.technology=scpsTechnology_ipv6&search.focus=scpsSessionFocus_troubleshootingTroubleshooting#/',
        'md5': '80e0c3b87e373fe3a3316b934b8915bf',
        'info_dict': {
            'id': '5803735679001',
            'ext': 'mp4',
            'timestamp': 1530311842,
            'title': 'Beating the CCIE Routing & Switching',
            'uploader_id': '5647924234001',
            'upload_date': '20180629',
        }
    }]

    # These appear to be constant across all Cisco Live presentations
    # and are not tied to any user session or event
    RAINFOCUS_API_URL = 'https://events.rainfocus.com/api/%s'
    RAINFOCUS_APIPROFILEID = 'Na3vqYdAlJFSxhYTYQGuMbpafMqftalz'
    RAINFOCUS_WIDGETID = 'n6l4Lo05R8fiy3RpUBm447dZN8uNWoye'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=%s'

    def _get_brightcove_url(self, result):
        """ Returns a Brightcove URL result from Rainfocus API result

        """
        bc_id = result['videos'][0]['url']
        video_title = result['title']
        self.to_screen('Resolved Brightcove ID: %s' % bc_id)
        self.to_screen('Found video "%s"' % video_title)
        return self.url_result(
            smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % bc_id,
                        {'title': video_title}),
            'BrightcoveNew', bc_id, video_title)

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        rf_api_headers = {
            'Origin': 'https://ciscolive.cisco.com',
            'rfApiProfileId': self.RAINFOCUS_APIPROFILEID,
            'rfWidgetId': self.RAINFOCUS_WIDGETID,
            'Referer': url
        }
        rf_api_args = {
            'video_id': None,
            'headers': rf_api_headers
        }

        # Single session URL (single video)
        if m.group('id'):
            rf_id = m.group('id')
            self.to_screen('Downloading video for Cisco Live session ID %s' %
                           rf_id)
            rf_api_args['url_or_request'] = self.RAINFOCUS_API_URL % 'session'
            rf_api_args['video_id'] = rf_id
            rf_api_args['data'] = compat_urllib_parse_urlencode({'id': rf_id})
            rf_api_result = self._download_json(**rf_api_args)
            rf_item = rf_api_result['items'][0]
            return self._get_brightcove_url(rf_item)
        else:
            # Filter query URL (multiple videos)
            if m.group('query'):
                rf_query = m.group('query')
                self.to_screen('Downloading video collection for query %s' %
                               rf_query)
                rf_query = str(rf_query + "&type=session&size=1000")
                data = rf_query
                rf_api_args['url_or_request'] = self.RAINFOCUS_API_URL % 'search'
                rf_api_args['data'] = data
                rf_api_args['video_id'] = None
                rf_api_result = self._download_json(**rf_api_args)
                entries = [self._get_brightcove_url(r) for r in rf_api_result['sectionList'][0]['items']]
                return self.playlist_result(entries)
