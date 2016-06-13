# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class NickDeIE(InfoExtractor):
    IE_NAME = 'nick.de'
    _VALID_URL = r'https?://(?:www\.)?nick\.de/shows/(?P<id>[\d]+)[\-\w]+'
    _TESTS = []

    def _extract_mgid(self, webpage):
        return self._search_regex(r'data-contenturi="([^"]+)', webpage, 'mgid')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        viedeo_title_p1 = self._search_regex(r'<h2\s*class=[\'"]*title[\'"]*>\s*([^\<\>\\]*)\s*</h2>', webpage, 'Series Name')
        viedeo_title_p2 = self._search_regex(r'<h4\s*class=[\'"]*title[\'"]*>\s*([^\<\>\\]*)\s*</h4>', webpage,'Episode Name')
        metadata_regex = r'data-mrss="(http://gakusei-cluster\.mtvnn\.com/v2/mrss\.xml\?uri=mgid\:sensei\:video\:mtvnn.com\:local_playlist-[\w]+)"'
        meta_url = self._search_regex(metadata_regex, webpage, 'nick.de metadata')
        metadata = self._download_webpage(meta_url, video_id,'Downloading metadata')
        ply_regex_str = r'url=\'(http\://videos\.mtvnn\.com/mediagen/[\w]+)\''
        ply_list_url = self._search_regex(ply_regex_str,metadata,'nick.de playlist url')
        video_title = viedeo_title_p1 + ' - ' + viedeo_title_p2
        video_title = video_title.replace(r'/',r'-')
        video_title = video_title.replace(r'“','')
        video_title = video_title.replace(r'”“','')
        pl_dat = self._download_webpage(ply_list_url,video_id,'Downloading Playlist')
        vurl_regex = r'<src>(rtmp://cp[\d]+\.edgefcs\.net/ondemand/riptide/r[\d]+/production/[\d]+/[\d]+/[\d]+/[\w]+/mp4_640px_[\w\d]+\.mp4)</src>'
        vurl = self._search_regex(vurl_regex,pl_dat,'Videourl')
        return {
            'id': video_id,
            'title': video_title,
            'ext': 'mp4',
            'description': self._og_search_description(webpage),
            'url': vurl
            # TODO more properties (see youtube_dl/extractor/common.py)
        }