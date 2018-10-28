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
    RAINFOCUS_API_URL = "https://events.rainfocus.com/api/%s"
    RAINFOCUS_APIPROFILEID = "Na3vqYdAlJFSxhYTYQGuMbpafMqftalz"
    RAINFOCUS_WIDGETID = "n6l4Lo05R8fiy3RpUBm447dZN8uNWoye"
    BRIGHTCOVE_ACCOUNT_ID = "5647924234001"
    BRIGHTCOVE_URL_TEMPLATE = "http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=%s"

    def _parse_rf_item(self, rf_item):
        """ Parses metadata and passes to Brightcove extractor
        
        """
        # Metadata parsed from Rainfocus API result
        # Not all of which is appropriate to pass to Brightcove extractor
        rf_result = {
            "event_name": rf_item.get("eventName"),
            # Full event name [Cisco Live EMEA 2016]
            "event_label": rf_item.get("eventLabel"),
            # Year/location [2016 Berlin]
            "sess_rf_id": rf_item.get("eventId"),
            # Rainfocus ID [14382715417240cleu16]
            "sess_abbr": rf_item.get("abbreviation"),
            # Shorthand session ID [BRKCRS-2501]
            "sess_title": rf_item.get("title"),
            # Full session title [Campus QoS Design-Simplified]
            "sess_desc": rf_item.get("abstract"),
            # Description [This session will apply Cisco's QoS strategy for rich media...]
            "sess_pres_name": rf_item["participants"][0]["fullName"], # TODO: Needs safe get() method
            # Presenter's full name [Tim Szigeti]
            "sess_pres_title": rf_item["participants"][0]["jobTitle"],
            # Presenter's job title [Principal Engineer - Technical Marketing]
            "sess_pdf_url": rf_item["files"][0]["url"],
            # Presentation PDF URL [https://clnv.s3.amazonaws.com/2016/eur/pdf/BRKCRS-2501.pdf]
            "sess_bc_id": rf_item["videos"][0]["url"],
            # Session Brightcove video ID [5803710412001]
            "sess_bc_url": self.BRIGHTCOVE_URL_TEMPLATE % rf_item["videos"][0]["url"],
            # Session Brightcove video URL [http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=5803710412001]
            "sess_duration": rf_item["times"][0]["length"] * 60,
            # Session duration in seconds [7200]
            "sess_location": rf_item["times"][0]["room"]
            # Session location [Hall 7.3 Breakout Room 732]
        }
        
        # Metadata passed to final Brightcove extractor
        # TODO: Only title is passed--need to work on how to best merge smuggled metadata
        metadata = {
            "id": rf_result.get("sess_abbr"),
            "title": rf_result.get("sess_title"),
            "creator": rf_result.get("sess_pres_name"),
            "description": rf_result.get("sess_desc"),
            "series": rf_result.get("event_name"),
            "duration": rf_result["sess_duration"],
            "location": rf_result["sess_location"]
        }
        self.to_screen("Session: %s [%s]" % (rf_result["sess_title"], rf_result["sess_abbr"]))
        self.to_screen("Presenter: %s, %s" % (rf_result["sess_pres_name"], rf_result["sess_pres_title"]))
        self.to_screen("Presentation PDF: %s" % rf_result["sess_pdf_url"])
        return self.url_result(
            smuggle_url(rf_result["sess_bc_url"], metadata),
                        'BrightcoveNew', rf_result["sess_bc_id"],
                        rf_result["sess_title"])

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
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
        if mobj.group('id'):
            rf_id = mobj.group('id')
            rf_api_args['url_or_request'] = self.RAINFOCUS_API_URL % 'session'
            rf_api_args['video_id'] = rf_id
            rf_api_args['data'] = compat_urllib_parse_urlencode({'id': rf_id})
            self.to_screen('Video for session ID %s' % rf_id)
            rf_api_result = self._download_json(**rf_api_args)
            rf_item = rf_api_result['items'][0]
            return self._parse_rf_item(rf_item)
        else:
            # Filter query URL (multiple videos)
            if mobj.group('query'):
                rf_query = mobj.group('query')
                rf_query = str(rf_query + "&type=session&size=1000")
                data = rf_query
                rf_api_args['url_or_request'] = self.RAINFOCUS_API_URL % 'search'
                rf_api_args['data'] = data
                # Query JSON results offer no obvious way to ID the search
                rf_api_args['video_id'] = "Filter query"
                self.to_screen('Video collection for query %s' % rf_query)
                rf_api_result = self._download_json(**rf_api_args)
                entries = [self._parse_rf_item(rf_item) for rf_item in rf_api_result['sectionList'][0]['items']]
                return self.playlist_result(entries)
