# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_duration


class RadioBremenIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?radiobremen\.de/mediathek/(?:index\.html)?\?id=(?P<id>[0-9]+)'
    IE_NAME = 'radiobremen'

    _TEST = {
        'url': 'http://www.radiobremen.de/mediathek/index.html?id=114720',
        'info_dict': {
            'id': '114720',
            'ext': 'mp4',
            'duration': 1685,
            'width': 512,
            'title': 'buten un binnen vom 22. Dezember',
            'thumbnail': 're:https?://.*\.jpg$',
            'description': 'Unter anderem mit diesen Themen: 45 Flüchtlinge sind in Worpswede angekommen +++ Freies Internet für alle: Bremer arbeiten an einem flächendeckenden W-Lan-Netzwerk +++ Aktivisten kämpfen für das Unibad +++ So war das Wetter 2014 +++',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        meta_url = 'http://www.radiobremen.de/apps/php/mediathek/metadaten.php?id=%s' % video_id
        meta_doc = self._download_webpage(
            meta_url, video_id, 'Downloading metadata')
        title = self._html_search_regex(
            r'<h1.*>(?P<title>.+)</h1>', meta_doc, 'title')
        description = self._html_search_regex(
            r'<p>(?P<description>.*)</p>', meta_doc, 'description', fatal=False)
        duration = parse_duration(self._html_search_regex(
            r'L&auml;nge:</td>\s+<td>(?P<duration>[0-9]+:[0-9]+)</td>',
            meta_doc, 'duration', fatal=False))

        page_doc = self._download_webpage(
            url, video_id, 'Downloading video information')
        mobj = re.search(
            r"ardformatplayerclassic\(\'playerbereich\',\'(?P<width>[0-9]+)\',\'.*\',\'(?P<video_id>[0-9]+)\',\'(?P<secret>[0-9]+)\',\'(?P<thumbnail>.+)\',\'\'\)",
            page_doc)
        video_url = (
            "http://dl-ondemand.radiobremen.de/mediabase/%s/%s_%s_%s.mp4" %
            (video_id, video_id, mobj.group("secret"), mobj.group('width')))

        formats = [{
            'url': video_url,
            'ext': 'mp4',
            'width': int(mobj.group('width')),
        }]
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats,
            'thumbnail': mobj.group('thumbnail'),
        }
