# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    get_element_by_id, get_element_by_class, strip_or_none,
    float_or_none, urljoin, js_to_json, unified_strdate)


class VidliiIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidlii.com/watch\?v=(?P<id>.{11})'
    _TESTS = [{
        'url': 'https://www.vidlii.com/watch?v=tJluaH4BJ3v',
        'md5': '9bf7d1e005dfa909b6efb0a1ff5175e2',
        'info_dict': {
            'id': 'tJluaH4BJ3v',
            'title': 'Vidlii is against me',
            'description': 'md5:de24ab8a9a310976d66bebb824aa2420',
            'thumbnail': 're:https://.*.jpg',
            'uploader': 'APPle5auc31995',
            'uploader_url': 'https://www.vidlii.com/user/APPle5auc31995',
            'upload_date': '20171107',
            'categories': 'News & Politics',
            'tags': ['Vidlii', 'Jan', 'Videogames'],
            'duration': 212,
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'ext': 'mp4'
        }
    }, {
        'url': 'https://www.vidlii.com/watch?v=vBo2IcrwOkO',
        'md5': 'b42640a596b4dc986702567d49268963',
        'info_dict': {
            'id': 'vBo2IcrwOkO',
            'title': '(OLD VIDEO) i like youtube!!',
            'description': 'Original upload date:<br />\nMarch 10th 2011<br />\nCredit goes to people who own content in the video',
            'thumbnail': 're:https://.*.jpg',
            'uploader': 'MyEditedVideoSpartan',
            'uploader_url': 'https://www.vidlii.com/user/MyEditedVideoSpartan',
            'upload_date': '20171011',
            'categories': 'Film & Animation',
            'tags': None,
            'duration': 34,
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'ext': 'mp4'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # extract videoInfo variable for further use
        videoInfo_dict = self._parse_json(js_to_json(self._html_search_regex(r'var\s*videoInfo\s*=\s*({[^}]*})', webpage,
                                                                             'videoInfo', fatal=True)), video_id)

        # extract basic properties of video
        title = (self._html_search_regex(r'<title>([^<]+?)</title>', webpage, 'title', default='', fatal=True) or
                 self._html_search_meta('twitter:title', webpage, 'title', default='', fatal=True)).replace(' - VidLii', '') \
                or self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title', default=None, fatal=True)

        description = strip_or_none(get_element_by_id('des_text', webpage))

        uploader_patterns = [r'<div[^>]+class="wt_person"[^>]*>(?:[^<]+)<a href="/user/[^>]*?>([^<]*?)<',
                             r'<img src="[^>]+?class=(?:"avt2\s*"',
                             r'\'avt2\s*\')[^>]+?alt=(?:"([^"]+?)"',
                             r'\'([^\']+?)\')>']
        uploader = self._html_search_regex(uploader_patterns, webpage, 'uploader', fatal=False)

        video_url = videoInfo_dict.get('src')

        # get additional properties
        uploader_url = urljoin('https://www.vidlii.com/user/', uploader)

        # returns date as YYYYMMDD
        upload_date = unified_strdate(
            self._html_search_meta('datePublished', webpage, 'upload_date', default=None,
                                   fatal=False) or self._html_search_regex(r'<date>(['r'^<]*?)</date>', webpage,
                                                                           'upload_date',
                                                                           default=None, fatal=False))

        categories = self._html_search_regex(
            r'<div>Category:\s*</div>[\s\r]*<div>[\s\r]*<a href="/videos\?c=[^>]*>([^<]*?)</a>', webpage, 'categories',
            default=None, fatal=False)
        tags = re.findall(r'<a href="/results\?q=[^>]*>\s*([^<]*)</a>', webpage) or None
        duration = int_or_none(
            self._html_search_meta('video:duration', webpage, 'duration', default=False, fatal=False) or
            videoInfo_dict.get('dur'))

        view_count_fb = re.findall(r'<strong>([^<]*?)</strong>', get_element_by_class('w_views', webpage) or '')
        view_count_fb = view_count_fb[0] if view_count_fb else None
        view_count = int_or_none(self._html_search_regex(r'Views:[^<]*<strong>([^<]*?)</strong>', webpage, 'view_count',
                                                         default=None, fatal=False)) or int_or_none(view_count_fb)

        comment_count_patterns = [r'Comments:[^<]*<strong>([^<]*?)</strong>',
                                  r'<span[^>]+id="cmt_num"[^>]*>([^<]+?)</span>']
        comment_count = int_or_none(
            self._html_search_regex(comment_count_patterns, webpage, 'comment_count', default=None, fatal=False))

        average_rating = float_or_none(
            self._html_search_regex(r'rating:\s*([^,]*),',
                                    webpage, 'average_rating', default=None, fatal=False))
        thumbnail_link = videoInfo_dict.get('img')
        thumbnail = urljoin('https://www.vidlii.com/', thumbnail_link)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'url': video_url,
            'uploader_url': uploader_url,
            'upload_date': upload_date,
            'categories': categories,
            'tags': tags,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'thumbnail': thumbnail,
        }
