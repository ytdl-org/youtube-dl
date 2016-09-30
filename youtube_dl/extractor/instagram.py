from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    get_element_by_attribute,
    int_or_none,
    limit_length,
    lowercase_escape,
    try_get,
)


class InstagramIE(InfoExtractor):
    _VALID_URL = r'(?P<url>https?://(?:www\.)?instagram\.com/p/(?P<id>[^/?#&]+))'
    _TESTS = [{
        'url': 'https://instagram.com/p/aye83DjauH/?foo=bar#abc',
        'md5': '0d2da106a9d2631273e192b372806516',
        'info_dict': {
            'id': 'aye83DjauH',
            'ext': 'mp4',
            'title': 'Video by naomipq',
            'description': 'md5:1f17f0ab29bd6fe2bfad705f58de3cb8',
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1371748545,
            'upload_date': '20130620',
            'uploader_id': 'naomipq',
            'uploader': 'Naomi Leonor Phan-Quang',
            'like_count': int,
            'comment_count': int,
            'comments': list,
        },
    }, {
        # missing description
        'url': 'https://www.instagram.com/p/BA-pQFBG8HZ/?taken-by=britneyspears',
        'info_dict': {
            'id': 'BA-pQFBG8HZ',
            'ext': 'mp4',
            'title': 'Video by britneyspears',
            'thumbnail': 're:^https?://.*\.jpg',
            'timestamp': 1453760977,
            'upload_date': '20160125',
            'uploader_id': 'britneyspears',
            'uploader': 'Britney Spears',
            'like_count': int,
            'comment_count': int,
            'comments': list,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://instagram.com/p/-Cmh1cukG2/',
        'only_matching': True,
    }, {
        'url': 'http://instagram.com/p/9o6LshA7zy/embed/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_embed_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?instagram\.com/p/[^/]+/embed.*?)\1',
            webpage)
        if mobj:
            return mobj.group('url')

        blockquote_el = get_element_by_attribute(
            'class', 'instagram-media', webpage)
        if blockquote_el is None:
            return

        mobj = re.search(
            r'<a[^>]+href=([\'"])(?P<link>[^\'"]+)\1', blockquote_el)
        if mobj:
            return mobj.group('link')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = mobj.group('url')

        webpage = self._download_webpage(url, video_id)

        (video_url, description, thumbnail, timestamp, uploader,
         uploader_id, like_count, comment_count, height, width) = [None] * 10

        shared_data = self._parse_json(
            self._search_regex(
                r'window\._sharedData\s*=\s*({.+?});',
                webpage, 'shared data', default='{}'),
            video_id, fatal=False)
        if shared_data:
            media = try_get(
                shared_data, lambda x: x['entry_data']['PostPage'][0]['media'], dict)
            if media:
                video_url = media.get('video_url')
                height = int_or_none(media.get('dimensions', {}).get('height'))
                width = int_or_none(media.get('dimensions', {}).get('width'))
                description = media.get('caption')
                thumbnail = media.get('display_src')
                timestamp = int_or_none(media.get('date'))
                uploader = media.get('owner', {}).get('full_name')
                uploader_id = media.get('owner', {}).get('username')
                like_count = int_or_none(media.get('likes', {}).get('count'))
                comment_count = int_or_none(media.get('comments', {}).get('count'))
                comments = [{
                    'author': comment.get('user', {}).get('username'),
                    'author_id': comment.get('user', {}).get('id'),
                    'id': comment.get('id'),
                    'text': comment.get('text'),
                    'timestamp': int_or_none(comment.get('created_at')),
                } for comment in media.get(
                    'comments', {}).get('nodes', []) if comment.get('text')]

        if not video_url:
            video_url = self._og_search_video_url(webpage, secure=False)

        formats = [{
            'url': video_url,
            'width': width,
            'height': height,
        }]

        if not uploader_id:
            uploader_id = self._search_regex(
                r'"owner"\s*:\s*{\s*"username"\s*:\s*"(.+?)"',
                webpage, 'uploader id', fatal=False)

        if not description:
            description = self._search_regex(
                r'"caption"\s*:\s*"(.+?)"', webpage, 'description', default=None)
            if description is not None:
                description = lowercase_escape(description)

        if not thumbnail:
            thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'formats': formats,
            'ext': 'mp4',
            'title': 'Video by %s' % uploader_id,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'uploader': uploader,
            'like_count': like_count,
            'comment_count': comment_count,
            'comments': comments,
        }


class InstagramUserIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/(?P<username>[^/]{2,})/?(?:$|[?#])'
    IE_DESC = 'Instagram user profile'
    IE_NAME = 'instagram:user'
    _TEST = {
        'url': 'https://instagram.com/porsche',
        'info_dict': {
            'id': 'porsche',
            'title': 'porsche',
        },
        'playlist_mincount': 2,
        'playlist': [{
            'info_dict': {
                'id': '614605558512799803_462752227',
                'ext': 'mp4',
                'title': '#Porsche Intelligent Performance.',
                'thumbnail': 're:^https?://.*\.jpg',
                'uploader': 'Porsche',
                'uploader_id': 'porsche',
                'timestamp': 1387486713,
                'upload_date': '20131219',
            },
        }],
        'params': {
            'extract_flat': True,
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader_id = mobj.group('username')

        entries = []
        page_count = 0
        media_url = 'http://instagram.com/%s/media' % uploader_id
        while True:
            page = self._download_json(
                media_url, uploader_id,
                note='Downloading page %d ' % (page_count + 1),
            )
            page_count += 1

            for it in page['items']:
                if it.get('type') != 'video':
                    continue
                like_count = int_or_none(it.get('likes', {}).get('count'))
                user = it.get('user', {})

                formats = [{
                    'format_id': k,
                    'height': v.get('height'),
                    'width': v.get('width'),
                    'url': v['url'],
                } for k, v in it['videos'].items()]
                self._sort_formats(formats)

                thumbnails_el = it.get('images', {})
                thumbnail = thumbnails_el.get('thumbnail', {}).get('url')

                # In some cases caption is null, which corresponds to None
                # in python. As a result, it.get('caption', {}) gives None
                title = (it.get('caption') or {}).get('text', it['id'])

                entries.append({
                    'id': it['id'],
                    'title': limit_length(title, 80),
                    'formats': formats,
                    'thumbnail': thumbnail,
                    'webpage_url': it.get('link'),
                    'uploader': user.get('full_name'),
                    'uploader_id': user.get('username'),
                    'like_count': like_count,
                    'timestamp': int_or_none(it.get('created_time')),
                })

            if not page['items']:
                break
            max_id = page['items'][-1]['id'].split('_')[0]
            media_url = (
                'http://instagram.com/%s/media?max_id=%s' % (
                    uploader_id, max_id))

        return {
            '_type': 'playlist',
            'entries': entries,
            'id': uploader_id,
            'title': uploader_id,
        }
