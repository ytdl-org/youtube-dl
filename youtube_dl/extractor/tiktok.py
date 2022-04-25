# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE
from ..compat import (
    compat_kwargs,
)
from ..utils import (
    dict_get,
    ExtractorError,
    float_or_none,
    get_element_by_id,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none,
)


# decorator enforces UA that TT doesn't block
def vanilla_UA_request(func):

    vanilla_UA = 'Mozilla/5.0'

    def wrapped(*args, **kwargs):
        headers = kwargs.get('headers', {})
        if 'User-Agent' not in headers:
            headers['User-Agent'] = vanilla_UA
            kwargs.update({'headers': headers, })
            kwargs = compat_kwargs(kwargs)
        return func(*args, **kwargs)

    return wrapped


class TikTokBaseIE(InfoExtractor):
    IE_DESC = 'Abstract base for TikTok extractors'
    IE_NAME = 'tiktok:base'

    @vanilla_UA_request
    def _request_webpage(self, *args, **kwargs):
        return super(TikTokBaseIE, self)._request_webpage(*args, **kwargs)

    def _get_SIGI_STATE(self, video_id, html):
        state = self._parse_json(
            get_element_by_id('SIGI_STATE', html)
            or self._search_regex(
                r'''(?s)<script\s[^>]*?\bid\s*=\s*(?P<q>"|'|\b)sigi-persisted-data(?P=q)[^>]*>[^=]*=\s*(?P<json>{.+?})\s*(?:;[^<]+)?</script''',
                html, 'sigi data', default='{}', group='json'), video_id)
        return state if isinstance(state, dict) else {}

    def _extract_video(self, data, video_id=None):
        video = try_get(data, lambda x: x['video'], dict)
        if not video:
            return
        width = int_or_none(video.get('width'))
        height = int_or_none(video.get('height'))

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

        author = data.get('author')
        if isinstance(author, dict):
            uploader_id = author.get('id')
        else:
            uploader_id = data.get('authorId')
            author = data
        uploader = str_or_none(author.get('nickname'))

        timestamp = int_or_none(data.get('createTime'))

        stats = try_get(data, lambda x: x['stats'], dict)
        view_count, like_count, comment_count, repost_count = [
            stats and int_or_none(stats.get('%sCount' % key))
            for key in ('play', 'digg', 'comment', 'share', )]

        aweme_id = data.get('id') or video_id

        return {
            'id': aweme_id,
            'display_id': video_id,
            'title': uploader or aweme_id,
            'description': str_or_none(data.get('desc')),
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': str_or_none(uploader_id),
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'repost_count': repost_count,
            'formats': formats,
        }


class TikTokIE(TikTokBaseIE):
    IE_DESC = 'TikTok video extractor'
    IE_NAME = 'tiktok'
    _VALID_URL = r'(?:https?://(?:(?:www|m)\.)?tiktok\.com/@[^/]+/video/|tiktok:(?P<user_id>[^/?#&]+):)(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zureeal/video/6606727368545406213',
        'md5': '163ceff303bb52de60e6887fe399e6cd',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'md5:363e08ccb6c691314710429f379bffe5',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'thumbnail': r're:^https?://.*',
            'duration': 15,
            'uploader': 'md5:363e08ccb6c691314710429f379bffe5',
            'uploader_id': '188294915489964032',
            'timestamp': 1538248586,
            'upload_date': '20180929',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
        }
    }]

    def _real_initialize(self):
        # Setup session (will set necessary cookies)
        self._request_webpage(
            'https://www.tiktok.com/', None, note='Setting up session')

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url).groupdict()
        video_id = m['id']
        if 'user_id' in m:
            url = 'https://www.tiktok.com/@%(user_id)s/video/%(id)s/' % m

        webpage = self._download_webpage(url.replace('://m.', '://www.'), video_id)

        page_props = self._get_SIGI_STATE(video_id, webpage)
        if try_get(page_props, lambda x: x['ItemModule'][video_id]['video'], dict):
            data = page_props['ItemModule'][video_id]
            if data.get('privateItem'):
                raise ExtractorError('This video is private', expected=True)
            return self._extract_video(data, video_id)

        # old page format - may still be served?
        page_props = self._parse_json(
            get_element_by_id('__NEXT_DATA__', webpage),
            video_id)['props']['pageProps']
        data = try_get(page_props, lambda x: x['itemInfo']['itemStruct'], dict)
        if not data and page_props.get('statusCode') == 10216:
            raise ExtractorError('This video is private', expected=True)
        return self._extract_video(data, video_id)


class TikTokUserIE(TikTokIE):
    IE_DESC = 'TikTok user profile extractor'
    IE_NAME = 'tiktok:user'
    _VALID_URL = r'https?://(?:(?:www|m)\.)?tiktok\.com/@(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zureeal',
        'info_dict': {
            'id': '188294915489964032',
        },
        'playlist_mincount': 30,
        'expected_warnings': [
            'More videos are available',
        ],
    }]

    @classmethod
    def suitable(cls, url):
        return False if TikTokIE.suitable(url) else super(TikTokBaseIE, cls).suitable(url)

    def _real_extract(self, url):
        user_id = self._match_id(url)

        webpage = self._download_webpage(url.replace('://m.', '://www.'), user_id)

        page_props = self._get_SIGI_STATE(user_id, webpage)
        user_data = try_get(page_props, lambda x: x['UserModule']['users'], dict)
        if user_data:
            num_id = try_get(
                user_data.values(),
                lambda x: [user['id'] for user in x if user['uniqueId'] == user_id and user['id'].isdigit()][0])
            item_data = try_get(page_props, lambda x: x['ItemList']['user-post'], dict) or {}
            item_list = dict_get(item_data, ('list', 'browserList'))
            if not item_list:
                item_list = try_get(item_data, lambda x: [y['id'] for y in x['preloadList']], list)
            entries = ['tiktok:%s:%s' % (user_id, x, ) for x in item_list or []]
            if item_data.get('hasMore', False):
                self._downloader.report_warning('More videos are available but the current extractor doesn\'t know how to find them')

            result = entries and self.playlist_from_matches(entries, num_id, ie='TikTok')
            if result:
                result['display_id'] = user_id
                return result

        """
        # this no longer works 2022-01
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
        """


class TikTokVMIE(GenericIE):
    IE_DESC = 'Resolver for TikTok shortcuts'
    IE_NAME = 'tiktok:shortcut'
    _VALID_URL = r'https?://(?:vm\.tiktok\.com|m\.tiktok\.com/v)/(?P<id>[^/?#&.]+)'
    _TESTS = [{
        'url': 'https://vm.tiktok.com/ZMLesneqK/',
        'info_dict': {
            'id': '7054218882072055046',
            'ext': 'mp4',
            'title': 'EddY',
            'upload_date': '20220117',
            'description': 'Hilft bestimmt gegen nervige Anrufer! 😂 #telefon #call #prank #fail #sprecher #stimme #voice #band #ansage #sound #comedy #unterhaltung #scammer #fy',
            'timestamp': 1642438324,
            'uploader': 'EddY',
            'uploader_id': '6850021004246467590',
        },
    }]

    @vanilla_UA_request
    def _request_webpage(self, *args, **kwargs):
        return super(GenericIE, self)._request_webpage(*args, **kwargs)
