# coding: utf-8
from __future__ import unicode_literals

import re
from urllib.error import HTTPError

from .common import InfoExtractor


class TubeTuGrazIE(InfoExtractor):
    _VALID_URL = r'https?://tube.tugraz\.at/paella/ui/watch\.html\?id=(?P<video_id>[0-9a-f\-]+)'
    _TEST = {
        'url': 'https://tube.tugraz.at/paella/ui/watch.html?id=85dd2fa9-91ad-4d49-8c85-416fc357a3c3',
        'md5': '9e6c926c2923ae090ce67c84e880cfbf',
        'info_dict': {
            'id': '85dd2fa9-91ad-4d49-8c85-416fc357a3c3',
            'ext': 'mp4',
            'title': '#13',
            'episode': '#13',
            'creator': 'Fuchs M',
            'series': '439.002 18W Elektronische Schaltungstechnik 2',
            'duration': 4790040,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('video_id')

        information_json = self._download_json("https://tube.tugraz.at/search/episode.json", "information json")['search-results']['result']
        information = list(filter(lambda video: video["id"] == video_id, information_json))[0]

        m3u8_urls = []
        for type_ in ("presentation", "presenter"):
            m3u8_urls.append("https://wowza.tugraz.at/matterhorn_engage/smil:engage-player_%s_%s.smil/playlist.m3u8" % (video_id, type_))

        formats = []
        for m3u8_url in m3u8_urls:
            try:
                self._request_webpage(m3u8_url, video_id)
                formats.append(self._extract_m3u8_formats(m3u8_url, video_id, ext="mp4")[0])
            except HTTPError:
                continue
        try:
            series = information['mediapackage']['seriestitle']
        except KeyError:
            series = None

        return {
            'id': video_id,
            'title': information['mediapackage']['title'],
            'episode': information['mediapackage']['title'],
            'creator': information['dcCreator'],
            'series': series,
            'duration': information['mediapackage']['duration'],

            'formats': formats,
        }
