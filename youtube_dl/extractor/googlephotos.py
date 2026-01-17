# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class GooglePhotosIE(InfoExtractor):
    _VALID_URL = r'https?://photos\.google\.com/share/(.+?)/photo/(.+?)key=(?P<id>.*)'
    _TEST = {
        'url': 'https://photos.google.com/share/AF1QipO4IcvSjf_niq1icqPYPBK50FAsKWniuyVY7Mx8sMIDKZGb71hkUi6ZK9hgIFX-mQ/photo/AF1QipNewPmRaMZquiCgyNtz4McqeLBdkXLugNB3ov6_?key=RUhSeEVVajdhcTVic3o2Wk1URWlVZEtRdnRoaTl3',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'AF1QipNewPmRaMZquiCgyNtz4McqeLBdkXLugNB3ov6_',
            'ext': 'mp4',
            'title': 'GooglePhotosVideo',
        }
    }

    _formats = YoutubeIE._formats
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        dash_formats = {}
        formats = []
        dash_mpd_fatal = True

        dash_link = self._search_regex(r'''data-url\s*=\s*('|")(?P<link>(?:(?!\1).)+)''', webpage, group='link')
        mpd_url = self._download_webpage(dash_link + '=mm,dash?alr=true', video_id)

        for df in self._extract_mpd_formats(
                mpd_url, video_id, fatal=dash_mpd_fatal,
                formats_dict=self._formats):
            dash_formats.setdefault(df['format_id'], df)

        
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': 'GooglePhotosVideo',
            'formats': formats,
        }
