from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    str_to_int,
    urlencode_postdata,
)


class RadioJavanBaseIE(InfoExtractor):
    def _real_extract(self, url):
        media_id = self._match_id(url)

        webpage = self._download_webpage(url, media_id)

        download_host = self._download_json(
            self._HOST_TRACKER_URL,
            media_id,
            data=urlencode_postdata({'id': media_id}),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': url,
            }
        )['host']

        formats = self.get_formats(webpage, download_host)
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        upload_date = unified_strdate(self._search_regex(
            r'class="date_added">Date added: ([^<]+)<',
            webpage, 'upload date', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="views">Plays: ([\d,]+)',
            webpage, 'view count', fatal=False))
        like_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) likes',
            webpage, 'like count', fatal=False))
        dislike_count = str_to_int(self._search_regex(
            r'class="rating">([\d,]+) dislikes',
            webpage, 'dislike count', fatal=False))

        return {
            'id': media_id,
            'title': title,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }


class RadioJavanVideoIE(RadioJavanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/videos/video/(?P<id>[^/]+)/?'
    _HOST_TRACKER_URL = 'https://www.radiojavan.com/videos/video_host'
    _TEST = {
        'url': 'http://www.radiojavan.com/videos/video/chaartaar-ashoobam',
        'md5': 'e85208ffa3ca8b83534fca9fe19af95b',
        'info_dict': {
            'id': 'chaartaar-ashoobam',
            'ext': 'mp4',
            'title': 'Chaartaar - Ashoobam',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'upload_date': '20150215',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        }
    }

    def get_formats(self, webpage, download_host):
        return [{
            'url': '%s/%s' % (download_host, video_path),
            'format_id': '%sp' % height,
            'height': int(height),
        } for height, video_path in re.findall(r"RJ\.video(\d+)p\s*=\s*'/?([^']+)'", webpage)]


class RadioJavanMp3IE(RadioJavanBaseIE):
    _VALID_URL = r'https?://(?:www\.)?radiojavan\.com/mp3s/mp3/(?P<id>[^/?]+)/?'
    _HOST_TRACKER_URL = 'https://www.radiojavan.com/mp3s/mp3_host'
    _TEST = {
        'url': 'https://www.radiojavan.com/mp3s/mp3/Mazyar-Fallahi-Baran-Fallahi-Begoo-Boro',
        'md5': '9601a5a94ced3a2f772f8d18170a8920',
        'info_dict': {
            'id': 'Mazyar-Fallahi-Baran-Fallahi-Begoo-Boro',
            'ext': 'mp3',
            'title': 'Mazyar Fallahi & Baran Fallahi - Begoo Boro',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'upload_date': '20180729',
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
        }
    }

    def get_formats(self, webpage, download_host):
        mp3_path = re.findall(r"RJ\.currentMP3Url\s*=\s*'/?([^']+)'", webpage)[0]
        return [{'url': '%s/media/%s.mp3' % (download_host, mp3_path)}]
