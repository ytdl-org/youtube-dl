# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class GooglePhotosIE(InfoExtractor):
    _VALID_URL = r'https?://photos\.google\.com/share/(.+?)/photo/(.+?)key=(?P<id>.*)'
    _TEST = {
        'url': 'https://photos.google.com/share/AF1QipO9WO5MnYm7850JgwAl7DIvRzbCoEcJamtywXL-oQ49rwF3K1frOSK63fjYD5MD-A/photo/AF1QipPRvvdy6-3EOqSACtJb7Q8QfmlXN4d4MwX5ico8?key=ZEV4S3RmYXd0bWNzQjRfQ09KQlBud1M4OUU1RzZn',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 'ZEV4S3RmYXd0bWNzQjRfQ09KQlBud1M4OUU1RzZn',
            'ext': 'mp4',
            'title': 'GooglePhotosVideo',
        }
    }

    _formats = {
        '133': {'ext': 'mp4', 'height': 240, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '134': {'ext': 'mp4', 'height': 360, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '135': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '136': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '137': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '138': {'ext': 'mp4', 'format_note': 'DASH video', 'vcodec': 'h264'},
        '160': {'ext': 'mp4', 'height': 144, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '212': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '264': {'ext': 'mp4', 'height': 1440, 'format_note': 'DASH video', 'vcodec': 'h264'},
        '298': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'h264', 'fps': 60},
        '299': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'vcodec': 'h264', 'fps': 60},
        '266': {'ext': 'mp4', 'height': 2160, 'format_note': 'DASH video', 'vcodec': 'h264'},

        '139': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 48, 'container': 'm4a_dash'},
        '140': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 128, 'container': 'm4a_dash'},
        '141': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'abr': 256, 'container': 'm4a_dash'},
        '256': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'container': 'm4a_dash'},
        '258': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'container': 'm4a_dash'},
        '325': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'dtse', 'container': 'm4a_dash'},
        '328': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'ec-3', 'container': 'm4a_dash'},
    }
    
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        dash_formats = {}
        formats = []
        dash_mpd_fatal = True

        dash_link = self._html_search_regex(r'data-url="(.+?)"', webpage, '')
        mpd_url = self._download_webpage(dash_link + '=mm,dash?alr=true', video_id)

        for df in self._extract_mpd_formats(
                mpd_url, video_id, fatal=dash_mpd_fatal,
                formats_dict=self._formats):
            if df['format_id'] not in dash_formats:
                dash_formats[df['format_id']] = df

        if dash_formats:
            formats = [f for f in formats if f['format_id'] not in dash_formats.keys()]
            formats.extend(dash_formats.values())
        
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': 'GooglePhotosVideo',
            'formats': formats,
        }
