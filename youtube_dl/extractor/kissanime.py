# coding: utf-8
from __future__ import unicode_literals

import base64
import re

from .youtube import YoutubeIE
from .common import InfoExtractor
from ..compat import compat_parse_qs
from ..utils import unescapeHTML

class KissAnimeIE(InfoExtractor):
    _VALID_URL_TEMPLATE = r'https?://(?:www\.)?%(host)s/%(type)s/(?P<id>[^/]+/[^/?#]+)'

    IE_NAME = 'kissanime'
    IE_HOST = 'kissanime.com'
    IE_TYPE = 'Anime'
    TXHA_BASE64_ENCODED = True
    _VALID_URL = _VALID_URL_TEMPLATE % {'host': re.escape(IE_HOST), 'type': re.escape(IE_TYPE)}

    _TESTS = [{
        'url': 'http://kissanime.com/Anime/Great-Teacher-Onizuka-Sub/Episode-001?id=57217',
        'md5': 'c29a73647b075a0dc075485abc197c0b',
        'info_dict': {
            'id': 'Great-Teacher-Onizuka-Sub/Episode-001',
            'ext': 'mp4',
            'title': 'Great Teacher Onizuka (Sub) Episode 001',
            'description': 'Watch Great Teacher Onizuka (Sub) Episode 001 online in high quality',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20131105',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage('http://%(host)s/%(type)s/%(id)s' % {
                'host': self.IE_HOST, 'type': self.IE_TYPE, 'id': video_id
            }, video_id)

        # get metadata
        metadata = {}
        for metatype in ["name", "description", "thumbnailUrl", "uploadDate"]:
            r = r'<meta itemprop="%s" content="([^"]*)"/>' % (metatype)
            metadata[metatype] = self._html_search_regex(r, webpage, metatype)

        # parse date format YYYY-M-D
        upload_date_parts = metadata['uploadDate'].split('-')
        assert len(upload_date_parts) == 3
        for i, x in enumerate([4, 2, 2]):
            assert(len(upload_date_parts[i]) <= x)
            upload_date_parts[i] = upload_date_parts[i].zfill(x)
        upload_date = ''.join(upload_date_parts)

        # get flashvars
        if self.TXHA_BASE64_ENCODED:
            txha_b64 = self._search_regex(r"var txha = '([A-Za-z0-9+/]+={0,2})';", webpage, 'txha (base64)')
            txha = base64.b64decode(txha_b64).decode('ascii')
        else:
            txha = self._search_regex(r"var txha = '([^']+)';", webpage, 'txha')

        flashvars_str = unescapeHTML(txha)
        flashvars = compat_parse_qs(flashvars_str)

        # get fmt info
        fmt_list = [tuple(fmt.split('/')) for fmt in flashvars['fmt_list'][0].split(',')]
        fmt_stream_map = dict([fmt.split('|') for fmt in flashvars['fmt_stream_map'][0].split(',')])

        formats = []

        for (fmt, fmt_res) in fmt_list:
            width, height = [int(x) for x in fmt_res.split('x')]
            formats.append({
                'url': fmt_stream_map[fmt],
                'ext': YoutubeIE._formats[fmt]['ext'],
                'format_id': fmt,
                'width': width,
                'height': height,
                'resolution': fmt_res
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': metadata['name'],
            'formats': formats,
            'description': metadata['description'],
            'thumbnail': metadata['thumbnailUrl'],
            'upload_date': upload_date
        }


class KissAnimePlaylistIE(InfoExtractor):
    _VALID_URL_TEMPLATE = r'https?://(?:www\.)?%(host)s/%(type)s/(?P<id>[^/?#]+)/?(?:[\?#].*)?$'

    IE_NAME = 'kissanime:playlist'
    IE_HOST = 'kissanime.com'
    IE_TYPE = 'Anime'
    _VALID_URL = _VALID_URL_TEMPLATE % {'host': re.escape(IE_HOST), 'type': re.escape(IE_TYPE)}

    _TESTS = [{
        'url': 'http://kissanime.com/Anime/Fairy-Tail',
        'info_dict': {
            'id': 'Fairy-Tail',
            'title': 'Fairy Tail (Sub)',
            'description': "re:Set in an.*Guild's master\.\xa0\n\nLucy Heartfilia.*Fairy Tail\.\xa0\n\nOne day,.*Fairy Tail\.",
        },
        'playlist_count': 175,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage('http://%(host)s/%(type)s/%(id)s' % {
                'host': self.IE_HOST, 'type': self.IE_TYPE, 'id': playlist_id
            }, playlist_id)

        # get metadata
        name = self._search_regex(r'<a Class="bigChar" href="[^"]*">([^<]*)</a>',
                                  webpage, 'name')
        desc = self._html_search_regex(r'<span class="info">Summary:</span>\n(.*)',
                                       webpage, 'desc', fatal=False)

        # get entries
        entries = []

        for m in re.finditer(r"""<tr>\n
                                 <td>\n
                                 <a\ href="/%(type)s/(?P<id>[^"]*)"\ title="(?P<desc>[^"]*)">\n
                                 (?P<name>[^<]*)</a>\n
                                 </td>\n
                                 <td>\n
                                 (?P<date>[0-9/]+)\n
                                 </td>\n
                                 </tr>\n""" % {'type': re.escape(self.IE_TYPE)},
                            webpage, re.VERBOSE):

            # parse date format M/D/YYYY
            # note that this date format is different to the meta tag in the
            # video page which KissAnimeIE parses
            upload_date_parts = m.group('date').split('/')
            assert len(upload_date_parts) == 3
            canon_date_parts = [None for i in range(3)]
            Y,M,D = enumerate([4,2,2])
            for date_part, (i, x) in zip(upload_date_parts, [M,D,Y]):
                assert(len(date_part) <= x)
                canon_date_parts[i] = date_part.zfill(x)
            canon_upload_date = ''.join(canon_date_parts)

            entries.append({
                '_type': 'url',
                'ie_key': 'Kiss%s' % self.IE_TYPE,
                'url': "http://%s/%s/%s" % (self.IE_HOST, self.IE_TYPE, m.group('id')),
                'description': m.group('desc'),
                'title': m.group('name'),
                'date': canon_upload_date,
            })

        # sort into chronological order
        entries.reverse()

        playlist_info = {
            '_type': 'playlist',
            'id': playlist_id,
            'title': name,
            'entries': entries,
        }
        if desc is not None:
            playlist_info['description'] = desc
        return playlist_info

class KissCartoonIE(KissAnimeIE):
    IE_NAME = 'kisscartoon'
    IE_HOST = 'kisscartoon.me'
    IE_TYPE = 'Cartoon'
    TXHA_BASE64_ENCODED = False
    _VALID_URL = KissAnimeIE._VALID_URL_TEMPLATE % {'host': re.escape(IE_HOST), 'type': re.escape(IE_TYPE)}

    _TESTS = [{
        'url': 'http://kisscartoon.me/Cartoon/Adventure-Time-with-Finn-Jake-Season-01/Episode-001?id=4063',
        'md5': '8585377f24b2761db1231d34db5ac1fe',
        'info_dict': {
            'id': 'Adventure-Time-with-Finn-Jake-Season-01/Episode-001',
            'ext': 'mp4',
            'title': 'Adventure Time with Finn & Jake Season 01 Episode 001',
            'description': 'Watch Adventure Time with Finn & Jake Season 01 Episode 001 online in high quality',
            'thumbnail': 're:^https?://.*\.jpg$',
            'upload_date': '20141105',
        }
    }]


class KissCartoonPlaylistIE(KissAnimePlaylistIE):
    _VALID_URL_TEMPLATE = r'https?://(?:www\.)?%(host)s/%(type)s/(?P<id>[^/]+)'

    IE_NAME = 'kisscartoon:playlist'
    IE_HOST = 'kisscartoon.me'
    IE_TYPE = 'Cartoon'
    _VALID_URL = KissAnimePlaylistIE._VALID_URL_TEMPLATE % {'host': re.escape(IE_HOST), 'type': re.escape(IE_TYPE)}

    _TESTS = [{
        'url': 'http://kisscartoon.me/Cartoon/Archer-Season-02',
        'info_dict': {
            'id': 'Archer-Season-02',
            'title': 'Archer Season 02',
            'description': "re:At ISIS.*royally screw each other\.",
        },
        'playlist_count': 13,
    }]
