# coding: utf-8
from __future__ import unicode_literals

<<<<<<< HEAD
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    clean_html,
    float_or_none,
=======
import re
from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_parse_qs
)
from ..utils import (
    clean_html,
>>>>>>> 2f72407593d15549a1ec6830a3cb5d7b4ad0b22b
    int_or_none,
    try_get,
    urlencode_postdata,
)


<<<<<<< HEAD
class CiscoLiveBaseIE(InfoExtractor):
    # These appear to be constant across all Cisco Live presentations
    # and are not tied to any user session or event
    RAINFOCUS_API_URL = 'https://events.rainfocus.com/api/%s'
    RAINFOCUS_API_PROFILE_ID = 'Na3vqYdAlJFSxhYTYQGuMbpafMqftalz'
    RAINFOCUS_WIDGET_ID = 'n6l4Lo05R8fiy3RpUBm447dZN8uNWoye'
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=%s'

    HEADERS = {
        'Origin': 'https://ciscolive.cisco.com',
        'rfApiProfileId': RAINFOCUS_API_PROFILE_ID,
        'rfWidgetId': RAINFOCUS_WIDGET_ID,
    }

    def _call_api(self, ep, rf_id, query, referrer, note=None):
        headers = self.HEADERS.copy()
        headers['Referer'] = referrer
        return self._download_json(
            self.RAINFOCUS_API_URL % ep, rf_id, note=note,
            data=urlencode_postdata(query), headers=headers)

    def _parse_rf_item(self, rf_item):
