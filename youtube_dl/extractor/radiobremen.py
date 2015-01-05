# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from .common import InfoExtractor


class RadioBremenIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?radiobremen\.de/mediathek/(index\.html)?\?id=(?P<video_id>[0-9]+)'
    IE_NAME = 'radiobremen'

    _TEST = {
        'url': 'http://www.radiobremen.de/mediathek/index.html?id=114720',
        'info_dict': {
            'id': '114720',
            'ext': 'mp4',
            'width': 512,
            'title': 'buten un binnen vom 22. Dezember',
            'description': 'Unter anderem mit diesen Themen: 45 Flüchtlinge sind in Worpswede angekommen +++ Freies Internet für alle: Bremer arbeiten an einem flächendeckenden W-Lan-Netzwerk +++ Aktivisten kämpfen für das Unibad +++ So war das Wetter 2014 +++',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        meta_url = "http://www.radiobremen.de/apps/php/mediathek/metadaten.php?id=%s" % video_id
        meta_doc = self._download_webpage(meta_url, video_id, 'Downloading metadata')
        title = self._html_search_regex("<h1.*>(?P<title>.+)</h1>", meta_doc, "title")
        description = self._html_search_regex("<p>(?P<description>.*)</p>", meta_doc, "description")
        duration = self._html_search_regex("L&auml;nge:</td>\s+<td>(?P<duration>[0-9]+:[0-9]+)</td>", meta_doc, "duration")

        page_doc = self._download_webpage(url, video_id, 'Downloading video information')
        pattern = "ardformatplayerclassic\(\'playerbereich\',\'(?P<width>[0-9]+)\',\'.*\',\'(?P<video_id>[0-9]+)\',\'(?P<secret>[0-9]+)\',\'(?P<thumbnail>.+)\',\'\'\)"
        mobj = re.search(pattern, page_doc)
        width, video_id, secret, thumbnail = int(mobj.group("width")), mobj.group("video_id"), mobj.group("secret"), mobj.group("thumbnail")
        video_url = "http://dl-ondemand.radiobremen.de/mediabase/{:}/{:}_{:}_{:}.mp4".format(video_id, video_id, secret, width)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': [
                {'url': video_url,
                 'ext': 'mp4',
                 'width': width,
                 'protocol': 'http'
                 }
            ],
            'thumbnail': thumbnail,
        }
