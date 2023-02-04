# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    ExtractorError,
    GeoRestrictedError,
    get_element_by_class,
    get_element_by_id,
    int_or_none,
    merge_dicts,
    orderedSet,
    unified_timestamp,
    urlencode_postdata,
    urljoin,
)


class BitChuteBaseIE(InfoExtractor):
    _USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.57 Safari/537.36'

    def _list_entries(self, list_id):
        TOKEN = 'zyG6tQcGPE5swyAEFLqKUwMuMMuF6IO2DZ6ZDQjGfsL0e4dcTLwqkTTul05Jdve7'
        list_url = self._API_URL + list_id
        offset = 0
        query = {'showall': '1'} if 18 <= int_or_none(self._downloader.params.get('age_limit')) or 0 else None
        for page_num in itertools.count(1):
            data = self._download_json(
                list_url + '/extend/', list_id,
                'Downloading list page %d' % (page_num, ),
                data=urlencode_postdata({
                    'csrfmiddlewaretoken': TOKEN,
                    'name': '',
                    'offset': offset,
                }), headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Referer': list_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cookie': 'csrftoken=' + TOKEN,
                }, query=query)
            if data.get('success') is False:
                break
            html = data.get('html')
            if not html:
                break
            video_ids = re.findall(
                r'''class\s*=\s*["'](?:channel-videos-)?image-container[^>]+>\s*<a\b[^>]+\bhref\s*=\s*["']/video/([^"'/]+)''',
                html)
            if not video_ids:
                break
            offset += len(video_ids)
            for video_id in video_ids:
                yield self.url_result(
                    'https://www.bitchute.com/video/' + video_id,
                    ie=BitChuteIE.ie_key(), video_id=video_id)

    def _search_title(self, html, title_id, **kwargs):
        return (
            clean_html(get_element_by_id(title_id, html)) or None
            or self._og_search_title(html, default=None)
            or self._html_search_regex(r'(?s)<title\b[^>]*>.*?</title', html, 'title', **kwargs))

    def _search_description(self, html, descr_id):
        return (
            self._og_search_description(html)
            or (descr_id and clean_html(get_element_by_id(descr_id, html)))
            or self._html_search_regex(
                r'(?s)<div\b[^>]+\bclass=["\']full hidden[^>]+>(.+?)</div>',
                html, 'description', fatal=False))


class BitChuteIE(BitChuteBaseIE):
    _VALID_URL = r'https?://(?:www\.)?bitchute\.com/(?:video|embed|torrent/[^/]+)/(?P<id>[^/?#&]+)'
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
            'age_limit': None,
            'channel_url': 'https://www.bitchute.com/channel/bitchute/',
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
            'uploader': "You Can't Stop Progress",
            'age_limit': 18,
            'channel_url': 'https://www.bitchute.com/channel/ycsp/',
        },
    }, {
        'url': 'https://www.bitchute.com/embed/lbb5G1hjPhw/',
        'only_matching': True,
    }, {
        'url': 'https://www.bitchute.com/torrent/Zee5BE49045h/szoMrox2JEI.webtorrent',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        urls = re.finditer(
            r'''<(?:script|iframe)\b[^>]+\bsrc\s*=\s*("|')(?P<url>%s)''' % (BitChuteIE._VALID_URL, ),
            webpage)
        return (mobj.group('url') for mobj in urls)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        def get_error_title(html):
            return clean_html(get_element_by_class('page-title', html)) or None

        def get_error_text(html):
            return clean_html(get_element_by_id('page-detail', html)) or None

        webpage, urlh = self._download_webpage_handle(
            'https://www.bitchute.com/video/' + video_id, video_id,
            headers={
                'User-Agent': self._USER_AGENT,
            }, expected_status=404)

        if urlh.getcode() == 404:
            raise ExtractorError(get_error_title(webpage) or 'Cannot find video', expected=True)

        title = self._search_title(webpage, 'video-title')

        format_urls = [
            mobj.group('url')
            for mobj in re.finditer(
                r'''\baddWebSeed\s*\(\s*("|')(?P<url>(?:(?!\1).)+)\1''', webpage)]
        format_urls.extend(re.findall(r'''as=(https?://[^&"']+)''', webpage))

        formats = [
            {'url': format_url}
            for format_url in orderedSet(format_urls)]

        if not formats:
            entries = self._parse_html5_media_entries(
                url, webpage, video_id)
            if not entries:
                error = clean_html(get_element_by_id('video-title', webpage)) or None
                if error == 'Video Unavailable':
                    raise GeoRestrictedError(error, expected=True)
                error = get_error_title(webpage)
                if error:
                    reason = get_error_text(webpage)
                    if reason:
                        self.to_screen(reason)
                    raise ExtractorError(error, expected=True)
                raise ExtractorError('Cannot find video', )
            formats = entries[0]['formats']

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        description = (
            self._search_description(webpage, 'video-description')
            or self._html_search_regex(
                r'(?s)<div\b[^>]+\bclass=["\']full hidden[^>]+>(.+?)</div>',
                webpage, 'description', fatal=False))
        thumbnail = self._html_search_meta(
            ('og:image', 'twitter:image:src'), webpage, 'thumbnail', fatal=False)
        uploader = self._html_search_regex(
            (r'''(?s)<div\b[^>]+?\bclass\s*=\s*["']channel-banner.*?<p\b[^>]+\bclass\s*=\s*["']name\b[^>]+>(.+?)</p>''',
             r'''(?s)<p\b[^>]+\bclass\s*=\s*["']video-author\b[^>]+>(.+?)</p>'''),
            webpage, 'uploader', fatal=False)

        def more_unified_timestamp(x):
            # ... at hh:mm TZ on month nth.
            y = re.split(r'\s+at\s+', x or '')[-1]
            y = re.sub(r'(?:^\s+|\s+$|\.+$|(?<=\d)(?:st|nd|rd|th))', '', y)
            y = ' '.join(reversed(re.split(r'\s+on\s+', y, 1)))
            return unified_timestamp(y) or unified_timestamp(x)

        timestamp = more_unified_timestamp(get_element_by_class('video-publish-date', webpage))

        # TODO: remove this work-around for class matching bug
        webpage = re.split(r'''('|")channel-banner\1''', webpage, 1)[-1]
        channel_details = get_element_by_class('details', webpage)
        channel_details = channel_details and get_element_by_class('name', channel_details)
        channel_url = urljoin(url, self._search_regex(
            r'''<a\b[^>]*?\bhref\s*=\s*('|")(?P<url>(?:(?!\1).)+)''',
            channel_details or '', 'channel url', group='url', default=None))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'timestamp': timestamp,
            'formats': formats,
            'age_limit': 18 if '>This video has been marked as Not Safe For Work' in webpage else None,
            'channel_url': channel_url,
        }


