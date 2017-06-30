# coding: utf-8
from __future__ import unicode_literals
from ..utils import ExtractorError
from .common import InfoExtractor
import re


class TubepatrolIE(InfoExtractor):
    # i.e. http://tubepatrol.sex/to/767066/plump-asian-loves-fucking-and-sucking.html
    _VALID_URL = r'http?://(?:www\.)?tubepatrol\.sex/[^/]+/(?P<id>\d+)/(?P<display_id>[^/]+)\.html'

    _TESTS = [
        {
            # MPEG-4 video format
            'url': 'http://tubepatrol.sex/to/555439/ani-black-fox-new-czech-anal-slut-legalporno-trailer.html',
            'info_dict': {
                'id': '555439',
                'display_id': 'ani-black-fox-new-czech-anal-slut-legalporno-trailer',
                'ext': 'mp4',
                'title': 'Ani Black Fox New Czech Anal Slut [legalporno Trailer]',
            },
        },
        {
            # Flash video format
            'url': 'http://tubepatrol.sex/to/3934608/ad4x-video-dp-de-kelly-lee-trailer-hd-porn-quebec.html',
            'info_dict': {
                'id': '3934608',
                'display_id': 'ad4x-video-dp-de-kelly-lee-trailer-hd-porn-quebec',
                'ext': 'flv',
                'title': 'AD4X Video - DP De Kelly Lee Trailer HD - Porn Quebec',
            },
        },
    ]

    def _real_extract(self, url):
        # Basic extractor implementation - Video ID, Display ID, Title, URL

        # IDs

        mobj = re.match(self._VALID_URL, url)
        try:
            video_id = mobj.group('id')
            display_id = mobj.group('display_id')
        except Exception as inst:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, "The video or display ID could not be extracted: %s" % inst), expected=True)

        # get the webpage source code
        webpage = self._download_webpage(url, video_id)

        # Title

        # first try the generic header text
        video_title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'video_title', default=None)
        if video_title is None:
            # fallback to the link text provided for embed
            video_title = self._html_search_regex(r'<a\shref="%s">(.+?)</a>' % url, webpage, 'video_title', default=None)
        if video_title is None:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, "The video title could not be extracted"), expected=True)

        # the URL for the video file is contained in a seperate link as:
        # https://borfos.com/kt_player/player.php?id=<video_id>
        flashvars_webpage = self._download_webpage('https://borfos.com/kt_player/player.php?id=%s' % video_id, video_id)
        flashvars_data = self._search_regex(r'(?s)flashvars\s*=\s*({.+?})', flashvars_webpage, 'flashvars_data', default=None)
        if flashvars_data is None:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, "The flash player data could not be extracted"), expected=True)

        # URL

        # yes, we are going to use a regex to extract the video URL instead of using the JSON approach
        #
        # this is done because a bunch of extraneous fields in the flash data contain wonky characters
        # that screw up the call to _parse_json() and we do not care for these fields anyway, so ...

        # first try the generic url
        video_url = self._search_regex(r'(?s)video_url:\s"(.+?)",\s*', flashvars_data, 'video_url', default=None)
        if video_url is None:
            # fallback to the HTML5 url
            video_url = self._search_regex(r'(?s)video_html5_url:\s"(.+?)",\s*', flashvars_data, 'video_url', default=None)
        if video_url is None:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, "The video URL could not be extracted"), expected=True)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': video_title,
            'url': video_url
        }
