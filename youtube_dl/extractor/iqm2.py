# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from .jwplatform import JWPlatformBaseIE
from ..utils import js_to_json

# Contributed by John Hawkinson <jhawk@mit.edu>, 6 Oct 2016.

class IQM2IE(JWPlatformBaseIE):
    IE_DESC = 'IQM2 (aka Accela) livestreamed video from municipal meetings'
    # We commonly see both iqm2.com and IQM2.com.
    _VALID_URL = r'(?i)https?://(?:\w+\.)?iqm2\.com/Citizens/\w+.aspx\?.*MeetingID=(?P<id>[0-9]+)'
    _TESTS = [
        # In some cases (e.g. cambridgema.iqm2.com), after a hefty
        # (several-hour) processing time, that video is available in easily
        # downloadable form from their web portal, but prior to that, the
        # video can only be watched in realtime through JWPlayer. Other
        # (somervillecityma.iqm2.com) instances don't seem to ever offer a
        # downloadable form. This extractor is designed to download the
        # realtime video without the download links being available.
        #
        # This processing makes it hard to test since there's only a narrow
        # window when it matters. After that the extractor finds links to the
        # processed video intead.
        {
            # This is a "realtime" case
            'url': 'http://somervillecityma.iqm2.com/Citizens/SplitView.aspx?Mode=Video&MeetingID=2308',
            'md5': '9ef458ff6c93f8b9323cf79db4ede9cf',
            'info_dict': {
                'id': '70472',
                'ext': 'mp4',
                'title': 'City of Somerville, Massachusetts',
            }},
        {
            # This is a "postprocessed" case    
            'url': 'http://cambridgema.iqm2.com/Citizens/SplitView.aspx?Mode=Video&MeetingID=1679#',
            'md5': '478ea30eee1966f7be0d8dd623122148',
            'info_dict': {
                'id': '1563',
                'ext': 'mp4',
                'title': 'Cambridge, MA',
            }},
        {
            'url': 'https://CambridgeMA.IQM2.com/Citizens/VideoMain.aspx?MeetingID=1679',
            'only_matching': True,
        },
        {
            'url': 'https://CambridgeMA.IQM2.com/Citizens/VideoMain.aspx?MeetingID=1594',
            'only_matching': True,
            }
    ]

    def _find_jwplayer_data(self, webpage):
        mobj = re.search(r'SetupJWPlayer\(eval\(\'(?P<options>.+)\'\)\);', webpage)
        if mobj:
            return mobj.group('options')
        
    def _extract_jwplayer_data(self, webpage, video_id, *args, **kwargs):
        jwplayer_data = self._parse_json(
            self._find_jwplayer_data(webpage), video_id,
            transform_source=js_to_json)

        assert(isinstance(jwplayer_data, list))
        jwplayer_data = {'sources': jwplayer_data }
        jwplayer_data['tracks'] = jwplayer_data['sources'][0].get('tracks')
        
        return self._parse_jwplayer_data(
            jwplayer_data, video_id, *args, **kwargs)

    def _real_extract(self, url):
        parent_id = self._match_id(url)
        parent_page = self._download_webpage(url, parent_id)

        # Take, e.g.
        #   http://cambridgema.iqm2.com/Citizens/SplitView.aspx?Mode=Video&MeetingID=1679
        # and look for
        #   <div id="VideoPanel" class="LeftTopContent">
        #     <div id="VideoPanelInner" ... src="/Citizens/VideoScreen.aspx?MediaID=1563&Frame=SplitView">
        # and then parse the canonicalized src element
        inner_url_rel = self._html_search_regex(
            r'<div id="VideoPanelInner".*src="([^"]+)"',
            parent_page, 'url');

        inner_url = compat_urlparse.urljoin(url, inner_url_rel)
        mobj = re.match(
            r'(?i)https?://(?:\w+\.)?iqm2\.com/Citizens/\w+.aspx\?.*MediaID=(?P<id>[0-9]+)',
            inner_url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(inner_url, video_id)

        info_dict = self._extract_jwplayer_data(
            webpage, video_id, require_title=False)

        video_title = self._og_search_title(
            webpage, default=None) or self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title',
            default='video')
        info_dict['title'] = video_title

        # No metadata is retrieved, as that would require finding a metadata
        # URL and retrieving a 3rd HTTP resource.

        return info_dict
