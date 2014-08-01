# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import get_element_by_id, parse_iso8601, determine_ext, int_or_none


class IzleseneIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?izlesene\.com/(?:video|embedplayer)/(?:[^/]+/)?(?P<id>[0-9]+)'
    _STREAM_URL = 'http://panel.izlesene.com/api/streamurl/{id:}/{format:}'
    _TEST = {
        'url': 'http://www.izlesene.com/video/sevincten-cildirtan-dogum-gunu-hediyesi/7599694',
        'md5': '4384f9f0ea65086734b881085ee05ac2',
        'info_dict': {
            'id': '7599694',
            'title': u'Sevinçten Çıldırtan Doğum Günü Hediyesi',
            'upload_date': '20140702',
            'uploader_id': 'pelikzzle',
            'description': u'Annesi oğluna doğum günü hediyesi olarak minecraft cd si alıyor, ve çocuk hunharca seviniyor',
            'timestamp': 1404298698,
            'duration': 95,
            'ext': 'mp4',
            'thumbnail': 're:^http://.*\.jpg',
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
        duration = int(
            self._html_search_regex(
                r'"videoduration"\s?:\s?"([^"]+)"', webpage, 'duration',
                fatal=False, default='0')
            ) / 1000
        view_count = get_element_by_id('videoViewCount',
                                       webpage).replace('.', '')
        timestamp = parse_iso8601(self._html_search_meta('uploadDate', webpage,
                                  'upload date', fatal=False))
        family_friendly = self._html_search_meta('isFamilyFriendly', webpage,
                                                 'age limit', fatal=False)
        uploader = self._html_search_regex(r"adduserUsername\s?=\s?'([^']+)';",
                                           webpage, 'uploader', fatal=False,
                                           default='')
        comment_count = self._html_search_regex(
            r'comment_count\s?=\s?\'([^\']+)\';',
            webpage, 'uploader', fatal=False)

        content_url = self._html_search_meta('contentURL', webpage,
                                             'content URL', fatal=False)
        ext = determine_ext(content_url)

        # Might be empty for some videos.
        qualities = self._html_search_regex(r'"quality"\s?:\s?"([^"]+)"',
                                            webpage, 'qualities', fatal=False,
                                            default='')

        formats = []
        for quality in qualities.split('|'):
            json = self._download_json(
                self._STREAM_URL.format(id=video_id, format=quality), video_id,
                note=u'Getting video URL for "%s" quality' % quality,
                errnote=u'Failed to get video URL for "%s" quality' % quality
            )
            video_format = '%sp' % quality if quality else 'sd'
            formats.append({
                'url': json.get('streamurl'),
                'ext': ext,
                'format': video_format,
                'format_id': video_format,
            })

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': int_or_none(view_count),
            'timestamp': timestamp,
            'age_limit': 18 if family_friendly == 'False' else 0,
            'uploader_id': uploader,
            'comment_count': int_or_none(comment_count),
        }
