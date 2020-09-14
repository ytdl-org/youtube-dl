# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_kwargs,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_iso8601,
    urljoin,
)


class WASDTVBaseIE(InfoExtractor):
    _API_BASE = 'https://wasd.tv/api/'
    _THUMBNAIL_SIZES = ('small', 'medium', 'large')

    def _fetch(self, *path, **kwargs):
        """
        Fetch the resource using WASD.TV API.

        The positional arguments are the parts of the resource path relative
        to the _API_BASE.

        The following keyword arguments are required by this method:
            * item_id -- item identifier (for logging purposes).
            * description -- human-readable resource description (for logging
            purposes).

        Any additional keyword arguments are passed directly to
        the _download_json method.
        """
        description = kwargs.pop('description')
        response = self._download_json(
            urljoin(self._API_BASE, '/'.join(map(compat_str, path))),
            kwargs.pop('item_id'),
            note='Downloading {} metadata'.format(description),
            errnote='Unable to download {} metadata'.format(description),
            **compat_kwargs(kwargs))
        if not isinstance(response, dict):
            raise ExtractorError(
                'JSON object expected, got: {!r}'.format(response))
        error = response.get('error')
        if error:
            raise ExtractorError(
                '{} returned error: {}'.format(self.IE_NAME, error['code']),
                expected=True)
        return response['result']

    def _extract_thumbnails(self, thumbnails_dict):
        if not thumbnails_dict:
            return None
        thumbnails = []
        for index, thumbnail_size in enumerate(self._THUMBNAIL_SIZES):
            thumbnail_url = thumbnails_dict.get(thumbnail_size)
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'preference': index,
            })
        return thumbnails

    def _extract_og_title(self, url, item_id):
        return self._og_search_title(self._download_webpage(url, item_id))


class WASDTVBaseVideoIE(WASDTVBaseIE):

    def _get_container(self, url):
        """
        Download and extract the media container dict for the given URL.
        Return the container dict.
        """
        raise NotImplementedError

    def _get_media_url(self, media_meta):
        """
        Extract the m3u8 URL from the media_meta dict.
        Return a tuple (url: str, is_live: bool).
        """
        raise NotImplementedError

    def _real_extract(self, url):
        container = self._get_container(url)
        stream = container['media_container_streams'][0]
        media = stream['stream_media'][0]
        media_meta = media['media_meta']
        media_url, is_live = self._get_media_url(media_meta)
        video_id = media.get('media_id') or container.get('media_container_id')
        return {
            'id': compat_str(video_id),
            'title': (
                container.get('media_container_name')
                or self._extract_og_title(url, video_id)),
            'description': container.get('media_container_description'),
            'thumbnails': self._extract_thumbnails(
                media_meta.get('media_preview_images')),
            'timestamp': parse_iso8601(container.get('created_at')),
            'view_count': int_or_none(stream.get(
                'stream_current_viewers' if is_live
                else 'stream_total_viewers')),
            'is_live': is_live,
            'formats': self._extract_m3u8_formats(media_url, video_id, 'mp4'),
        }


class WASDTVStreamIE(WASDTVBaseVideoIE):
    IE_NAME = 'wasdtv:stream'
    _VALID_URL = r'https?://wasd\.tv/(?P<id>[^/#?]+)$'
    _TEST = {
        'url': 'https://wasd.tv/24_7',
        'info_dict': {
            'id': '559738',
            'ext': 'mp4',
            'title': 'Live 24/7 Music',
            'description': '24&#x2F;7 Music',
            'timestamp': int,
            'upload_date': r're:^\d{8}$',
            'is_live': True,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _get_container(self, url):
        nickname = self._match_id(url)
        channel = self._fetch(
            'channels', 'nicknames', nickname,
            item_id=nickname,
            description='channel')
        channel_id = channel['channel_id']
        containers = self._fetch(
            'v2', 'media-containers',
            query={
                'channel_id': channel_id,
                'media_container_type': 'SINGLE',
                'media_container_status': 'RUNNING',
            },
            item_id=channel_id,
            description='running media containers')
        if not containers:
            raise ExtractorError(
                '{} is offline'.format(nickname), expected=True)
        return containers[0]

    def _get_media_url(self, media_meta):
        return media_meta['media_url'], True


class WASDTVRecordIE(WASDTVBaseVideoIE):
    IE_NAME = 'wasdtv:record'
    _VALID_URL = r'https?://wasd\.tv/[^/#?]+/videos\?record=(?P<id>\d+)$'
    _TEST = {
        'url': 'https://wasd.tv/mightypoot/videos?record=551500',
        'info_dict': {
            'id': '551593',
            'ext': 'mp4',
            'title': 'Похвали Стримера Финал: Fall Guys, Darkest Dungeon',
            'description': 'Здрасте.\nна этом всё',
            'timestamp': 1598885270,
            'upload_date': '20200831',
            'is_live': False,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _get_container(self, url):
        container_id = self._match_id(url)
        return self._fetch(
            'v2', 'media-containers', container_id,
            item_id=container_id,
            description='media container')

    def _get_media_url(self, media_meta):
        media_archive_url = media_meta.get('media_archive_url')
        if media_archive_url:
            return media_archive_url, False
        return media_meta['media_url'], True


class WASDTVClipIE(WASDTVBaseIE):
    IE_NAME = 'wasdtv:clip'
    _VALID_URL = r'https?://wasd\.tv/[^/#?]+/clips\?clip=(?P<id>\d+)$'
    _TEST = {
        'url': 'https://wasd.tv/dawgos/clips?clip=5539',
        'info_dict': {
            'id': '5539',
            'ext': 'mp4',
            'title': 'это про вас',
            'timestamp': 1598912283,
            'upload_date': '20200831',
            'view_count': None,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        clip_id = self._match_id(url)
        clip = self._fetch(
            'v2', 'clips', clip_id,
            item_id=clip_id,
            description='clip')
        clip_data = clip['clip_data']
        return {
            'id': compat_str(clip_id),
            'title': (
                clip.get('clip_title')
                or self._extract_og_title(url, clip_id)),
            'thumbnails': self._extract_thumbnails(clip_data.get('preview')),
            'timestamp': parse_iso8601(clip.get('created_at')),
            'view_count': int_or_none(clip.get('clip_views_count')),
            'formats': self._extract_m3u8_formats(
                clip_data['url'], clip_id, 'mp4'),
        }
