# coding: utf-8
from __future__ import unicode_literals

import itertools
import re
from string import capwords

from .common import InfoExtractor
from ..utils import (
    clean_html,
    date_from_str,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    join_nonempty,
    parse_duration,
    strip_or_none,
    unified_strdate,
    urljoin,
)


class HQPornerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hqporner\.com/hdporn/(?P<id>[\d]+)-'
    _TESTS = [{
        'url': 'https://hqporner.com/hdporn/110374-looking_for_a_change_of_pace.html',
        'md5': '7eb7b791a1ce8a619bde603b2dc334b5',
        'info_dict': {
            'id': '110374',
            'ext': 'mp4',
            'title': 'Looking For A Change Of Pace',
            'description': 'featuring Myra',
            'upload_date': '20230227',
            'age_limit': 18,
            'tags': list,
            'categories': list,
            'duration': 3271,
            'thumbnail': r're:https?://.*\.jpg',
        },
    }, {
        'url': 'https://hqporner.com/hdporn/86482-all_night_rager.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # some pages need a `referer` to avoid 404
        webpage = self._download_webpage(url, video_id, headers={'referer': 'https://hqporner.com/?q=porn'})

        # details below video are in a <header> element
        heading = self._search_regex(r'''(?s)(<header>.+?</section>)\s*</div>''', webpage, 'heading', default='')
        title = (
            capwords(clean_html(get_element_by_class('main-h1', heading) or ''))
            or self._html_search_regex(
                r'<title\b[^>]*>\s*([^<]+)(?:\s+-\s+HQporner\.com)?\s*</title>',
                webpage, 'title'))
        # video details are in a page loaded by this <iframe>
        player = get_element_by_id('playerWrapper', webpage)
        player = self._search_regex(
            r'''<iframe [^>]*\bsrc\s*=\s*('|")(?P<url>(?:(?!\1)\S)+)''',
            player, 'player iframe', group='url')
        player = self._download_webpage(urljoin(url, player), video_id, note='Downloading player iframe')
        # select the complete set of videos
        player = self._search_regex(
            r'''\belse\s*\{\s*\$\s*\(\s*('|")#jw\1\s*\)\s*\.\s*html\s*\(\s*(?P<vstr>("|')\s*<video [^>]+>[^)]+</video>\s*\3)''',
            player, 'video element', group='vstr')
        # it's a string containing HTML5 video
        info = self._parse_html5_media_entries(
            url, self._parse_json(player, video_id), video_id)[0]  # not used now: m3u8_id='hls', m3u8_entry_protocol='m3u8_native', mpd_id='dash')
        # site offers no timestamp, but may have "however-many date-units ago"
        upload_date = get_element_by_class('fa-calendar', heading) or ''
        if upload_date.endswith(' ago'):
            upload_date = date_from_str('now-' + upload_date[:-len(' ago')].replace(' ', '').replace('one', '1'))
            if upload_date:
                upload_date = upload_date.isoformat().replace('-', '')
        else:
            # probably ineffective
            upload_date = unified_strdate(upload_date)

        # utils candidate
        def tag_list(s, delim=','):
            return [t for t in map(strip_or_none, s.split(delim)) if t] or None

        desc = self._html_search_meta('description', webpage, default='')

        info.update({
            'id': video_id,
            'title': title,
            'age_limit': 18,
            'upload_date': upload_date,
            'description': clean_html(get_element_by_class('icon fa-star-o', heading)),
            'duration': parse_duration(
                get_element_by_class('fa-clock-o', heading)
                or self._search_regex(r'Video duration is\s+([^.]+)', desc, 'duration', default='')),
            'categories': tag_list(
                clean_html(self._search_regex(r'(?s)</h3>\s*<p>(.+?)</p>', heading, 'categories', default='').replace('</a>', ','))
                or self._html_search_meta('keywords', webpage, default='')),
            'tags': tag_list(self._search_regex(r'Tags [\w\s-]+:\s+([^.]+)', desc, 'tags', default='')),
        })
        return info


class HQPornerListBaseIE(InfoExtractor):

    # yt-dlp shim
    @classmethod
    def _match_valid_url(cls, url):
        return re.match(cls._VALID_URL, url)

    def _real_extract(self, url):
        pl_id, pg = self._match_valid_url(url).group('id', 'pg')
        pg = int_or_none(pg)

        def entries():
            """
                Generate the playlist
                If `pg` is a page number, get the list for that page
                Otherwise continue from `url` until exhausted
            """
            next = url
            for pnum in itertools.count(start=pg or 1):
                p_url = urljoin(url, next)
                first = (pg or 1) == pnum
                if not p_url and not first:
                    break
                page = self._download_webpage(
                    p_url, pl_id,
                    note='Downloading page' + ('' if first else (' %d' % pnum)),
                    fatal=first)
                if not page:
                    break
                for m in re.finditer(
                        # each entry in a playlist page has a hyperlinked <img> followed by the caption:
                        # <h3> containing a hyperlinked title, followed by a <span> containing duration
                        r'''(?sx)
                            # <img> with thumbnail (extracted), then closing containing <a><div>
                            (?:<img\b[^>]+\bsrc\s*=\s*("|')(?P<thm>(?:(?!\1).)+)\1[^>]*>.*?)?
                            # caption: extract href and title
                            <h3\b[^>]+\bclass\s*=\s*("|')(?:(?:(?!\3).)+\s)*?meta-data-title(?:\s(?:(?!\3).)+)*\3[^>]*>\s*
                                <a\b[^>]+\bhref\b=("|')(?P<url>(?:(?!\4).)+)\4[^>]*>(?P<ttl>[^<]*)</a>\s*
                            </h3>\s*
                            # extract duration
                            (?:<span\b[^>]+\bclass\s*=\s*("|')(?:(?:(?!\7).)+\s)*?fa-clock-o(?:\s(?:(?!\7).)+)*\7[^>]*>(?P<dur>[^<]+)</span>)?
                        ''', page):
                    a_url = self._proto_relative_url(urljoin(url, m.group('url')))
                    if a_url:
                        res = self.url_result(a_url, video_title=capwords(clean_html(m.group('ttl')) or '') or None)
                        res.update({
                            'duration': parse_duration(m.group('dur')),
                            'thumbnail': self._proto_relative_url(urljoin(a_url, m.group('thm'))),
                        })
                        yield res
                if pg is not None:
                    break
                # next is the last link in the pagination block, unless that's the current URL
                maybe_next = urljoin(url, self._search_regex(
                    r'''(?s)<a\b[^>]+\bhref\s*=\s*("|')(?P<url>(?:(?!\1).)+)\1[^>]*>[^>]*</a>\s*</li>\s*$''',
                    get_element_by_class('pagination', page) or '', 'next page',
                    group='url', default=None))
                next = maybe_next if maybe_next != next else None

        return self.playlist_result(entries(), playlist_id=join_nonempty(pl_id, pg, delim=':'))

    @staticmethod
    def _set_title(info):
        pl_id, _, pg = info['id'].rpartition(':')
        if not pl_id:
            pl_id = pg
            pg = None
        info['title'] = pl_id.replace('/', ': ')
        if pg:
            info['title'] += ' [%s]' % (pg, )


class HQPornerListIE(HQPornerListBaseIE):

    _VALID_URL = r'https?://(?:www\.)?hqporner\.com/(?P<id>(?:top|(?:category|actress)/[^/]+))(?:/(?P<pg>\d+))?'
    _TESTS = [{
        'url': 'https://hqporner.com/category/beach-porn',
        'info_dict': {
            'id': 'category/beach-porn',
            'title': 'Category: beach-porn',
        },
        'playlist_mincount': 250,
    }, {
        'url': 'https://hqporner.com/category/beach-porn/2',
        'info_dict': {
            'id': 'category/beach-porn:2',
            'title': 'Category: beach-porn [2]',
        },
        'playlist_count': 50,
    }, {
        'url': 'https://hqporner.com/actress/mary/1',
        'info_dict': {
            'id': 'actress/mary:1',
            'title': 'Actress: mary [1]',
        },
        'playlist_count': 50,
    },
    ]

    def _real_extract(self, url):
        res = super(HQPornerListIE, self)._real_extract(url)
        self._set_title(res)
        res['title'] = res['title'].capitalize()
        return res


class HQPornerSearchIE(HQPornerListBaseIE):

    _VALID_URL = r'https?://(?:www\.)?hqporner\.com/\?q=(?P<id>[^&]+)(?:&p=(?P<pg>\d+))?'
    _TESTS = [{
        'url': 'https://hqporner.com/?q=french',
        'info_dict': {
            'id': 'french',
            'title': 'Searching: french',
        },
        'playlist_mincount': 250,
    }, {
        'url': 'https://hqporner.com/?q=french&p=2',
        'info_dict': {
            'id': 'french:2',
            'title': 'Searching: french [2]',
        },
        'playlist_count': 50,
    },
    ]

    def _real_extract(self, url):
        res = super(HQPornerSearchIE, self)._real_extract(url)
        self._set_title(res)
        res['title'] = 'Searching: ' + res['title']
        return res
