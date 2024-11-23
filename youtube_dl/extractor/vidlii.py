# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

from ..utils import (
    float_or_none,
    get_element_by_id,
    int_or_none,
    strip_or_none,
    unified_strdate,
    urljoin,
    str_to_int,
)


class VidLiiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidlii\.com/(?:watch|embed)\?.*?\bv=(?P<id>[0-9A-Za-z_-]{11})'
    _TESTS = [{
        'url': 'https://www.vidlii.com/watch?v=tJluaH4BJ3v',
        'md5': '9bf7d1e005dfa909b6efb0a1ff5175e2',
        'info_dict': {
            'id': 'tJluaH4BJ3v',
            'ext': 'mp4',
            'title': 'Vidlii is against me',
            'description': 'md5:fa3f119287a2bfb922623b52b1856145',
            'thumbnail': 're:https://.*.jpg',
            'uploader': 'APPle5auc31995',
            'uploader_url': 'https://www.vidlii.com/user/APPle5auc31995',
            'upload_date': '20171107',
            'duration': 212,
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'categories': ['News & Politics'],
            'tags': ['Vidlii', 'Jan', 'Videogames'],
        }
    }, {
        # HD
        'url': 'https://www.vidlii.com/watch?v=2Ng8Abj2Fkl',
        'md5': '450e7da379c884788c3a4fa02a3ce1a4',
        'info_dict': {
            'id': '2Ng8Abj2Fkl',
            'ext': 'mp4',
            'title': 'test',
            'description': 'md5:cc55a86032a7b6b3cbfd0f6b155b52e9',
            'thumbnail': 'https://www.vidlii.com/usfi/thmp/2Ng8Abj2Fkl.jpg',
            'uploader': 'VidLii',
            'uploader_url': 'https://www.vidlii.com/user/VidLii',
            'upload_date': '20200927',
            'duration': 5,
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'categories': ['Film & Animation'],
            'tags': list,
        },
    }, {
        'url': 'https://www.vidlii.com/embed?v=tJluaH4BJ3v&a=0',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.vidlii.com/watch?v=%s' % video_id, video_id)

        formats = []

        def add_format(format_url, height=None):
            height = int(self._search_regex(r'(\d+)\.mp4',
                         format_url, 'height', default=360))

            formats.append({
                'url': format_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
            })

        sources = re.findall(
            r'src\s*:\s*(["\'])(?P<url>(?:https?://)?(?:(?!\1).)+)\1',
            webpage)

        formats = []
        if len(sources) > 1:
            add_format(sources[1][1])
            self._check_formats(formats, video_id)
        if len(sources) > 0:
            add_format(sources[0][1])

        self._sort_formats(formats)

        title = self._html_search_regex(
            (r'<h1>([^<]+)</h1>', r'<title>([^<]+) - VidLii<'), webpage,
            'title')

        description = self._html_search_meta(
            ('description', 'twitter:description'), webpage,
            default=None) or strip_or_none(
            get_element_by_id('des_text', webpage))

        thumbnail = self._html_search_meta(
            'twitter:image', webpage, default=None)
        if not thumbnail:
            thumbnail_path = self._search_regex(
                r'img\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'thumbnail', fatal=False, group='url')
            if thumbnail_path:
                thumbnail = urljoin(url, thumbnail_path)

        uploader = self._search_regex(
            r'<div[^>]+class=["\']wt_person[^>]+>\s*<a[^>]+\bhref=["\']/user/[^>]+>([^<]+)',
            webpage, 'uploader', fatal=False)
        uploader_url = 'https://www.vidlii.com/user/%s' % uploader if uploader else None

        upload_date = unified_strdate(self._html_search_meta(
            'datePublished', webpage, default=None) or self._search_regex(
            r'<date>([^<]+)', webpage, 'upload date', fatal=False))

        duration = int_or_none(self._html_search_meta(
            'video:duration', webpage, 'duration',
            default=None) or self._search_regex(
            r'duration\s*:\s*(\d+)', webpage, 'duration', fatal=False))

        view_count = str_to_int(self._html_search_regex(
            (r'<strong>([\d,.]+)</strong> views',
             r'Views\s*:\s*<strong>([\d,.]+)</strong>'),
            webpage, 'view count', fatal=False))

        comment_count = int_or_none(self._search_regex(
            (r'<span[^>]+id=["\']cmt_num[^>]+>(\d+)',
             r'Comments\s*:\s*<strong>(\d+)'),
            webpage, 'comment count', fatal=False))

        average_rating = float_or_none(self._search_regex(
            r'rating\s*:\s*([\d.]+)', webpage, 'average rating', fatal=False))

        category = self._html_search_regex(
            r'<div>Category\s*:\s*</div>\s*<div>\s*<a[^>]+>([^<]+)', webpage,
            'category', fatal=False)
        categories = [category] if category else None

        tags = [
            strip_or_none(tag)
            for tag in re.findall(
                r'<a[^>]+\bhref=["\']/results\?.*?q=[^>]*>([^<]+)',
                webpage) if strip_or_none(tag)
        ] or None

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_url': uploader_url,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'categories': categories,
            'tags': tags,
        }
