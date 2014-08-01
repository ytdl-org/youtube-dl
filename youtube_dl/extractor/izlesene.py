# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    get_element_by_id,
    parse_iso8601,
    determine_ext,
    int_or_none,
    str_to_int,
)


class IzleseneIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?izlesene\.com/(?:video|embedplayer)/(?:[^/]+/)?(?P<id>[0-9]+)'
    _STREAM_URL = 'http://panel.izlesene.com/api/streamurl/{id:}/{format:}'
    _TEST = {
        'url': 'http://www.izlesene.com/video/sevincten-cildirtan-dogum-gunu-hediyesi/7599694',
        'md5': '4384f9f0ea65086734b881085ee05ac2',
        'info_dict': {
            'id': '7599694',
            'ext': 'mp4',
            'title': 'Sevinçten Çıldırtan Doğum Günü Hediyesi',
            'description': 'Annesi oğluna doğum günü hediyesi olarak minecraft cd si alıyor, ve çocuk hunharca seviniyor',
            'thumbnail': 're:^http://.*\.jpg',
            'uploader_id': 'pelikzzle',
            'timestamp': 1404298698,
            'upload_date': '20140702',
            'duration': 95.395,
            'age_limit': 0,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = 'http://www.izlesene.com/video/%s' % video_id

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        uploader = self._html_search_regex(
            r"adduserUsername\s*=\s*'([^']+)';", webpage, 'uploader', fatal=False, default='')
        timestamp = parse_iso8601(self._html_search_meta(
            'uploadDate', webpage, 'upload date', fatal=False))

        duration = int_or_none(self._html_search_regex(
            r'"videoduration"\s*:\s*"([^"]+)"', webpage, 'duration', fatal=False))
        if duration:
            duration /= 1000.0

        view_count = str_to_int(get_element_by_id('videoViewCount', webpage))
        comment_count = self._html_search_regex(
            r'comment_count\s*=\s*\'([^\']+)\';', webpage, 'uploader', fatal=False)

        family_friendly = self._html_search_meta(
            'isFamilyFriendly', webpage, 'age limit', fatal=False)

        content_url = self._html_search_meta(
            'contentURL', webpage, 'content URL', fatal=False)
        ext = determine_ext(content_url, 'mp4')

        # Might be empty for some videos.
        qualities = self._html_search_regex(
            r'"quality"\s*:\s*"([^"]+)"', webpage, 'qualities', fatal=False, default='')

        formats = []
        for quality in qualities.split('|'):
            json = self._download_json(
                self._STREAM_URL.format(id=video_id, format=quality), video_id,
                note='Getting video URL for "%s" quality' % quality,
                errnote='Failed to get video URL for "%s" quality' % quality
            )
            formats.append({
                'url': json.get('streamurl'),
                'ext': ext,
                'format_id': '%sp' % quality if quality else 'sd',
            })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader_id': uploader,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': int_or_none(view_count),
            'comment_count': int_or_none(comment_count),
            'age_limit': 18 if family_friendly == 'False' else 0,
            'formats': formats,
        }
