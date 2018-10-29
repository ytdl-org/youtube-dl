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
    }, {
        'url': 'https://ciscolive.cisco.com/on-demand-library/?search.solutions=scpsSolutions_cleanair#/',
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

    def _parse_rf_item(self, rf_item):
        """ Parses metadata and passes to Brightcove extractor

        """
        # Metadata parsed from Rainfocus API result
        # Not all of which is appropriate to pass to Brightcove extractor
        # but might be nice to print to output

        event_name = rf_item.get('eventName')
        # Full event name [Cisco Live EMEA 2016]
        # rf_id = rf_item.get('eventId')
        # Rainfocus ID [14382715417240cleu16]
        cl_id = rf_item.get('abbreviation')
        # Cisco Live ID - Shorthand session ID [BRKCRS-2501]
        title = rf_item.get('title')
        # Full session title [Campus QoS Design-Simplified]
        description = rf_item.get('abstract')
        # Description [This session will apply Cisco's QoS strategy for rich media...]
        presenter_name = rf_item['participants'][0]['fullName']  # TODO: Needs safe get() method
        # Presenter's full name [Tim Szigeti]
        presenter_title = rf_item['participants'][0]['jobTitle']
        # Presenter's job title [Principal Engineer - Technical Marketing]
        pdf_url = rf_item['files'][0]['url']
        # Presentation PDF URL [https://clnv.s3.amazonaws.com/2016/eur/pdf/BRKCRS-2501.pdf]
        bc_id = rf_item['videos'][0]['url']
        # Brightcove video ID [5803710412001]
        bc_url = self.BRIGHTCOVE_URL_TEMPLATE % bc_id
        # Brightcove video URL [http://players.brightcove.net/5647924234001/SyK2FdqjM_default/index.html?videoId=5803710412001]
        duration = rf_item['times'][0]['length'] * 60
        # Duration. Provided in minutes * 60 = seconds [7200]
        location = rf_item['times'][0]['room']
        # Location [Hall 7.3 Breakout Room 732]

        # Metadata passed to final Brightcove extractor
        # TODO: Only title is passed--need to work on how to best merge smuggled metadata
        metadata = {
            'id': cl_id,
            'title': title,
            'creator': presenter_name,
            'description': description,
            'series': event_name,
            'duration': duration,
            'location': location,
        }
        self.to_screen('Event Name: %s' % event_name)
        self.to_screen('Session ID: %s' % cl_id)
        self.to_screen('Session Title: %s' % title)
        self.to_screen('Presenter: %s, %s' % (presenter_name, presenter_title))
        self.to_screen('Slide Deck URL: %s' % pdf_url)
        self.to_screen('Video URL: %s' % bc_url)
        return self.url_result(smuggle_url(bc_url, metadata), 'BrightcoveNew', bc_id, title)

    def _check_bc_url_exists(self, rf_item):
        """ Checks for the existence of a Brightcove URL in a
            RainFocus result item

        """
        msg = "Skipping session that does not include a valid video URL: %s" % rf_item.get("title", "Unknown title")
        try:
            bc_id = rf_item["videos"][0]["url"]
            mobj = re.match(r'\d+', bc_id)
            if mobj:
                return rf_item
            else:
                self.report_warning(msg)
        except IndexError:
            self.report_warning(msg)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        rf_headers = {
            'Origin': 'https://ciscolive.cisco.com',
            'rfApiProfileId': self.RAINFOCUS_APIPROFILEID,
            'rfWidgetId': self.RAINFOCUS_WIDGETID,
            'Referer': url
        }
        rf_args = {
            'video_id': None,
            'headers': rf_headers
        }

        # Single session URL (single video)
        if mobj.group('id'):
            rf_id = mobj.group('id')
            rf_args['url_or_request'] = self.RAINFOCUS_API_URL % 'session'
            rf_args['video_id'] = rf_id
            rf_args['data'] = compat_urllib_parse_urlencode({'id': rf_id})
            rf_result = self._download_json(**rf_args)
            rf_item = self._check_bc_url_exists(rf_result['items'][0])
            return self._parse_rf_item(rf_item)
        else:
            # Filter query URL (multiple videos)
            if mobj.group('query'):
                rf_query = mobj.group('query')
                rf_query = str(rf_query + '&type=session&size=1000')
                rf_args['url_or_request'] = self.RAINFOCUS_API_URL % 'search'
                rf_args['data'] = rf_query
                # Query JSON results offer no obvious way to ID the search
                rf_args['video_id'] = 'Filter query'
                self.to_screen('Video collection for filter query "%s"' % rf_query)
                rf_results = self._download_json(**rf_args)
                # Not all sessions have videos; filter them out before moving on
                rf_video_results = [rf_item for rf_item in rf_results["sectionList"][0]["items"]
                                    if self._check_bc_url_exists(rf_item)]
                entries = [self._parse_rf_item(rf_item) for rf_item in rf_video_results]
                return self.playlist_result(entries)
