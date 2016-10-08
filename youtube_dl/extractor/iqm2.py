# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from .generic import GenericIE

# IQM2 aka Accela is a municipal meeting management platform that
# (among other things) stores livestreamed video from municipal
# meetings.  After a hefty (several-hour) processing time, that video
# is available in easily downloadable form from their web portal, but
# prior to that, the video can only be watched in realtime through
# JWPlayer. This extractor is designed to download the realtime video
# prior to download links being available. For more info on Accela, see:
#   http://www.iqm2.com/About/Accela.aspx
#   http://www.accela.com/

# This processing makes it challenging to produce a test case for,
# because the extractor will want to find the processed and easily
# downloadable version. So there may be interesting bugs during the
# race condition time before the processed video is available (which
# is really the only time this extractor is especially important).

# This is also a relatively braindead extractor. It parses a given page like
#   http://cambridgema.iqm2.com/Citizens/SplitView.aspx?Mode=Video&MeetingID=1679
# to determine the location of an inner div defined by a URL of the form
#   http://cambridgema.iqm2.com/Citizens/VideoScreen.aspx?MediaID=1563&Frame=SplitView
# and then feed it to the generic extractor.

# It appears that the metadata associated with the video (like its
# title) does not appear anywhere in the 2 HTML pages that get
# downloaded through this extractor. So it would need to download
# additional HTTP resources in order to get "real" metadata.

# Contributed by John Hawkinson <jhawk@mit.edu>, 6 Oct 2016.

class IQM2IE(InfoExtractor):

    # We commonly see both iqm2.com and IQM2.com.
    _VALID_URL = r'(?i)https?://(?:\w+\.)?iqm2\.com/Citizens/\w+.aspx\?.*MeetingID=(?P<id>[0-9]+)'
    _TESTS = [ {
        'url': 'http://cambridgema.iqm2.com/Citizens/SplitView.aspx?Mode=Video&MeetingID=1679#',
        'md5': '478ea30eee1966f7be0d8dd623122148',
        'info_dict': {
            'id': '1563_720',
            'ext': 'mp4',
            'title': 'Cambridge, MA (2)',
            'uploader': 'cambridgema.iqm2.com',
        }}, {
            'url': 'https://CambridgeMA.IQM2.com/Citizens/VideoMain.aspx?MeetingID=1679',
            'only_matching': True,
        }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        # print "Original URL is", url

        # <div id="VideoPanel" class="LeftTopContent">
        #   <div id="VideoPanelInner" ... src="/Citizens/VideoScreen.aspx?MediaID=1563&Frame=SplitView">
        inner_url_rel = self._html_search_regex(
            r'<div id="VideoPanelInner".*src="([^"]+)"',
            webpage, 'url');
        # print "inner_URL is", inner_url_rel

        inner_url = compat_urlparse.urljoin(url, inner_url_rel)
        # print "Joined URL is", inner_url

        # Generic extractor matches this under the "Broaden the
        # findall a little bit: JWPlayer JS loader" (line 2372 as of 6
        # Oct 2016, dcdb292fddc82ae11f4c0b647815a45c88a6b6d5).
        return self.url_result(inner_url, 'Generic')
