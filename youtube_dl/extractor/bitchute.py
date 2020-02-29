# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..utils import (
    orderedSet,
    unified_strdate,
    unified_timestamp,
    urlencode_postdata,
)


class BitChuteIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bitchute\.com/(?:video|embed|torrent/[^/]+)/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.bitchute.com/video/mxzcCZI0RQ0k/',
        'md5': '94e5c980ffdb450e72a8ed55f2e9280b',
        'info_dict': {
            'id': 'mxzcCZI0RQ0k',
            'ext': 'mp4',
            'title': 'Some People are just Glitches in the Matrix',
            'description': 'md5:46cc1f8670f6da35fec011bb1d1e548e',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'stargods',
            'upload_date': '20200218',
            'timestamp': 1582066500,
        },
    }, {
        'url': 'https://www.bitchute.com/embed/lbb5G1hjPhw/',
        'only_matching': True,
    }, {
        'url': 'https://www.bitchute.com/torrent/Zee5BE49045h/szoMrox2JEI.webtorrent',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.bitchute.com/video/%s' % video_id, video_id, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.57 Safari/537.36',
            })

        title = self._html_search_regex(
            (r'<[^>]+\bid=["\']video-title[^>]+>([^<]+)', r'<title>([^<]+)'),
            webpage, 'title', default=None) or self._html_search_meta(
            'description', webpage, 'title',
            default=None) or self._og_search_description(webpage)

        format_urls = []
        for mobj in re.finditer(
                r'addWebSeed\s*\(\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage):
            format_urls.append(mobj.group('url'))
        format_urls.extend(re.findall(r'as=(https?://[^&"\']+)', webpage))

        formats = [
            {'url': format_url}
            for format_url in orderedSet(format_urls)]

        if not formats:
            formats = self._parse_html5_media_entries(
                url, webpage, video_id)[0]['formats']

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        description = self._html_search_regex(
            r'(?s)<div\b[^>]+\bclass=["\']full hidden[^>]+>(.+?)</div>',
            webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._html_search_meta(
            'twitter:image:src', webpage, 'thumbnail')
        uploader = self._html_search_regex(
            (r'(?s)<div class=["\']channel-banner.*?<p\b[^>]+\bclass=["\']name[^>]+>(.+?)</p>',
             r'(?s)<p\b[^>]+\bclass=["\']video-author[^>]+>(.+?)</p>'),
            webpage, 'uploader', fatal=False)

        upload_date = unified_strdate(self._search_regex(
            r'class=["\']video-publish-date[^>]+>[^<]+ at \d+:\d+ UTC on (.+?)\.',
            webpage, 'upload date', fatal=False))

        timestamp = unified_timestamp('-'.join([upload_date[:4], upload_date[4:6], upload_date[6:]]) + ' ' + self._search_regex(
            r'class=["\']video-publish-date[^>]+>[^<]+ (\d+:\d+ UTC) on',
            webpage, 'timestamp', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'formats': formats,
            'timestamp': timestamp,
        }


class BitChuteChannelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bitchute\.com/channel/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.bitchute.com/channel/stargods/',
        'playlist_mincount': 50,
        'info_dict': {
            'id': 'stargods',
        },
    }

    _TOKEN = 'zyG6tQcGPE5swyAEFLqKUwMuMMuF6IO2DZ6ZDQjGfsL0e4dcTLwqkTTul05Jdve7'

    def _entries(self, channel_id):
        channel_url = 'https://www.bitchute.com/channel/%s/' % channel_id
        offset = 0
        for page_num in itertools.count(1):
            data = self._download_json(
                '%sextend/' % channel_url, channel_id,
                'Downloading channel page %d' % page_num,
                data=urlencode_postdata({
                    'csrfmiddlewaretoken': self._TOKEN,
                    'name': '',
                    'offset': offset,
                }), headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'Referer': channel_url,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cookie': 'csrftoken=%s' % self._TOKEN,
                })
            if data.get('success') is False:
                break
            html = data.get('html')
            if not html:
                break
            video_ids = re.findall(
                r'class=["\']channel-videos-image-container[^>]+>\s*<a\b[^>]+\bhref=["\']/video/([^"\'/]+)',
                html)
            if not video_ids:
                break
            offset += len(video_ids)
            for video_id in video_ids:
                yield self.url_result(
                    'https://www.bitchute.com/video/%s' % video_id,
                    ie=BitChuteIE.ie_key(), video_id=video_id)

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        return self.playlist_result(
            self._entries(channel_id), playlist_id=channel_id)
