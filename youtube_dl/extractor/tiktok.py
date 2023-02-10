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
        def get_replies_of_tiktok_comment(self, aweme_id, comment_id):
                reply_json = self._download_json(
                    f'https://api-h2.tiktokv.com/aweme/v1/comment/list/reply/?comment_id={comment_id}&item_id={aweme_id}&cursor=0&count=20&insert_ids=&top_ids=&channel_id=0', 
                    data=b'', fatal=False, note='Checking if comment has any replies...') or {} 
                has_more = traverse_obj(reply_json, ('has_more'))
                commentsnum = len(reply_json['comments'])

                for i in range(has_more) and commentsnum != 0:
                    if i == 0:
                        comment_data = reply_json
                        note='Comment downloading completed!'
                    else:
                        comment_data = self._download_json(
                            f'https://api-h2.tiktokv.com/aweme/v1/comment/list/reply/?comment_id={comment_id}&item_id={aweme_id}&count=50&insert_ids=&top_ids=&channel_id=0', 
                            data=b'', fatal=False, query={'cursor': i + 50}, note='Downloading replies...') or {}
                    for comment in comment_data['comments']:
                        yield {
                            'id': comment.get('cid'), # comment ID
                            'alt_id': comment.get('aweme_id'), # "aweme" id, seems to be tiktok's universal id, we might swap them
                            'text': comment.get('text'),
                            'like_count': comment.get('digg_count'),
                            'timestamp': comment.get('create_time'),
                            'is_pinned': comment.get('author_pin'), # booleen
                            'is_hidden': comment.get('no_show'), # booleen
                            'lang': comment.get('comment_language'), # 2 letter language code: en, jp, fr, etc. shortened to lang as its more common and saves disk space
                            'text_extra': comment.get('text_extra'), # includes hashtags, most likely same format as in video metadata
                            'reply_count': comment.get('reply_comment_total'), 
                            'author_id': comment['user']['uid'], # user id (possibly aweme id)
                            'author': comment['user']['nickname'], # user nickname
                            'author_label': comment.get('label_text'), 
                            'author_handle': comment['user']['unique_id'], # user handle, @ultimatemariofan101 for example without the at symbol
                            'author_thumbnail': comment['user']['avatar_larger']['url_list'][0], 
                            'author_full_info': comment.get('user'),
                        }

    def _get_comments(self, aweme_id):
                # references: https://gist.github.com/theblazehen/25c18eda95165e65fc5159942fb5e4db (uses v1 api), https://github.com/yt-dlp/yt-dlp/issues/5037 (new api documentation)
                comment_json = self._download_json(
                    f'https://api-h2.tiktokv.com/aweme/v2/comment/list/?aweme_id={aweme_id}&cursor=0&count=50&forward_page_type=1', 
                    data=b'', fatal=False, note='Checking if video has any comments...') or {} 
                has_more = traverse_obj(comment_json, ('has_more'))
                commentsnum = len(comment_json['comments'])

                for i in range(has_more) and commentsnum != 0:
                    if i == 0:
                        comment_data = comment_json
                        note='Comment downloading completed!'
                    else:
                        comment_data = self._download_json(
                            f'https://api-h2.tiktokv.com/aweme/v2/comment/list/?aweme_id={aweme_id}&count=50&forward_page_type=1', 
                            data=b'', fatal=False, query={'cursor': i + 50}, note='Downloading a page of comments') or {}
                    for comment in comment_data['comments']:
                        yield {
                            'id': comment.get('cid'), # comment ID
                            'alt_id': comment.get('aweme_id'), # "aweme" id, seems to be tiktok's universal id, we might swap them
                            'text': comment.get('text'),
                            'like_count': comment.get('digg_count'),
                            'timestamp': comment.get('create_time'),
                            'is_pinned': comment.get('author_pin'), # booleen
                            'is_hidden': comment.get('no_show'), # booleen
                            'lang': comment.get('comment_language'), # 2 letter language code: en, jp, fr, etc
                            'text_extra': comment.get('text_extra'), # includes hashtags, most likely same format as in video metadata
                            'reply_count': comment.get('reply_comment_total'), 
                            'parent': comment.get('reply_id'), # parent comment if
                            'parent_reply': comment.get('reply_to_reply_id'), # exclusive to replies to replies
                            'author_id': comment['user']['uid'], # user id (possibly aweme id)
                            'author': comment['user']['nickname'], # user nickname
                            'author_label': comment.get('label_text'),
                            'author_handle': comment['user']['unique_id'], # user handle, @ultimatemariofan101 for example without the at symbol
                            'author_thumbnail': comment['user']['avatar_larger']['url_list'][0], 
                            'author_full_info': comment.get('user'),
                        }
                        if self._configuration_arg('no_tiktok_replies') is None:
                            for comment in traverse_obj(comments):
                                if comment.get('reply_comment_total') > 0:
                                    get_replies_of_tiktok_comment(self, aweme_id, i)
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

        return {
            'id': aweme_id,
            'title': uploader or aweme_id,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
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
            'title': 'Zureeal',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'thumbnail': r're:^https?://.*',
            'duration': 15,
            'uploader': 'Zureeal',
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
