# coding: utf-8
from __future__ import unicode_literals

import functools
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    extract_attributes,
    ExtractorError,
    get_element_by_class,
    get_element_by_id,
    HEADRequest,
    int_or_none,
    merge_dicts,
    OnDemandPagedList,
    orderedSet,
    parse_count,
    parse_duration,
    traverse_obj,
    unified_timestamp,
    urlencode_postdata,
    urljoin,
)


def get_elements_html_by_class(class_name, html):
    for m in re.finditer(
            r'(?P<elt><(?P<tag>[\w-]+)(?:\s[^>]+)?>)', html):
        if get_element_by_class(class_name, '%sa</%s>' % (m.group('elt'), m.group('tag'))):
            m = re.match(r'%s(?:[\s\S]*?</%s>)?' % (m.group('elt'), m.group('tag')), html[m.start():])
            yield m.group(0)


def get_element_html_by_class(class_name, html):
    return next(get_elements_html_by_class(class_name, html), None)


class BitChuteBaseIE(InfoExtractor):
    _USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.57 Safari/537.36'
    _HEADERS = {
        'User-Agent': _USER_AGENT,
        'Referer': 'https://www.bitchute.com/',
    }
    _GEO_BYPASS = False


class BitChuteIE(BitChuteBaseIE):
    _VALID_URL = r'https?://(?:(?:www|old)\.)?bitchute\.com/(?:video|embed|torrent/[^/]+)/(?P<id>[^/?#&]+)'
    _EMBED_REGEX = [r'<(?:script|iframe)[^>]+\bsrc=(["\'])(?P<url>{0})'.format(_VALID_URL)]
    _TESTS = [{
        'url': 'https://www.bitchute.com/video/UGlrF9o9b-Q/',
        'md5': '7e427d7ed7af5a75b5855705ec750e2b',
        'info_dict': {
            'id': 'UGlrF9o9b-Q',
            'ext': 'mp4',
            'title': 'This is the first video on #BitChute !',
            'timestamp': 1483425420,
            'upload_date': '20170103',
            'description': 'md5:a0337e7b1fe39e32336974af8173a034',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'BitChute',
            'uploader_url': 'https://www.bitchute.com/profile/I5NgtHZn9vPj/',
            'channel': 'BitChute',
            'channel_url': 'https://www.bitchute.com/channel/bitchute/',
            'age_limit': None,
        },
    }, {
        # test case: video with different channel and uploader
        'url': 'https://www.bitchute.com/video/Yti_j9A-UZ4/',
        'md5': 'f10e6a8e787766235946d0868703f1d0',
        'info_dict': {
            'id': 'Yti_j9A-UZ4',
            'ext': 'mp4',
            'title': 'Israel at War | Full Measure',
            'description': 'md5:38cf7bc6f42da1a877835539111c69ef',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'sharylattkisson',
            'timestamp': 1699296060,
            'upload_date': '20231106',
            'uploader_url': 'https://www.bitchute.com/profile/9K0kUWA9zmd9/',
            'channel': 'Full Measure with Sharyl Attkisson',
            'channel_url': 'https://www.bitchute.com/channel/sharylattkisson/',
        },
    }, {
        # NSFW (#24419)
        'url': 'https://www.bitchute.com/video/wrTrKp7PmFZC/',
        'md5': '4ef880ce8d24e322172d41a0cf6f8096',
        'info_dict': {
            'id': 'wrTrKp7PmFZC',
            'ext': 'mp4',
            'title': "You Can't Stop Progress | Episode 2",
            'timestamp': 1541476920,
            'upload_date': '20181106',
            'description': 'md5:f191b538a2c4d8f57540141a6bfd7eb0',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'lporiginalg',
            'channel': "You Can't Stop Progress",
            'age_limit': 18,
            'channel_url': 'https://www.bitchute.com/channel/ycsp/',
        },
    }, {
        # video not downloadable in browser, but we can recover it
        'url': 'https://www.bitchute.com/video/2s6B3nZjAk7R/',
        'md5': '05c12397d5354bf24494885b08d24ed1',
        'info_dict': {
            'id': '2s6B3nZjAk7R',
            'ext': 'mp4',
            'filesize': 71537926,
            'title': 'STYXHEXENHAMMER666 - Election Fraud, Clinton 2020, EU Armies, and Gun Control',
            'description': 'md5:228ee93bd840a24938f536aeac9cf749',
            'timestamp': 1542130260,
            'upload_date': '20181113',
            'uploader': 'BitChute',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader_url': 'https://www.bitchute.com/profile/I5NgtHZn9vPj/',
            'channel': 'BitChute',
            'channel_url': 'https://www.bitchute.com/channel/bitchute/',
        },
        'params': {'check_formats': None},
    }, {
        # restricted video
        'url': 'https://www.bitchute.com/video/WEnQU7XGcTdl/',
        'info_dict': {
            'id': 'WEnQU7XGcTdl',
            'ext': 'mp4',
            'title': 'Impartial Truth - Ein Letzter Appell an die Vernunft',
            'description': 'md5:32ebe076beaa571b253788465a69c63a',
            'timestamp': 1609918800.0,
            'upload_date': '20210106',
            'uploader': 'Freier_Mann',
        },
        'params': {'skip_download': True},
        'skip': 'Georestricted in DE',
    }, {
        'url': 'https://www.bitchute.com/embed/lbb5G1hjPhw/',
        'only_matching': True,
    }, {
        'url': 'https://www.bitchute.com/torrent/Zee5BE49045h/szoMrox2JEI.webtorrent',
        'only_matching': True,
    }, {
        'url': 'https://old.bitchute.com/video/UGlrF9o9b-Q/',
        'only_matching': True,
    }]

    @staticmethod
    def extract_urls(webpage):
        urls = re.finditer(
            r'''<(?:script|iframe)\s[^>]*\b(?<!-)src\s*=\s*["'](?P<url>%s)''' % (BitChuteIE._VALID_URL, ),
            webpage)
        return (mobj.group('url') for mobj in urls)

    def _check_format(self, video_url, video_id):
        urls = orderedSet(
            re.sub(r'(^https?://)(seed\d+)(?=\.bitchute\.com)', r'\g<1>{0}'.format(host), video_url)
            for host in (r'\g<2>', 'seed122', 'seed125', 'seed126', 'seed128',
                         'seed132', 'seed150', 'seed151', 'seed152', 'seed153',
                         'seed167', 'seed171', 'seed177', 'seed305', 'seed307',
                         'seedp29xb', 'zb10-7gsop1v78'))
        for url in urls:
            try:
                response = self._request_webpage(
                    HEADRequest(url), video_id=video_id, note='Checking {0}'.format(url), headers=self._HEADERS)
            except ExtractorError as e:
                self.to_screen('{0}: URL is invalid, skipping: {1}'.format(video_id, e.cause))
                continue
            return {
                'url': url,
                'filesize': int_or_none(response.headers.get('Content-Length')),
            }

    def _raise_if_restricted(self, webpage):
        page_title = clean_html(get_element_by_class('page-title', webpage)) or ''
        if re.match(r'(?:Channel|Video) Restricted$', page_title):
            reason = clean_html(get_element_by_id('page-detail', webpage)) or page_title
            self.raise_geo_restricted(reason)

    @staticmethod
    def _make_url(html):
        path = extract_attributes(get_element_html_by_class('spa', html) or '').get('href')
        return urljoin('https://www.bitchute.com', path)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        def get_error_title(html):
            return clean_html(get_element_by_class('page-title', html)) or None

        webpage, urlh = self._download_webpage_handle(
            'https://old.bitchute.com/video/{0}'.format(video_id), video_id,
            headers=self._HEADERS, expected_status=404)

        self._raise_if_restricted(webpage)

        if urlh.getcode() == 404:
            raise ExtractorError(get_error_title(webpage) or 'Cannot find video', expected=True)

        entries = self._parse_html5_media_entries(url, webpage, video_id)

        title = (
            clean_html(get_element_by_id('video-title', webpage))
            or self._og_search_title(webpage, default=None)
            or self._html_search_regex(r'(?s)<title(?!-)\b[^>]*>(.*?)</title', webpage, 'title'))

        formats = []
        for format_ in traverse_obj(entries, (0, 'formats', Ellipsis)):
            if self.get_param('check_formats') is not False:
                format_.update(self._check_format(format_.pop('url'), video_id) or {})
                if 'url' not in format_:
                    continue
            formats.append(format_)

        if not formats:
            self.raise_no_formats(
                'Video is unavailable. Please make sure this video is playable in the browser '
                'before reporting this issue.', expected=True, video_id=video_id)

        self._sort_formats(formats)

        details = get_element_by_class('details', webpage) or ''
        uploader_html = get_element_html_by_class('creator', details) or ''
        channel_html = get_element_html_by_class('name', details) or ''

        def more_unified_timestamp(datetime_str):
            # ... at hh:mm TZ on month nth, yyyy
            m_ts = re.search(
                r'\bat\s+(\d+:\d+)\s+([A-Z]+)\s+on\s+(\w+)\s+(\d+)(?:st|nd|rd|th)?[,\s]\s*(\d+)\s*\.*$',
                (datetime_str or '').strip())
            if m_ts:
                new_dt = ' '.join(m_ts.group(4, 3, 5, 1, 2))
                new_dt = unified_timestamp(new_dt)
                if new_dt:
                    return new_dt
            return unified_timestamp(datetime_str)

        timestamp = more_unified_timestamp(
            get_element_by_class('video-publish-date', webpage))

        return {
            'id': video_id,
            'title': title,
            'description': (
                self._og_search_description(webpage, default=None)
                or clean_html(get_element_by_class('full hidden', webpage))),
            'thumbnail': self._html_search_meta(
                ('og:image', 'twitter:image:src'), webpage, 'thumbnail',
                fatal=False),
            'uploader': clean_html(uploader_html),
            'uploader_url': self._make_url(uploader_html),
            'channel': clean_html(channel_html),
            'channel_url': self._make_url(channel_html),
            'timestamp': timestamp,
            'formats': formats,
            'age_limit': 18 if '>This video has been marked as Not Safe For Work' in webpage else None,
        }


