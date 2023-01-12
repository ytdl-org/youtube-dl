# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from datetime import datetime
import re
from ..utils import (
    merge_dicts
)


class Pr0grammStaticIE(InfoExtractor):
    # https://pr0gramm.com/static/5466437
    _VALID_URL = r'https?://pr0gramm\.com/static/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://pr0gramm.com/static/5466437',
        'md5': '52fa540d70d3edc286846f8ca85938aa',
        'info_dict': {
            'id': '5466437',
            'ext': 'mp4',
            'title': 'pr0gramm',
            'uploader': 'g11st',
            'upload_date': '20221221',
            'release_date': '20221221',
            'timestamp': 1671580800,
            'release_timestamp': 1671580800
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Fetch media sources
        entries = self._parse_html5_media_entries(url, webpage, video_id)
        media_info = entries[0]

        # this raises if there are no formats
        self._sort_formats(media_info.get('formats') or [])

        # Fetch author
        uploader = self._html_search_regex(r'by\W+([\w-]+)\W+', webpage, 'uploader')

        # Fetch approx upload timestamp from filename
        # Have None-defaults in case the extraction fails
        uploadDay = None
        uploadMon = None
        uploadYear = None
        uploadTimestamp = None
        uploadTimestr = None
        # (//img.pr0gramm.com/2022/12/21/62ae8aa5e2da0ebf.mp4)
        m = re.search(r'.*//img\.pr0gramm\.com/(?P<year>[0-9]+)/(?P<mon>[0-9]+)/(?P<day>[0-9]+)/\w+\.\w{,4}.*', webpage)

        if (m):
            # Up to a day of accuracy should suffice...
            uploadDay = m.groupdict().get('day')
            uploadMon = m.groupdict().get('mon')
            uploadYear = m.groupdict().get('year')
            uploadDatetime = datetime(int(uploadYear), int(uploadMon), int(uploadDay))
            epochDatetime = datetime(1970, 1, 1)
            uploadTimestamp = (uploadDatetime - epochDatetime).total_seconds()
            uploadTimestr = str(uploadYear) + str(uploadMon) + str(uploadDay)

        return merge_dicts({
            'id': video_id,
            'title': 'pr0gramm',  # Posts don't have titles. The id seems to be postfixed by yt-dl automatically.
            'uploader': uploader,
            'timestamp': uploadTimestamp,
            'release_date': uploadTimestr,
            'release_timestamp': uploadTimestamp,
            'upload_date': uploadTimestr
        }, media_info)


# This extractor is for the primary url (used for sharing, and appears in the
# location bar) Since this page loads the DOM via JS, yt-dl can't find any
# video information here. So let's redirect to a compatibility version of
# the site, which does contain the <video>-element  by itself,  without requiring
# js to be ran.
class Pr0grammIE(InfoExtractor):
    # https://pr0gramm.com/new/546637
    # https://pr0gramm.com/new/video/546637
    _VALID_URL = r'https?://pr0gramm\.com/(?:new|top)/(?:[^/]+/)?(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://pr0gramm.com/new/video/5466437',
        'info_dict': {
            'id': '5466437',
            'ext': 'mp4',
            'title': 'pr0gramm',
            'uploader': 'g11st',
            'upload_date': '20221221',
            'release_date': '20221221',
            'timestamp': 1671580800,
            'release_timestamp': 1671580800
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        return self.url_result(
            'https://pr0gramm.com/static/' + video_id,
            video_id=video_id,
            ie=Pr0grammStaticIE.ie_key())
