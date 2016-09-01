# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    urlencode_postdata,
    compat_str,
    ExtractorError,
)


class CuriosityStreamBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'curiositystream'
    _auth_token = None
    _API_BASE_URL = 'https://api.curiositystream.com/v1/'

    def _handle_errors(self, result):
        error = result.get('error', {}).get('message')
        if error:
            if isinstance(error, dict):
                error = ', '.join(error.values())
            raise ExtractorError(
                '%s said: %s' % (self.IE_NAME, error), expected=True)

    def _call_api(self, path, video_id):
        headers = {}
        if self._auth_token:
            headers['X-Auth-Token'] = self._auth_token
        result = self._download_json(
            self._API_BASE_URL + path, video_id, headers=headers)
        self._handle_errors(result)
        return result['data']

    def _real_initialize(self):
        (email, password) = self._get_login_info()
        if email is None:
            return
        result = self._download_json(
            self._API_BASE_URL + 'login', None, data=urlencode_postdata({
                'email': email,
                'password': password,
            }))
        self._handle_errors(result)
        self._auth_token = result['message']['auth_token']

    def _extract_media_info(self, media):
        video_id = compat_str(media['id'])
        limelight_media_id = media['limelight_media_id']
        title = media['title']

        subtitles = {}
        for closed_caption in media.get('closed_captions', []):
            sub_url = closed_caption.get('file')
            if not sub_url:
                continue
            lang = closed_caption.get('code') or closed_caption.get('language') or 'en'
            subtitles.setdefault(lang, []).append({
                'url': sub_url,
            })

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': 'limelight:media:' + limelight_media_id,
            'title': title,
            'description': media.get('description'),
            'thumbnail': media.get('image_large') or media.get('image_medium') or media.get('image_small'),
            'duration': int_or_none(media.get('duration')),
            'tags': media.get('tags'),
            'subtitles': subtitles,
            'ie_key': 'LimelightMedia',
        }


class CuriosityStreamIE(CuriosityStreamBaseIE):
    IE_NAME = 'curiositystream'
    _VALID_URL = r'https?://app\.curiositystream\.com/video/(?P<id>\d+)'
    _TEST = {
        'url': 'https://app.curiositystream.com/video/2',
        'md5': 'a0074c190e6cddaf86900b28d3e9ee7a',
        'info_dict': {
            'id': '2',
            'ext': 'mp4',
            'title': 'How Did You Develop The Internet?',
            'description': 'Vint Cerf, Google\'s Chief Internet Evangelist, describes how he and Bob Kahn created the internet.',
            'timestamp': 1448388615,
            'upload_date': '20151124',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media = self._call_api('media/' + video_id, video_id)
        return self._extract_media_info(media)


class CuriosityStreamCollectionIE(CuriosityStreamBaseIE):
    IE_NAME = 'curiositystream:collection'
    _VALID_URL = r'https?://app\.curiositystream\.com/collection/(?P<id>\d+)'
    _TEST = {
        'url': 'https://app.curiositystream.com/collection/2',
        'info_dict': {
            'id': '2',
            'title': 'Curious Minds: The Internet',
            'description': 'How is the internet shaping our lives in the 21st Century?',
        },
        'playlist_mincount': 17,
    }

    def _real_extract(self, url):
        collection_id = self._match_id(url)
        collection = self._call_api(
            'collections/' + collection_id, collection_id)
        entries = []
        for media in collection.get('media', []):
            entries.append(self._extract_media_info(media))
        return self.playlist_result(
            entries, collection_id,
            collection.get('title'), collection.get('description'))
