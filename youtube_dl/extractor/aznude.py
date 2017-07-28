# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import urljoin

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import re


class AZNudeIE(InfoExtractor):
    IE_NAME = 'aznude'
    _VALID_URL = r'https?://(?:www\.)?aznude\.com/(?:mrskin|azncdn)/[^/?]+/[^/?]+/(?P<id>.*)\.html'
    _TEST = {
        'url': 'https://www.aznude.com/mrskin/marisatomei/loiteringwithintent/loiteringwithintent-mcnallytomei-hd-01-hd.html',
        'md5': '28973bf7b818edfe55677b67bc073e40',
        'info_dict': {
            'id': 'loiteringwithintent-mcnallytomei-hd-01-hd',
            'ext': 'mp4',
            'title': 'Marisa Tomei in Loitering With Intent - 01',
            'thumbnail': 'https://cdn1.aznude.com/marisatomei/loiteringwithintent/LoiteringWithIntent-McNallyTomei-HD-01-gigantic-4.jpg',
            'description': 'Watch Marisa Tomei\'s Breasts scene on AZNude for free (22 seconds).',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        numeric_id = '-'.join(re.findall(r'(?P<num>(?:s\d+e\d+)|(?:\d+[xX]\d+)|(?:\d+))', video_id))
        webpage = self._download_webpage(url, video_id)

        jwplayer_data = self._find_jwplayer_data(webpage)
        parsed_formats = self._parse_jwplayer_data(jwplayer_data, video_id, require_title=False)['formats']

        for format in parsed_formats:
            url = format['url']

            if url.endswith('-lo.' + format['ext']):
                format['format'] = 'Low Quality'
                format['format_id'] = 'LQ'
                format['quality'] = 1
                format['width'] = 640
                format['height'] = 360
                format['format_note'] = '360p video with mono audio'

            elif url.endswith('-hi.' + format['ext']):
                format['format'] = 'High Quality'
                format['format_id'] = 'HQ'
                format['quality'] = 2
                format['width'] = 640
                format['height'] = 360
                format['format_note'] = '360p video with stereo audio'

            elif url.endswith('-hd.' + format['ext']):
                format['format'] = 'High Definition'
                format['format_id'] = 'HD'
                format['quality'] = 3
                format['width'] = 1280
                format['height'] = 720
                format['format_note'] = '720p video with stereo audio'
            else:
                # Unknown format!
                parsed_formats.remove(format)


        artist = self._html_search_regex(r'(?P<artist><span><a href="/view/celeb/[^/?]/[^/?]+\.html">[^<]+</a></span>)',
                                    webpage,
                                    url,
                                    default=None)
        work = self._html_search_regex(r'in (?P<work><a href="/view/movie/[^/?]/[^/?]+\.html">[^<]+</a>)',
                                  webpage,
                                  url,
                                  default=None)

        if (artist is not None) and (work is not None):
            title = artist + ' in ' + work
        else:
            title = self._og_search_title(webpage)

        if numeric_id != "":
            title = title + ' - ' + numeric_id

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': parsed_formats
        }


class AZNudeCollectionIE(InfoExtractor):
    IE_NAME = 'aznude:collection'
    _VALID_URL = r'https?://(?:www\.)?aznude\.com/(?:view/[^/]+/[^/]+|browse/(?:videos|tags/vids))/(?P<id>.+)\.html'
    _TESTS = [ {
        'url': 'http://www.aznude.com/view/celeb/m/marisatomei.html',
        'info_dict': {
            'title': 'Marisa Tomei Nude - Aznude ',
            'id': 'view/celeb/m/marisatomei.html',
        },
        'playlist_mincount': 33,
    }, {
        'url': 'https://www.aznude.com/view/movie/l/loiteringwithintent.html',
        'info_dict': {
            'title': 'Loitering With Intent Nude Scenes - Aznude',
            'id': 'view/movie/l/loiteringwithintent.html',
        },
        'playlist_mincount': 2,
    } ]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        title = self._search_regex(r'(?:<title>)(?P<thetitle>.+)(?:</title>)', webpage, 'title', default=None).title()

        parse_result = urlparse(url)
        url_prefix = parse_result.scheme + '://' + parse_result.netloc

        entries = []
        for path in re.findall(r'(?:<a[^>]+href=")(?P<url>[^"]+)(?:"[^>]+class="(?:[^"]+ )?show-clip(?:"| [^"]+")[^>]*>)', webpage):
            if not path.startswith("//"):
                entries.append( self.url_result(urljoin(url_prefix, path), AZNudeIE.ie_key()) )

        return self.playlist_result(entries, page_id, title)