class BitChuteChannelIE(BitChuteBaseIE):
    _VALID_URL = r'https?://(?:www\.)?bitchute\.com/channel/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.bitchute.com/channel/livesonnet/',
        'playlist_mincount': 135,
        'info_dict': {
            'id': 'livesonnet',
            'title': 'livesonnet_vidz',
            'description': 'md5:b0017be20656a1347eeb84f1049fc424',
        }
    }, {
        # channel with NSFW content, not listed
        'url': 'https://www.bitchute.com/channel/hQl9oMSgUyMX/',
        'playlist_maxcount': 150,
        'info_dict': {
            'id': 'hQl9oMSgUyMX',
            'title': "You Can't Stop Progress",
            'description': 'md5:a7e3fd8cf02e96ddcc73e9f13d2ce768',
        },
    }, {
        # channel with NSFW content, listed with adult age limit
        'url': 'https://www.bitchute.com/channel/hQl9oMSgUyMX/',
        'playlist_mincount': 160,
        'info_dict': {
            'id': 'hQl9oMSgUyMX',
            'title': "You Can't Stop Progress",
            'description': 'md5:a7e3fd8cf02e96ddcc73e9f13d2ce768',
        },
        'params': {
            'age_limit': 18,
        }
    }]
    _API_URL = 'https://www.bitchute.com/channel/'

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.bitchute.com/channel/' + channel_id, channel_id,
            headers={
                'User-Agent': self._USER_AGENT,
            })

        title = self._search_title(webpage, 'channel-title', default=None)

        result = self.playlist_result(
            self._list_entries(channel_id), playlist_id=channel_id, playlist_title=title)

        return merge_dicts(
            result,
            {'description': self._search_description(webpage, 'channel-description')})


class BitChutePlaylistIE(BitChuteBaseIE):
    _VALID_URL = r'https?://(?:www\.)?bitchute\.com/playlist/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.bitchute.com/playlist/g4WTfWTdYEQa/',
        'playlist_mincount': 1,
        'info_dict': {
            'id': 'g4WTfWTdYEQa',
            'title': 'Podcasts',
            'description': 'Podcast Playlist',
        },
    }]
    _API_URL = 'https://www.bitchute.com/playlist/'

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.bitchute.com/playlist/' + playlist_id, playlist_id,
            headers={
                'User-Agent': self._USER_AGENT,
            })

        title = self._search_title(webpage, 'playlist-title', default=None)

        result = self.playlist_result(
            self._list_entries(playlist_id), playlist_id=playlist_id, playlist_title=title)

        description = (
            clean_html(get_element_by_class('description', webpage))
            or self._search_description(webpage, None))

        return merge_dicts(
            result,
            {'description': description})
