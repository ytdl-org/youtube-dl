# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_parse_qs
)
from ..utils import (
    try_get,
    clean_html,
    urlencode_postdata,
    int_or_none,
    ExtractorError
)


class CiscoLiveIE(InfoExtractor):
    IE_NAME = 'ciscolive'
    _VALID_URL = r'(?:https?://)?ciscolive\.cisco\.com/on-demand-library/\??(?P<query>[^#]+)#/(?:session/(?P<id>.+))?$'
    _TESTS = [
        {
            'url': 'https://ciscolive.cisco.com/on-demand-library/?#/session/1423353499155001FoSs',
            'md5': 'c98acf395ed9c9f766941c70f5352e22',
            'info_dict': {
                'id': '5803694304001',
                'ext': 'mp4',
                'title': '13 Smart Automations to Monitor Your Cisco IOS Network [BRKNMS-2465]',
                'description': 'md5:171c3a1c0469c126d01f083a83d6c60b',
                'timestamp': 1530305395,
                'uploader_id': '5647924234001',
                'upload_date': '20180629',
                'location': '16B Mezz.',
            },
        },
        {
            'url': 'https://ciscolive.cisco.com/on-demand-library/?search.event=ciscoliveus2018&search.technicallevel=scpsSkillLevel_aintroductory&search.focus=scpsSessionFocus_designAndDeployment#/',
            'md5': '993d4cf051f6174059328b1dce8e94bd',
            'info_dict': {
                'upload_date': '20180629',
                'title': 'DevNet Panel-Applying Design Thinking to Building Products in Cisco [DEVNET-1794]',
                'timestamp': 1530316421,
                'uploader_id': '5647924234001',
                'id': '5803751616001',
                'description': 'md5:291dbd447bf745d1f61d944d9508538f',
                'location': 'WoS, DevNet Theater',
                'ext': 'mp4',
            },
        },
        {
            'url': 'https://ciscolive.cisco.com/on-demand-library/?search.technology=scpsTechnology_applicationDevelopment&search.technology=scpsTechnology_ipv6&search.focus=scpsSessionFocus_troubleshootingTroubleshooting#/',
            'md5': '80e0c3b87e373fe3a3316b934b8915bf',
            'info_dict': {
                'upload_date': '20180629',
                'title': 'Beating the CCIE Routing & Switching [BRKCCIE-9162]',
                'timestamp': 1530311842,
                'uploader_id': '5647924234001',
                'id': '5803735679001',
                'description': 'md5:18bf6e8a634df0a51290401f209089b0',
                'location': 'Tulúm 02',
                'ext': 'mp4',
            },
        }
    ]

    # These appear to be constant across all Cisco Live presentations
    # and are not tied to any user session or event
    RAINFOCUS_API_URL = 'https://events.rainfocus.com/api/%s'
    RAINFOCUS_APIPROFILEID = 'Na3vqYdAlJFSxhYTYQGuMbpafMqftalz'
    RAINFOCUS_WIDGETID = 'n6l4Lo05R8fiy3RpUBm447dZN8uNWoye'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=%s'

    def _parse_rf_item(self, rf_item):
        ''' Parses metadata and passes to Brightcove extractor

        '''
        event_name = rf_item.get('eventName')
        cl_id = rf_item.get('abbreviation')
        title = rf_item.get('title')
        description = clean_html(rf_item.get('abstract'))
        presenter_name = try_get(rf_item, lambda x: x['participants'][0]['fullName'])
        presenter_title = try_get(rf_item, lambda x: x['participants'][0]['jobTitle'])
        pdf_url = try_get(rf_item, lambda x: x['files'][0]['url'])
        bc_id = rf_item['videos'][0]['url']
        bc_url = self.BRIGHTCOVE_URL_TEMPLATE % bc_id
        duration = int_or_none(try_get(rf_item, lambda x: x['times'][0]['length']))
        location = try_get(rf_item, lambda x: x['times'][0]['room'])

        if duration:
            duration = duration * 60

        return {
            '_type': 'url_transparent',
            'url': bc_url,
            'id': cl_id,
            'title': '%s [%s]' % (title, cl_id),
            'creator': '%s, %s' % (presenter_name, presenter_title),
            'description': '%s\n\nVideo Player: %s\nSlide Deck: %s' % (description, bc_url, pdf_url),
            'series': event_name,
            'duration': duration,
            'location': location,
            'ie_key': 'BrightcoveNew',
        }

    def _check_bc_id_exists(self, rf_item):
        ''' Checks for the existence of a Brightcove URL in a
            RainFocus result item

        '''
        bc_id = try_get(rf_item, lambda x: x['videos'][0]['url'])
        mobj = re.match(r'\d+', bc_id)
        if mobj:
            return rf_item

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        headers = {
            'Origin': 'https://ciscolive.cisco.com',
            'rfApiProfileId': self.RAINFOCUS_APIPROFILEID,
            'rfWidgetId': self.RAINFOCUS_WIDGETID,
            'Referer': url,
        }
        # Single session URL (single video)
        if mobj.group('id'):
            rf_id = mobj.group('id')
            request = self.RAINFOCUS_API_URL % 'session'
            data = urlencode_postdata({'id': rf_id})
            rf_result = self._download_json(request, rf_id, data=data, headers=headers)
            rf_item = self._check_bc_id_exists(rf_result['items'][0])
            return self._parse_rf_item(rf_item)
        else:
            # Filter query URL (multiple videos)
            rf_query = compat_parse_qs((compat_urllib_parse_urlparse(url).query))
            rf_query['type'] = 'session'
            rf_query['size'] = 1000
            data = urlencode_postdata(rf_query)
            request = self.RAINFOCUS_API_URL % 'search'
            # Query JSON results offer no obvious way to ID the search
            rf_results = self._download_json(request, 'Filter query', data=data, headers=headers)
            # Not all sessions have videos; filter them out before moving on
            rf_video_results = [
                rf_item
                for rf_item in rf_results['sectionList'][0]['items']
                if self._check_bc_id_exists(rf_item)
            ]
            entries = [self._parse_rf_item(rf_item) for rf_item in rf_video_results]
            return self.playlist_result(entries, 'Filter query')
