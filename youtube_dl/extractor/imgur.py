# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    int_or_none,
    js_to_json,
    merge_dicts,
    mimetype2ext,
    parse_iso8601,
    T,
    traverse_obj,
    txt_or_none,
    url_or_none,
)


class ImgurBaseIE(InfoExtractor):
    # hard-coded value, as also used by ArchiveTeam
    _CLIENT_ID = '546c25a59c58ad7'

    @classmethod
    def _imgur_result(cls, item_id):
        return cls.url_result('imgur:%s' % item_id, ImgurIE.ie_key(), item_id)

    def _call_api(self, endpoint, video_id, **kwargs):
        return self._download_json(
            'https://api.imgur.com/post/v1/%s/%s?client_id=%s&include=media,account' % (endpoint, video_id, self._CLIENT_ID),
            video_id, **kwargs)

    @staticmethod
    def get_description(s):
        if 'Discover the magic of the internet at Imgur' in s:
            return None
        return txt_or_none(s)


class ImgurIE(ImgurBaseIE):
    _VALID_URL = r'''(?x)
        (?:
            https?://(?:i\.)?imgur\.com/(?!(?:a|gallery|t|topic|r)/)|
            imgur:
        )(?P<id>[a-zA-Z0-9]+)
    '''

    _TESTS = [{
        'url': 'https://imgur.com/A61SaA1',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'timestamp': 1416446068,
            'upload_date': '20141120',
        },
    }, {
        'url': 'https://i.imgur.com/A61SaA1.gifv',
        'only_matching': True,
    }, {
        'url': 'https://i.imgur.com/crGpqCV.mp4',
        'only_matching': True,
    }, {
        # previously, no title
        'url': 'https://i.imgur.com/jxBXAMC.gifv',
        'info_dict': {
            'id': 'jxBXAMC',
            'ext': 'mp4',
            'title': 'Fahaka puffer feeding',
            'timestamp': 1533835503,
            'upload_date': '20180809',
        },
    }]

    def _extract_twitter_formats(self, html, tw_id='twitter', **kwargs):
        fatal = kwargs.pop('fatal', False)
        tw_stream = self._html_search_meta('twitter:player:stream', html, fatal=fatal, **kwargs)
        if not tw_stream:
            return []
        ext = mimetype2ext(self._html_search_meta(
            'twitter:player:stream:content_type', html, default=None))
        width, height = (int_or_none(self._html_search_meta('twitter:player:' + v, html, default=None))
                         for v in ('width', 'height'))
        return [{
            'format_id': tw_id,
            'url': tw_stream,
            'ext': ext or determine_ext(tw_stream),
            'width': width,
            'height': height,
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._call_api('media', video_id, fatal=False, expected_status=404)
        webpage = self._download_webpage(
            'https://i.imgur.com/{id}.gifv'.format(id=video_id), video_id, fatal=not data) or ''

        if not traverse_obj(data, ('media', 0, (
                ('type', T(lambda t: t == 'video' or None)),
                ('metadata', 'is_animated'))), get_all=False):
            raise ExtractorError(
                '%s is not a video or animated image' % video_id,
                expected=True)

        media_fmt = traverse_obj(data, ('media', 0, {
            'url': ('url', T(url_or_none)),
            'ext': 'ext',
            'width': ('width', T(int_or_none)),
            'height': ('height', T(int_or_none)),
            'filesize': ('size', T(int_or_none)),
            'acodec': ('metadata', 'has_sound', T(lambda b: None if b else 'none')),
        }))

        media_url = traverse_obj(media_fmt, 'url')
        if media_url:
            if not media_fmt.get('ext'):
                media_fmt['ext'] = mimetype2ext(traverse_obj(
                    data, ('media', 0, 'mime_type'))) or determine_ext(media_url)
            if traverse_obj(data, ('media', 0, 'type')) == 'image':
                media_fmt['acodec'] = 'none'
                media_fmt.setdefault('preference', -10)

        tw_formats = self._extract_twitter_formats(webpage)
        if traverse_obj(tw_formats, (0, 'url')) == media_url:
            tw_formats = []
        else:
            # maybe this isn't an animated image/video?
            self._check_formats(tw_formats, video_id)

        video_elements = self._search_regex(
            r'(?s)<div class="video-elements">(.*?)</div>',
            webpage, 'video elements', default=None)
        if not (video_elements or tw_formats or media_url):
            raise ExtractorError(
                'No sources found for video %s. Maybe a plain image?' % video_id,
                expected=True)

        def mung_format(fmt, *extra):
            fmt.update({
                'http_headers': {
                    'User-Agent': 'youtube-dl (like wget)',
                },
            })
            for d in extra:
                fmt.update(d)
            return fmt

        if video_elements:
            def og_get_size(media_type):
                return dict((p, int_or_none(self._og_search_property(
                    ':'.join((media_type, p)), webpage, default=None)))
                    for p in ('width', 'height'))

            size = og_get_size('video')
            if all(v is None for v in size.values()):
                size = og_get_size('image')

            formats = traverse_obj(
                re.finditer(r'<source\s+src="(?P<src>[^"]+)"\s+type="(?P<type>[^"]+)"', video_elements),
                (Ellipsis, {
                    'format_id': ('type', T(lambda s: s.partition('/')[2])),
                    'url': ('src', T(self._proto_relative_url)),
                    'ext': ('type', T(mimetype2ext)),
                }, T(lambda f: mung_format(f, size))))

            gif_json = self._search_regex(
                r'(?s)var\s+videoItem\s*=\s*(\{.*?\})',
                webpage, 'GIF code', fatal=False)
            MUST_BRANCH = (None, T(lambda _: None))
            formats.extend(traverse_obj(gif_json, (
                T(lambda j: self._parse_json(
                    j, video_id, transform_source=js_to_json, fatal=False)), {
                        'url': ('gifUrl', T(self._proto_relative_url)),
                        'filesize': ('size', T(int_or_none)),
                }, T(lambda f: mung_format(f, size, {
                    'format_id': 'gif',
                    'preference': -10,  # gifs are worse than videos
                    'ext': 'gif',
                    'acodec': 'none',
                    'vcodec': 'gif',
                    'container': 'gif',
                })), MUST_BRANCH)))
        else:
            formats = []

        # maybe add formats from JSON or page Twitter metadata
        if not any((u == media_url) for u in traverse_obj(formats, (Ellipsis, 'url'))):
            formats.append(mung_format(media_fmt))
        tw_url = traverse_obj(tw_formats, (0, 'url'))
        if not any((u == tw_url) for u in traverse_obj(formats, (Ellipsis, 'url'))):
            formats.extend(mung_format(f) for f in tw_formats)

        self._sort_formats(formats)

        return merge_dicts(traverse_obj(data, {
            'uploader_id': ('account_id', T(txt_or_none),
                            T(lambda a: a if int_or_none(a) != 0 else None)),
            'uploader': ('account', 'username', T(txt_or_none)),
            'uploader_url': ('account', 'avatar_url', T(url_or_none)),
            'like_count': ('upvote_count', T(int_or_none)),
            'dislike_count': ('downvote_count', T(int_or_none)),
            'comment_count': ('comment_count', T(int_or_none)),
            'age_limit': ('is_mature', T(lambda x: 18 if x else None)),
            'timestamp': (('updated_at', 'created_at'), T(parse_iso8601)),
            'release_timestamp': ('created_at', T(parse_iso8601)),
        }, get_all=False), traverse_obj(data, ('media', 0, 'metadata', {
            'title': ('title', T(txt_or_none)),
            'description': ('description', T(self.get_description)),
            'duration': ('duration', T(float_or_none)),
            'timestamp': (('updated_at', 'created_at'), T(parse_iso8601)),
            'release_timestamp': ('created_at', T(parse_iso8601)),
        })), {
            'id': video_id,
            'formats': formats,
            'title': self._og_search_title(webpage, default='Imgur video ' + video_id),
            'description': self.get_description(self._og_search_description(webpage)),
            'thumbnail': url_or_none(self._html_search_meta('thumbnailUrl', webpage, default=None)),
        })


class ImgurGalleryBaseIE(ImgurBaseIE):
    _GALLERY = True

    def _real_extract(self, url):
        gallery_id = self._match_id(url)

        data = self._call_api('albums', gallery_id, fatal=False, expected_status=404)

        info = traverse_obj(data, {
            'title': ('title', T(txt_or_none)),
            'description': ('description', T(self.get_description)),
        })

        if traverse_obj(data, 'is_album'):

            def yield_media_ids():
                for m_id in traverse_obj(data, (
                        'media', lambda _, v: v.get('type') == 'video' or v['metadata']['is_animated'],
                        'id', T(txt_or_none))):
                    yield m_id

            # if a gallery with exactly one video, apply album metadata to video
            media_id = (
                self._GALLERY
                and traverse_obj(data, ('image_count', T(lambda c: c == 1)))
                and next(yield_media_ids(), None))

            if not media_id:
                result = self.playlist_result(
                    map(self._imgur_result, yield_media_ids()), gallery_id)
                result.update(info)
                return result
            gallery_id = media_id

        result = self._imgur_result(gallery_id)
        info['_type'] = 'url_transparent'
        result.update(info)
        return result


class ImgurGalleryIE(ImgurGalleryBaseIE):
    IE_NAME = 'imgur:gallery'
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/(?:gallery|(?:t(?:opic)?|r)/[^/]+)/(?P<id>[a-zA-Z0-9]+)'

    _TESTS = [{
        'url': 'http://imgur.com/gallery/Q95ko',
        'info_dict': {
            'id': 'Q95ko',
            'title': 'Adding faces make every GIF better',
        },
        'playlist_count': 25,
        'skip': 'Zoinks! You\'ve taken a wrong turn.',
    }, {
        # TODO: static images - replace with animated/video gallery
        'url': 'http://imgur.com/topic/Aww/ll5Vk',
        'only_matching': True,
    }, {
        'url': 'https://imgur.com/gallery/YcAQlkx',
        'add_ies': ['Imgur'],
        'info_dict': {
            'id': 'YcAQlkx',
            'ext': 'mp4',
            'title': 'Classic Steve Carell gif...cracks me up everytime....damn the repost downvotes....',
            'timestamp': 1358554297,
            'upload_date': '20130119',
            'uploader_id': '1648642',
            'uploader': 'wittyusernamehere',
        },
    }, {
        # TODO: static image - replace with animated/video gallery
        'url': 'http://imgur.com/topic/Funny/N8rOudd',
        'only_matching': True,
    }, {
        'url': 'http://imgur.com/r/aww/VQcQPhM',
        'add_ies': ['Imgur'],
        'info_dict': {
            'id': 'VQcQPhM',
            'ext': 'mp4',
            'title': 'The boss is here',
            'timestamp': 1476494751,
            'upload_date': '20161015',
            'uploader_id': '19138530',
            'uploader': 'thematrixcam',
        },
    },
        # from PR #16674
        {
        'url': 'https://imgur.com/t/unmuted/6lAn9VQ',
        'info_dict': {
            'id': '6lAn9VQ',
            'title': 'Penguins !',
        },
        'playlist_count': 3,
    }, {
        'url': 'https://imgur.com/t/unmuted/kx2uD3C',
        'add_ies': ['Imgur'],
        'info_dict': {
            'id': 'ZVMv45i',
            'ext': 'mp4',
            'title': 'Intruder',
            'timestamp': 1528129683,
            'upload_date': '20180604',
        },
    }, {
        'url': 'https://imgur.com/t/unmuted/wXSK0YH',
        'add_ies': ['Imgur'],
        'info_dict': {
            'id': 'JCAP4io',
            'ext': 'mp4',
            'title': 're:I got the blues$',
            'description': 'Luka’s vocal stylings.\n\nFP edit: don’t encourage me. I’ll never stop posting Luka and friends.',
            'timestamp': 1527809525,
            'upload_date': '20180531',
        },
    }]


class ImgurAlbumIE(ImgurGalleryBaseIE):
    IE_NAME = 'imgur:album'
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/a/(?P<id>[a-zA-Z0-9]+)'
    _GALLERY = False
    _TESTS = [{
        # TODO: only static images - replace with animated/video gallery
        'url': 'http://imgur.com/a/j6Orj',
        'only_matching': True,
    },
        # from PR #21693
        {
        'url': 'https://imgur.com/a/iX265HX',
        'info_dict': {
            'id': 'iX265HX',
            'title': 'enen-no-shouboutai'
        },
        'playlist_count': 2,
    }, {
        'url': 'https://imgur.com/a/8pih2Ed',
        'info_dict': {
            'id': '8pih2Ed'
        },
        'playlist_mincount': 1,
    }]
