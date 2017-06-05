# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_chr
from ..utils import (
    determine_ext,
    ExtractorError,
)

class VeyqoIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?veyqo\.net\/(?P<id>[a-zA-Z0-9-_]+)'
    _TEST = {
        'url': 'http://www.veyqo.net/rkprime-aidra-fox-get-closet-24-12-2016/',
        'md5': '308b079d7e7314e5d23a459bb95b67ee',
        'info_dict': {
            'id': 'rkprime-aidra-fox-get-closet-24-12-2016',
            'ext': 'unknown_video',
            'title': 'RKPrime - Aidra Fox (Get In The Closet) (24.12.2016)',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
      
        ol_link = self._search_regex('https?://(?:openload\.(?:co|io)|oload\.tv)/(?:f|embed)/(?P<id>[a-zA-Z0-9-_]+)',webpage, 'openload link')
        webpage = self._download_webpage('https://openload.co/embed/%s/' % ol_link, video_id)

        if 'File not found' in webpage or 'deleted by the owner' in webpage:
            raise ExtractorError('File not found', expected=True)

        ol_id = self._search_regex(
            '<span[^>]+id="[a-zA-Z0-9]+x"[^>]*>([0-9]+)</span>',
            webpage, 'openload ID')
        first_two_chars = int(float(ol_id[0:][:2]))
        urlcode = ''
        num = 2

        while num < len(ol_id):
            urlcode += compat_chr(int(float(ol_id[num:][:3])) - first_two_chars * int(float(ol_id[num + 3:][:2])))
            num += 5

        video_url = 'https://openload.co/stream/' + urlcode

        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'<span[^>]+class=["\']title["\'][^>]*>([^<]+)', webpage,
            'title', default=None) or self._html_search_meta(
            'description', webpage, 'title', fatal=True)

        entries = self._parse_html5_media_entries(url, webpage, video_id)
        subtitles = entries[0]['subtitles'] if entries else None
        print video_id
        print title
        print determine_ext(title)
        print self._og_search_thumbnail(webpage, default=None)
        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
            # Seems all videos have extensions in their titles
            'ext': determine_ext(title),
            'subtitles': subtitles,
               }
