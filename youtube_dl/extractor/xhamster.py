from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate,
    str_to_int,
    int_or_none,
    parse_duration,
)


class XHamsterIE(InfoExtractor):
    """Information Extractor for xHamster"""
    _VALID_URL = r'http://(?:www\.)?xhamster\.com/movies/(?P<id>[0-9]+)/(?P<seo>.+?)\.html(?:\?.*)?'
    _TESTS = [
        {
            'url': 'http://xhamster.com/movies/1509445/femaleagent_shy_beauty_takes_the_bait.html',
            'md5': '8281348b8d3c53d39fffb377d24eac4e',
            'info_dict': {
                'id': '1509445',
                'ext': 'mp4',
                'title': 'FemaleAgent Shy beauty takes the bait',
                'upload_date': '20121014',
                'uploader_id': 'Ruseful2011',
                'duration': 893,
                'age_limit': 18,
            }
        },
        {
            'url': 'http://xhamster.com/movies/2221348/britney_spears_sexy_booty.html?hd',
            'md5': '4cbd8d56708ecb4fb4124c23e4acb81a',
            'info_dict': {
                'id': '2221348',
                'ext': 'mp4',
                'title': 'Britney Spears  Sexy Booty',
                'upload_date': '20130914',
                'uploader_id': 'jojo747400',
                'duration': 200,
                'age_limit': 18,
            }
        }
    ]

    def _real_extract(self,url):
        def extract_video_url(webpage):
            mp4 = re.search(r'<video\s+.*?file="([^"]+)".*?>', webpage)
            if mp4 is None:
                raise ExtractorError('Unable to extract media URL')
            else:
                return mp4.group(1)

        def is_hd(webpage):
            return '<div class=\'icon iconHD\'' in webpage

        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        seo = mobj.group('seo')
        mrss_url = 'http://xhamster.com/movies/%s/%s.html' % (video_id, seo)
        webpage = self._download_webpage(mrss_url, video_id)

        title = self._html_search_regex(r'<title>(?P<title>.+?) - xHamster\.com</title>', webpage, 'title')

        # Only a few videos have an description
        mobj = re.search(r'<span>Description: </span>([^<]+)', webpage)
        description = mobj.group(1) if mobj else None

        upload_date = self._html_search_regex(r'hint=\'(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} [A-Z]{3,4}\'',
            webpage, 'upload date', fatal=False)
        if upload_date:
            upload_date = unified_strdate(upload_date)

        uploader_id = self._html_search_regex(r'<a href=\'/user/[^>]+>(?P<uploader_id>[^<]+)',
            webpage, 'uploader id', default='anonymous')

        thumbnail = self._html_search_regex(r'<video\s+.*?poster="([^"]+)".*?>', webpage, 'thumbnail', fatal=False)

        duration = parse_duration(self._html_search_regex(r'<span>Runtime:</span> (\d+:\d+)</div>',
            webpage, 'duration', fatal=False))

        view_count = self._html_search_regex(r'<span>Views:</span> ([^<]+)</div>', webpage, 'view count', fatal=False)
        if view_count:
            view_count = str_to_int(view_count)

        mobj = re.search(r"hint='(?P<likecount>\d+) Likes / (?P<dislikecount>\d+) Dislikes'", webpage)
        (like_count, dislike_count) = (mobj.group('likecount'), mobj.group('dislikecount')) if mobj else (None, None)

        mobj = re.search(r'</label>Comments \((?P<commentcount>\d+)\)</div>', webpage)
        comment_count = mobj.group('commentcount') if mobj else 0

        age_limit = self._rta_search(webpage)

        hd = is_hd(webpage)

        video_url = extract_video_url(webpage)
        formats = [{
            'url': video_url,
            'format_id': 'hd' if hd else 'sd',
            'preference': 1,
        }]

        if not hd:
            mrss_url = self._search_regex(r'<link rel="canonical" href="([^"]+)', webpage, 'mrss_url')
            webpage = self._download_webpage(mrss_url + '?hd', video_id, note='Downloading HD webpage')
            if is_hd(webpage):
                video_url = extract_video_url(webpage)
                formats.append({
                    'url': video_url,
                    'format_id': 'hd',
                    'preference': 2,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'uploader_id': uploader_id,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': int_or_none(like_count),
            'dislike_count': int_or_none(dislike_count),
            'comment_count': int_or_none(comment_count),
            'age_limit': age_limit,
            'formats': formats,
        }