class BitChuteChannelIE(BitChuteBaseIE):
    _VALID_URL = r'https?://(?:(?:www|old)\.)?bitchute\.com/(?P<type>channel|playlist)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.bitchute.com/channel/bitchute/',
        'info_dict': {
            'id': 'bitchute',
            'title': 'BitChute',
            'description': 'md5:2134c37d64fc3a4846787c402956adac',
        },
        'playlist': [
            {
                'md5': '7e427d7ed7af5a75b5855705ec750e2b',
                'info_dict': {
                    'id': 'UGlrF9o9b-Q',
                    'ext': 'mp4',
                    'title': 'This is the first video on #BitChute !',
                    'description': 'md5:a0337e7b1fe39e32336974af8173a034',
                    'thumbnail': r're:^https?://.*\.jpg$',
                    'uploader': 'BitChute',
                    'timestamp': 1483425420,
                    'upload_date': '20170103',
                    'uploader_url': 'https://www.bitchute.com/profile/I5NgtHZn9vPj/',
                    'channel': 'BitChute',
                    'channel_url': 'https://www.bitchute.com/channel/bitchute/',
                    'duration': 16,
                    'view_count': int,
                },
            },
        ],
        'params': {
            'skip_download': True,
            'playlist_items': '109',  # ie, -1
        },
    }, {
        'url': 'https://www.bitchute.com/playlist/wV9Imujxasw9/',
        'playlist_mincount': 20,
        'info_dict': {
            'id': 'wV9Imujxasw9',
            'title': 'Bruce MacDonald and "The Light of Darkness"',
            'description': r're:(?s)Bruce MacDonald co-wrote a book .{803} available to buy at Amazon\.$',
        },
    }, {
        'url': 'https://www.bitchute.com/playlist/g4WTfWTdYEQa/',
        'playlist_mincount': 1,
        'info_dict': {
            'id': 'g4WTfWTdYEQa',
            'title': 'Podcasts',
            'description': 'Podcast Playlist',
        },
    }, {
        'url': 'https://old.bitchute.com/playlist/wV9Imujxasw9/',
        'only_matching': True,
    }]

    _API_URL = 'https://old.bitchute.com'
    _TOKEN = 'zyG6tQcGPE5swyAEFLqKUwMuMMuF6IO2DZ6ZDQjGfsL0e4dcTLwqkTTul05Jdve7'
    PAGE_SIZE = 25
    HTML_CLASS_NAMES = {
        'channel': {
            'container': 'channel-videos-container',
            'title': 'channel-videos-title',
            'description': 'channel-videos-text',
        },
        'playlist': {
            'container': 'playlist-video',
            'title': 'title',
            'description': 'description',
        },

    }

    @classmethod
    def _make_url(cls, playlist_id, playlist_type):
        return '{0}/{1}/{2}/'.format(cls._API_URL, playlist_type, playlist_id)

    def _fetch_page(self, playlist_id, playlist_type, page_num):
        playlist_url = self._make_url(playlist_id, playlist_type)
        data = self._download_json(
            '{0}extend/'.format(playlist_url), playlist_id, 'Downloading page {0}'.format(page_num),
            data=urlencode_postdata({
                'csrfmiddlewaretoken': self._TOKEN,
                'name': '',
                'offset': page_num * self.PAGE_SIZE,
            }), headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': playlist_url,
                'X-Requested-With': 'XMLHttpRequest',
                'Cookie': 'csrftoken=%s' % (self._TOKEN,),
            })
        if not traverse_obj(data, 'success'):
            return
        classes = self.HTML_CLASS_NAMES[playlist_type]
        for video_html in get_elements_html_by_class(classes['container'], data.get('html')):
            video_id = self._search_regex(
                r'<a\s[^>]*\b(?<!-)href\s*=\s*["\']/video/([^"\'/]+)', video_html, 'video id', default=None)
            if not video_id:
                continue
            yield merge_dicts({
                '_type': 'url_transparent',
            }, self.url_result(
                'https://www.bitchute.com/video/{0}'.format(video_id),
                BitChuteIE.ie_key(), video_id), {
                'title': clean_html(get_element_by_class(classes['title'], video_html)),
                'description': clean_html(get_element_by_class(classes['description'], video_html)),
                'duration': parse_duration(get_element_by_class('video-duration', video_html)),
                'view_count': parse_count(clean_html(get_element_by_class('video-views', video_html))),
            })

    def _real_extract(self, url):
        playlist_type, playlist_id = self._match_valid_url(url).group('type', 'id')
        webpage = self._download_webpage(self._make_url(playlist_id, playlist_type), playlist_id)

        page_func = functools.partial(self._fetch_page, playlist_id, playlist_type)
        return merge_dicts(self.playlist_result(
            OnDemandPagedList(page_func, self.PAGE_SIZE), playlist_id), {
            'title': self._html_search_regex(
                r'(?s)<title\b(?<!-)[^>]*>([^<]+)</title>', webpage, 'title', default=None),
            'description': (
                clean_html(get_element_by_class('description', webpage))
                or self._html_search_meta(
                    ('description', 'og:description', 'twitter:description'), webpage, default=None)),
            'playlist_count': int_or_none(self._html_search_regex(
                r'<span>(\d+)\s+videos?</span>', webpage, 'playlist count', default=None)),
        })


__all__ = [
    'BitChuteIE',
    'BitChuteChannelIE',
]
