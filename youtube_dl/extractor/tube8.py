from __future__ import unicode_literals

import itertools
import re
from time import sleep

from .common import InfoExtractor
from ..utils import (
    traverse_obj,
    T,
    url_or_none,
    parse_iso8601,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    parse_qs,
    urljoin,
)


class Tube8IE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:www\.)?tube8\.com\/+porn-video+\/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.tube8.com/porn-video/189530841/',
        'md5': '532408f59e89a32027d873af6289c85a',
        'info_dict': {
            'id': '189530841',
            'ext': 'mp4',
            'title': 'Found dildo. She let it cum in her tight ass to keep the secret',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'MaryKrylova',
            'timestamp': 1718961736,
            'upload_date': '20240621',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_valid_url(url).group('id')
        webpage = self._download_webpage(url, video_id)

        playervars = self._search_json(
            r'\bplayervars\s*:', webpage, 'playervars', video_id)

        extra_info = self._search_json(
            r'application/ld\+json[\"\']?>\s?', webpage, 'extra_info', video_id)

        uploader = traverse_obj(extra_info, (
            '@graph', lambda _, v: v.get('author'), 'author'))[0]

        thumbnail = traverse_obj(extra_info, (
            '@graph', lambda _, v: v.get('thumbnail'), 'thumbnail'))[0]

        timestamp = parse_iso8601(traverse_obj(extra_info, (
            '@graph', lambda _, v: v.get('datePublished'), 'datePublished'))[0])

        # Borrowed from youporn extractor
        def get_fmt(x):
            v_url = url_or_none(x.get('videoUrl'))
            if v_url:
                x['videoUrl'] = v_url
                return (x['format'], x)

        defs_by_format = dict(traverse_obj(playervars, (
            'mediaDefinitions', lambda _, v: v.get('format'), T(get_fmt))))

        title = traverse_obj(playervars, 'video_title')
        if not thumbnail:
            thumbnail = traverse_obj(playervars, 'image_url')

        # Borrowed from youporn extractor
        def get_format_data(f):
            if f not in defs_by_format:
                return []
            return self._download_json(
                defs_by_format[f]['videoUrl'], video_id, '{0}-formats'.format(f))

        formats = []
        for mp4_url in traverse_obj(
                get_format_data('mp4'),
                (lambda _, v: not isinstance(v['defaultQuality'], bool), 'videoUrl'),
                (Ellipsis, 'videoUrl')):
            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+', mp4_url)
            if mobj:
                height = int(mobj.group('height'))
                tbr = int(mobj.group('bitrate'))
                formats.append({
                    'format_id': '%dp-%dk' % (height, tbr),
                    'url': mp4_url,
                    'ext': 'mp4',
                    'tbr': tbr,
                    'height': height,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'uploader': uploader,
            'timestamp': timestamp,
        }


# Currently only user channels
class Tube8ListIE(InfoExtractor):
    _PLAYLIST_TITLEBAR_RE = r'\s+[Vv]ideos\s*$'
    _PAGE_RETRY_COUNT = 0  # ie, no retry
    _PAGE_RETRY_DELAY = 2  # seconds

    _VALID_URL = r'https?:\/\/(?:www\.)?tube8\.com\.?\/+user-videos\/+(?P<id>\d+)\/+(?P<author>[^\/]+)\/?.*'
    _TESTS = [{
        'url': 'https://www.tube8.com/user-videos/195075441/MaryKrylova/',
        'info_dict': {
            'id': '195075441',
        },
        'playlist_mincount': 29,
    }, {
        'url': 'https://www.tube8.com/user-videos/195048331/FoxyElf/',
        'info_dict': {
            'id': '195048331',
        },
        'playlist_mincount': 86,
    }]

    # Borrowed from youporn extractor
    @classmethod
    def _get_title_from_slug(cls, title_slug):
        return re.sub(r'[_-]', ' ', title_slug)

    # Borrowed from youporn extractor
    def _get_next_url(self, url, pl_id, html):
        return urljoin(url, self._search_regex(
            r'''<a\s[^>]*?\bhref\s*=\s*("|')(?P<url>(?:(?!\1)[^>])+)\1''',
            get_element_by_id('next', html) or '', 'next page',
            group='url', default=None))

    # Borrowed from youporn extractor
    def _entries(self, url, pl_id, html=None, page_num=None):

        # separates page sections
        PLAYLIST_SECTION_RE = (
            r'''<div\s[^>]*\bclass\s*=\s*('|")(?:[\w$-]+\s+|\s)*?title-bar(?:\s+[\w$-]+|\s)*\1[^>]*>'''
        )
        # contains video link
        VIDEO_URL_RE = r'''(?x)
            <div\s[^>]*\bdata-video-id\s*=\s*('|")\d+\1[^>]*>\s*
            (?:<div\b[\s\S]+?</div>\s*)*
            <a\s[^>]*\bhref\s*=\s*('|")(?P<url>(?:(?!\2)[^>])+)\2
        '''

        def yield_pages(url, html=html, page_num=page_num):
            fatal = not html
            for pnum in itertools.count(start=page_num or 1):
                if not html:
                    html = self._download_webpage(
                        url, pl_id, note='Downloading page %d' % pnum,
                        fatal=fatal)
                if not html:
                    break
                fatal = False
                yield (url, html, pnum)
                # explicit page: extract just that page
                if page_num is not None:
                    break
                next_url = self._get_next_url(url, pl_id, html)
                if not next_url or next_url == url:
                    break
                url, html = next_url, None

        def retry_page(msg, tries_left, page_data):
            if tries_left <= 0:
                return
            self.report_warning(msg, pl_id)
            sleep(self._PAGE_RETRY_DELAY)
            return next(
                yield_pages(page_data[0], page_num=page_data[2]), None)

        def yield_entries(html):
            for frag in re.split(PLAYLIST_SECTION_RE, html):
                if not frag:
                    continue
                t_text = get_element_by_class('title-text', frag or '')
                if not (t_text and re.search(self._PLAYLIST_TITLEBAR_RE, t_text)):
                    continue
                for m in re.finditer(VIDEO_URL_RE, frag):
                    video_url = urljoin(url, m.group('url'))
                    if video_url:
                        yield self.url_result(video_url)

        last_first_url = None
        for page_data in yield_pages(url, html=html, page_num=page_num):
            # page_data: url, html, page_num
            first_url = None
            tries_left = self._PAGE_RETRY_COUNT + 1
            while tries_left > 0:
                tries_left -= 1
                for from_ in yield_entries(page_data[1]):
                    # may get the same page twice instead of empty page
                    # or (site bug) intead of actual next page
                    if not first_url:
                        first_url = from_['url']
                        if first_url == last_first_url:
                            # sometimes (/porntags/) the site serves the previous page
                            # instead but may provide the correct page after a delay
                            page_data = retry_page(
                                'Retrying duplicate page...', tries_left, page_data)
                            if page_data:
                                first_url = None
                                break
                            continue
                    yield from_
                else:
                    if not first_url and 'no-result-paragarph1' in page_data[1]:
                        page_data = retry_page(
                            'Retrying empty page...', tries_left, page_data)
                        if page_data:
                            continue
                    else:
                        # success/failure
                        break
            # may get an infinite (?) sequence of empty pages
            if not first_url:
                break
            last_first_url = first_url

    # Borrowed from youporn extractor
    def _real_extract(self, url, html=None):
        # exceptionally, id may be None
        m_dict = self._match_valid_url(url).groupdict()
        pl_id, page_type, sort = (m_dict.get(k) for k in ('id', 'type', 'sort'))

        qs = parse_qs(url)
        for q, v in qs.items():
            if v:
                qs[q] = v[-1]
            else:
                del qs[q]

        base_id = pl_id or 'Tube8'
        title = self._get_title_from_slug(base_id)
        if page_type:
            title = '%s %s' % (page_type.capitalize(), title)
        base_id = [base_id.lower()]
        if sort is None:
            title += ' videos'
        else:
            title = '%s videos by %s' % (title, re.sub(r'[_-]', ' ', sort))
            base_id.append(sort)
        if qs:
            ps = ['%s=%s' % item for item in sorted(qs.items())]
            title += ' (%s)' % ','.join(ps)
            base_id.extend(ps)
        pl_id = '/'.join(base_id)

        return self.playlist_result(
            self._entries(url, pl_id, html=html,
                          page_num=int_or_none(qs.get('page'))),
            playlist_id=pl_id)
