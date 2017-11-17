# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    get_element_by_id, str_or_none, get_element_by_class, strip_or_none,
    float_or_none)


class VidliiIE(InfoExtractor):
    _VALID_URL = r'(?:https*?:\/\/)*(?:www\.)*vidlii.com\/watch\?v=(?P<id>[^?\s]{11})'
    _TESTS = [{
        'url': 'https://www.vidlii.com/watch?v=tJluaH4BJ3v',
        'md5': '9bf7d1e005dfa909b6efb0a1ff5175e2',
        'info_dict': {
            'id': 'tJluaH4BJ3v',
            'title': 'Vidlii is against me',
            'description': 'I have HAD it. Vidlii does not like me. I have tried to uplaod videos and submit them to the contest and no ne of my videos show up so maybe it is broken for everyone else but this one was trying to submit it because I wanted to submit to the contest :) Tanks I hope the website is fixed PS: Jan you are cool please add my video',
            'thumbnail': 'https://www.vidlii.com/usfi/thmp/tJluaH4BJ3v.jpg',
            'uploader': 'APPle5auc31995',
            'url': 'https://cdn.vidlii.com/videos/tJluaH4BJ3v.mp4',
            'uploader_url': 'https://www.vidlii.com/user/APPle5auc31995',
            'upload_date': '20171107',
            'categories': 'News & Politics',
            'tags': ['Vidlii', 'Jan', 'Videogames'],
            'duration': 212,
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'type': 'video',
            'ext': 'mp4'
        }
    }, {
        'url': 'https://www.vidlii.com/watch?v=vBo2IcrwOkO',
        'md5': 'b42640a596b4dc986702567d49268963',
        'info_dict': {
            'id': 'vBo2IcrwOkO',
            'title': '(OLD VIDEO) i like youtube!!',
            'description': 'Original upload date:<br />\nMarch 10th 2011<br />\nCredit goes to people who own content in the video',
            'thumbnail': 'https://www.vidlii.com/usfi/thmp/vBo2IcrwOkO.jpg',
            'uploader': 'MyEditedVideoSpartan',
            'url': 'https://cdn.vidlii.com/videos/vBo2IcrwOkO.mp4',
            'uploader_url': 'https://www.vidlii.com/user/MyEditedVideoSpartan',
            'upload_date': '20171011',
            'categories': 'Film & Animation',
            'tags': None,
            'duration': 34,
            'view_count': int,
            'comment_count': int,
            'average_rating': float,
            'type': 'video',
            'ext': 'mp4'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title_1 = str_or_none(
            self._html_search_regex(r'<h1>(.+?)</h1>', webpage,
                                    'title', default=None))
        title_2 = str_or_none(
            self._html_search_regex(r'<title>([^<]+?)</title>', webpage,
                                    'title', default=None)).replace(
            " - VidLii", "")
        title_3 = str_or_none(
            self._html_search_meta('twitter:title', webpage, 'title',
                                   default=False)).replace(" - VidLii", "")
        # assert title_1 == title_2 == title_3, "TITLE fallback is not working"
        title = title_1 or title_2 or title_3

        description = strip_or_none(
            get_element_by_id('des_text', webpage).strip())

        uploader_1 = str_or_none(
            self._html_search_regex(
                r'<div[^>]+class="wt_person"[^>]*>(?:[^<]+)<a href="\/user\/[^>]*?>([^<]*?)<',
                webpage,
                'uploader', default=None))
        uploader_2 = str_or_none(
            self._html_search_regex(
                r'<img src="[^>]+?class=["\']avt2\s*["\'][^>]+?alt=["\']([^"\']+?)["\']',
                webpage, 'uploader', default=None))
        # assert uploader_1 == uploader_2, "UPLOADER fallback is not working"
        uploader = uploader_1 or uploader_2

        url = self._html_search_regex(
            r'videoInfo[\s]*=[\s]*{[^}]*src:[\s]*(?:"|\')([^"]*?)(?:"|\')',
            webpage, 'url', default=None)

        # get additional properties
        uploader_url = "https://www.vidlii.com/user/%s" % uploader

        # returns date as YYYYMMDD
        upload_date = str_or_none(
            self._html_search_meta('datePublished', webpage, 'upload_date',
                                   default=False).replace("-",
                                                          ""))

        categories = self._html_search_regex(
            r'<div>Category:\s*<\/div>[\s\r]*<div>[\s\r]*<a href="\/videos\?c=[^>]*>([^<]*?)<\/a>',
            webpage,
            'categories', default=None)
        tags = re.findall(r'<a href="/results\?q=[^>]*>[\s]*([^<]*)</a>',
                          webpage) or None
        duration_1 = int_or_none(
            self._html_search_meta('video:duration', webpage, 'duration',
                                   default=False))
        duration_2 = int_or_none(
            self._html_search_regex(
                r'videoInfo[^=]*=[^{]*{[^}]*dur:([^,}]*?),', webpage,
                'duration', default=None))
        # assert duration_1 == duration_2, "DURATION fallback is not working"
        duration = duration_1 or duration_2

        view_count_1 = int_or_none(self._html_search_regex(
            r'Views:[^<]*<strong>([^<]*?)<\/strong>', webpage,
            'view_count', default=None))
        view_count_2 = re.findall(r'<strong>([^<]*?)</strong>',
                                  get_element_by_class("w_views",
                                                       webpage))
        view_count_2 = int_or_none(view_count_2[
                                       0]) if view_count_2 else None
        # assert view_count_1 == view_count_2, "VIEW COUNT fallback is not working"
        view_count = view_count_1 or view_count_2

        comment_count_1 = int_or_none(self._html_search_regex(
            r'Comments:[^<]*<strong>([^<]*?)<\/strong>', webpage,
            'comment_count', default=None))
        comment_count_2 = int_or_none(
            self._html_search_regex(
                r'<span[^>]+id="cmt_num"[^>]*>([^<]+?)<\/span>', webpage,
                'comment_count', default=None))
        # assert comment_count_1 == comment_count_2, "COMMENT COUNT fallback is not working"
        comment_count = comment_count_1 or comment_count_2

        average_rating = float_or_none(
            self._html_search_regex(
                r'{[\s\r]*\$\("#rateYo"\).rateYo\({[^}]*rating:\s*([^,]*?),[^}.]*}',
                webpage, 'average_rating', default=None))
        thumbnail_link = self._html_search_regex(
            r'videoInfo[\s]*=[\s]*{[^}]*img:[\s]*(?:"|\')([^"]*?)(?:"|\')',
            webpage, 'thumbnail', default=None)
        thumbnail = 'https://www.vidlii.com%s' % thumbnail_link
        video_type = self._og_search_property('type', webpage, 'type')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'url': url,
            'uploader_url': uploader_url,
            'upload_date': upload_date,
            'categories': categories,
            'tags': tags,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'thumbnail': thumbnail,
            'type': video_type
        }
