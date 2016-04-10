# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate


class GlideIE(InfoExtractor):
    IE_DESC = 'Glide mobile video messages (glide.me)'
    _VALID_URL = r'https?://share\.glide\.me/(?P<id>[A-Za-z0-9\-=_+]+)'
    _TEST = {
        'url': 'http://share.glide.me/UZF8zlmuQbe4mr+7dCiQ0w==',
        'md5': '4466372687352851af2d131cfaa8a4c7',
        'info_dict': {
            'id': 'UZF8zlmuQbe4mr+7dCiQ0w==',
            'ext': 'mp4',
            'title': 'Damon Timm\'s Glide message',
            'thumbnail': 're:^https?://.*?\.cloudfront\.net/.*\.jpg$',
            'uploader': 'Damon Timm',
            'upload_date': '20140919',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title')
        video_url = self._proto_relative_url(self._search_regex(
            r'<source[^>]+src=(["\'])(?P<url>.+?)\1',
            webpage, 'video URL', default=None,
            group='url')) or self._og_search_video_url(webpage)
        thumbnail = self._proto_relative_url(self._search_regex(
            r'<img[^>]+id=["\']video-thumbnail["\'][^>]+src=(["\'])(?P<url>.+?)\1',
            webpage, 'thumbnail url', default=None,
            group='url')) or self._og_search_thumbnail(webpage)
        uploader = self._search_regex(
            r'<div[^>]+class=["\']info-name["\'][^>]*>([^<]+)',
            webpage, 'uploader', fatal=False)
        upload_date = unified_strdate(self._search_regex(
            r'<div[^>]+class="info-date"[^>]*>([^<]+)',
            webpage, 'upload date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
        }
