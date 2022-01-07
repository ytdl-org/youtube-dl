# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    HEADRequest,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none,
)


class TikTokBaseIE(InfoExtractor):
    def _download_webpage(
            self, url_or_request, video_id, note=None, errnote=None,
            fatal=True, tries=1, timeout=5, encoding=None, data=None,
            headers={}, query={}, expected_status=None, setup=True):

        if setup:
            url = url_or_request.geturl() if isinstance(url_or_request, compat_urllib_request.Request) else url_or_request
            # dummy request to set cookies
            self._request_webpage(
                HEADRequest(url), video_id,
                note=False, errnote='Could not send HEAD request to %s' % url,
                fatal=False, headers=headers)

        return super(TikTokBaseIE, self)._download_webpage(
            url_or_request, video_id, note=note, errnote=errnote,
            fatal=fatal, tries=tries, timeout=timeout, encoding=encoding, data=data,
            headers=headers, query=query, expected_status=expected_status)

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
    _VALID_URL = r'https?://(?:www\.)?tiktok\.com/@[^/]+/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.tiktok.com/@zureeal/video/6606727368545406213',
        'md5': '163ceff303bb52de60e6887fe399e6cd',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'md5:24acc456b62b938a7e2dd88e978b20d9',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'thumbnail': r're:^https?://.*',
            'duration': 15,
            'uploader': 'md5:24acc456b62b938a7e2dd88e978b20d9',
            'uploader_id': '188294915489964032',
            'timestamp': 1538248586,
            'upload_date': '20180929',
            'view_count': int,
            'like_count': int,
            'comment_count': int,
            'repost_count': int,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        page_props = self._parse_json(self._search_regex(
            r'''(?s)<script\s[^>]*?\bid\s*=\s*(?P<q>"|'|\b)sigi-persisted-data(?P=q)[^>]*>[^=]*=\s*(?P<json>{.+?})\s*(?:;[^<]+)?</script''',
            webpage, 'sigi data', default='{}', group='json'), video_id)
        data = try_get(page_props, lambda x: x['ItemModule'][video_id]['video'], dict)
        if data:
            data = page_props['ItemModule'][video_id]
            if data.get('privateItem'):
                raise ExtractorError('This video is private', expected=True)
            return self._extract_video(data, video_id)

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

    @classmethod
    def suitable(cls, url):
        return False if TikTokIE.suitable(url) else super(TikTokUserIE, cls).suitable(url)

    def _real_extract(self, url):
        user_id = self._match_id(url)

        webpage = self._download_webpage(url, user_id)
        page_props = self._parse_json(self._search_regex(
            r'''(?s)<script\s[^>]*?\bid\s*=\s*(?P<q>"|'|\b)sigi-persisted-data(?P=q)[^>]*>[^=]*=\s*(?P<json>{.+?})\s*(?:;[^<]+)?</script''',
            webpage, 'sigi data', default='{}', group='json'), user_id)
        user_data = try_get(page_props, lambda x: x['UserModule']['users'], dict)
        entries = []
        if user_data:
            num_id = try_get(
                user_data.values(),
                lambda x: [user['id'] for user in x if user['uniqueId'] == user_id][0],
                compat_str)
            item_data = try_get(page_props, lambda x: x['ItemModule'], dict)
            if item_data:
                item_data = item_data.values()
            for data in item_data or []:
                if data.get('privateItem'):
                    continue
                item = self._extract_video(data, user_id)
                if item:
                    entries.append(item)
            result = entries and self.playlist_result(entries, num_id)
            if not result:
                item_data = try_get(page_props, lambda x: x['ItemList']['user-post']['list'], list)
                result = self.playlist_from_matches(item_data, playlist_id=num_id, getter=lambda m: 'tiktok:%s' % (m, ))
            if result:
                result['display_id'] = user_id
                return result

        data = self._download_json(
            'https://m.tiktok.com/h5/share/usr/list/%s/' % user_id, user_id,
            query={'_signature': '_'})
        for aweme in data['aweme_list']:
            try:
                entry = self._extract_video(aweme)
            except ExtractorError:
                continue
            entry['extractor_key'] = TikTokIE.ie_key()
            entries.append(entry)

        return self.playlist_result(entries, user_id)
