# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    compat_str,
    ExtractorError,
    float_or_none,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none,
)


class TikTokBaseIE(InfoExtractor):
    def _extract_video(self, data, video_id=None):
        video = data['video']
        description = str_or_none(try_get(data, lambda x: x['desc']))
        width = int_or_none(try_get(data, lambda x: video['width']))
        height = int_or_none(try_get(data, lambda x: video['height']))

        format_urls = set()
        formats = []
        for format_id in ('download', 'play'):
            format_url = url_or_none(video.get('%sAddr' % format_id))
            if not format_url:
                continue
            if format_url in format_urls:
                continue
            format_urls.add(format_url)
            formats.append({
                'url': format_url,
                'ext': 'mp4',
                'height': height,
                'width': width,
                'http_headers': {
                    'Referer': 'https://www.tiktok.com/',
                }
            })
        self._sort_formats(formats)

        thumbnail = url_or_none(video.get('cover'))
        duration = float_or_none(video.get('duration'))

        channel = try_get(data, lambda x: x['author']['uniqueId'], compat_str)
        uploader = try_get(data, lambda x: x['author']['nickname'], compat_str)
        uploader_id = try_get(data, lambda x: x['author']['id'], compat_str)

        timestamp = int_or_none(data.get('createTime'))

        def stats(key):
            return int_or_none(try_get(
                data, lambda x: x['stats']['%sCount' % key]))

        view_count = stats('play')
        like_count = stats('digg')
        comment_count = stats('comment')
        repost_count = stats('share')

        aweme_id = data.get('id') or video_id

        track = try_get(data, lambda x: x['music']['title'])
        track_id = try_get(data, lambda x: x['music']['id'])
        artist = try_get(data, lambda x: x['music']['authorName'])
        album = try_get(data, lambda x: x['music']['album'])

        return {
            'id': aweme_id,
            'title': uploader or aweme_id,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'channel': channel,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'repost_count': repost_count,
            'track': track,
            'track_id': track_id,
            'artist': artist,
            'album': album,
            'formats': formats,
        }


class TikTokIE(TikTokBaseIE):
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/@[^/]+/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zureeal/video/6606727368545406213',
        'md5': '163ceff303bb52de60e6887fe399e6cd',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'Zureeal',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'thumbnail': r're:^https?://.*',
            'duration': 15,
            'channel': 'zureeal',
            'uploader': 'Zureeal',
            'uploader_id': '188294915489964032',
            'timestamp': 1538248586,
            'upload_date': '20180929',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
            'track': 'Joogieboy1596 FRANK SOMOHANO',
            'track_id': '6576279366609668870',
            'artist': 'JoogieBoy1596',
            'album': 'user87329004',
        }
    }]

    def _real_initialize(self):
        # Setup session (will set necessary cookies)
        self._request_webpage(
            'https://www.tiktok.com/', None, note='Setting up session')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        page_props = self._parse_json(self._search_regex(
            r'<script[^>]+\bid=["\']__NEXT_DATA__[^>]+>\s*({.+?})\s*</script',
            webpage, 'data'), video_id)['props']['pageProps']
        data = try_get(page_props, lambda x: x['itemInfo']['itemStruct'], dict)
        if not data and page_props.get('statusCode') == 10216:
            raise ExtractorError('This video is private', expected=True)
        return self._extract_video(data, video_id)


class TikTokUserIE(TikTokBaseIE):
    _VALID_URL = r'https://(?:www\.)?tiktok\.com/@(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zureeal',
        'info_dict': {
            'id': '188294915489964032',
        },
        'playlist_mincount': 24,
    }]
    _WORKING = False

    @classmethod
    def suitable(cls, url):
        return False if TikTokIE.suitable(url) else super(TikTokUserIE, cls).suitable(url)

    def _real_extract(self, url):
        user_id = self._match_id(url)
        data = self._download_json(
            'https://m.tiktok.com/h5/share/usr/list/%s/' % user_id, user_id,
            query={'_signature': '_'})
        entries = []
        for aweme in data['aweme_list']:
            try:
                entry = self._extract_video(aweme)
            except ExtractorError:
                continue
            entry['extractor_key'] = TikTokIE.ie_key()
            entries.append(entry)
        return self.playlist_result(entries, user_id)