=======
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
                'title': '13 Smart Automations to Monitor Your Cisco IOS Network',
                'description': 'md5:ec4a436019e09a918dec17714803f7cc',
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
                'title': 'DevNet Panel-Applying Design Thinking to Building Products in Cisco',
                'timestamp': 1530316421,
                'uploader_id': '5647924234001',
                'id': '5803751616001',
                'description': 'md5:5f144575cd6848117fe2f756855b038b',
                'location': 'WoS, DevNet Theater',
                'ext': 'mp4',
            },
        },
        {
            'url': 'https://ciscolive.cisco.com/on-demand-library/?search.technology=scpsTechnology_applicationDevelopment&search.technology=scpsTechnology_ipv6&search.focus=scpsSessionFocus_troubleshootingTroubleshooting#/',
            'md5': '80e0c3b87e373fe3a3316b934b8915bf',
            'info_dict': {
                'upload_date': '20180629',
                'title': 'Beating the CCIE Routing & Switching',
                'timestamp': 1530311842,
                'uploader_id': '5647924234001',
                'id': '5803735679001',
                'description': 'md5:e71970799e92d7f5ff57ae23f64b0929',
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
        ''' Parses metadata and passes to Brightcove extractor '''
>>>>>>> 2f72407593d15549a1ec6830a3cb5d7b4ad0b22b
        event_name = rf_item.get('eventName')
        title = rf_item['title']
        description = clean_html(rf_item.get('abstract'))
        presenter_name = try_get(rf_item, lambda x: x['participants'][0]['fullName'])
        bc_id = rf_item['videos'][0]['url']
        bc_url = self.BRIGHTCOVE_URL_TEMPLATE % bc_id
<<<<<<< HEAD
        duration = float_or_none(try_get(rf_item, lambda x: x['times'][0]['length']))
=======
        duration = int_or_none(try_get(rf_item, lambda x: x['times'][0]['length']))
>>>>>>> 2f72407593d15549a1ec6830a3cb5d7b4ad0b22b
        location = try_get(rf_item, lambda x: x['times'][0]['room'])

        if duration:
            duration = duration * 60

        return {
            '_type': 'url_transparent',
<<<<<<< HEAD
            'url': bc_url,
            'ie_key': 'BrightcoveNew',
            'title': title,
            'description': description,
            'duration': duration,
            'creator': presenter_name,
            'location': location,
            'series': event_name,
        }


class CiscoLiveSessionIE(CiscoLiveBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ciscolive(?:\.cisco)?\.com/[^#]*#/session/(?P<id>[^/?&]+)'
    _TESTS = [{
        'url': 'https://ciscolive.cisco.com/global/on-demand-library/?#/session/1423353499155001FoSs',
        'md5': 'c98acf395ed9c9f766941c70f5352e22',
        'info_dict': {
            'id': '5803694304001',
            'ext': 'mp4',
            'title': '13 Smart Automations to Monitor Your Cisco IOS Network',
            'description': 'md5:ec4a436019e09a918dec17714803f7cc',
            'timestamp': 1530305395,
            'upload_date': '20180629',
            'uploader_id': '5647924234001',
            'location': '16B Mezz.',
        },
    }, {
        'url': 'https://www.ciscolive.com/global/on-demand-library.html?#/session/14479207924060017vKJ',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        rf_id = self._match_id(url)
        rf_result = self._call_api('session', rf_id, {'id': rf_id}, url)
        return self._parse_rf_item(rf_result['items'][0])


class CiscoLiveSearchIE(CiscoLiveBaseIE):
    _VALID_URL = r'https?://(?:www\.)?ciscolive(?:\.cisco)?\.com/[^?]*\?search'
    _TESTS = [{
        'url': 'https://ciscolive.cisco.com/on-demand-library/?search.event=ciscoliveus2018&search.technicallevel=scpsSkillLevel_aintroductory&search.focus=scpsSessionFocus_designAndDeployment#/',
        'info_dict': {
            'title': 'Search query',
        },
        'playlist_count': 5,
    }, {
        'url': 'https://ciscolive.cisco.com/on-demand-library/?search.technology=scpsTechnology_applicationDevelopment&search.technology=scpsTechnology_ipv6&search.focus=scpsSessionFocus_troubleshootingTroubleshooting#/',
        'only_matching': True,
    }, {
        'url': 'https://www.ciscolive.com/global/on-demand-library.html?search.event=ciscoliveemea2019#/',
        'only_matching': True,   
    }]

    @classmethod
    def suitable(cls, url):
        return False if CiscoLiveSessionIE.suitable(url) else super(CiscoLiveSearchIE, cls).suitable(url)

    @staticmethod
    def _check_bc_id_exists(rf_item):
        return int_or_none(try_get(rf_item, lambda x: x['videos'][0]['url'])) is not None

    def _entries(self, query, url):
        query['size'] = 50
        query['from'] = 0
        for page_num in itertools.count(1):
            results = self._call_api(
                'search', None, query, url,
                'Downloading search JSON page %d' % page_num)
            sl = try_get(results, lambda x: x['sectionList'][0], dict)
            if sl:
                results = sl
            items = results.get('items')
            if not items or not isinstance(items, list):
                break
            for item in items:
                if not isinstance(item, dict):
                    continue
                if not self._check_bc_id_exists(item):
                    continue
                yield self._parse_rf_item(item)
            size = int_or_none(results.get('size'))
            if size is not None:
                query['size'] = size
            total = int_or_none(results.get('total'))
            if total is not None and query['from'] + query['size'] > total:
                break
            query['from'] += query['size']

    def _real_extract(self, url):
        query = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        query['type'] = 'session'
        return self.playlist_result(
            self._entries(query, url), playlist_title='Search query')
=======
            'creator': presenter_name,
            'description': description,
            'duration': duration,
            'ie_key': 'BrightcoveNew',
            'location': location,
            'series': event_name,
            'title': title,
            'url': bc_url,
        }

    def _check_bc_id_exists(self, rf_item):
        ''' Checks for the existence of a Brightcove URL in an API result '''
        bc_id = try_get(rf_item, lambda x: x['videos'][0]['url'])
        if bc_id:
            if bc_id.strip().isdigit():
                return rf_item

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        HEADERS = {
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
            rf_result = self._download_json(request, rf_id, data=data, headers=HEADERS)
            rf_item = self._check_bc_id_exists(rf_result['items'][0])
            return self._parse_rf_item(rf_item)
        else:
            # Filter query URL (multiple videos)
            rf_query = compat_parse_qs((compat_urllib_parse_urlparse(url).query))
            rf_query['type'] = 'session'
            rf_query['size'] = 1000
            data = urlencode_postdata(rf_query)
            request = self.RAINFOCUS_API_URL % 'search'
            rf_results = self._download_json(request, 'Filter query', data=data, headers=HEADERS)
            entries = [
                self._parse_rf_item(rf_item)
                for rf_item
                in rf_results['sectionList'][0]['items']
                if self._check_bc_id_exists(rf_item)
            ]
            return self.playlist_result(entries, 'Filter query')
>>>>>>> 2f72407593d15549a1ec6830a3cb5d7b4ad0b22b
