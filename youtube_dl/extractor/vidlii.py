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
            # TODO this might change in future, how to handle?
            'view_count': 233,
            # TODO this might change in future, how to handle?
            'comment_count': 13,
            'average_rating': 1.8571428571429,
            'type': 'video',
            'ext': 'mp4'
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    },  {
        'url': 'https://www.vidlii.com/watch?v=vBo2IcrwOkO',
        'md5': 'b42640a596b4dc986702567d49268963',
        'info_dict': {
            'id': 'vBo2IcrwOkO',
            'ext': 'mp4',
            'title': '(OLD VIDEO) i like youtube!!',
            'thumbnail': 'https://www.vidlii.com/usfi/thmp/vBo2IcrwOkO.jpg',
            'upload_date': '20171011',
            'description':'Original upload date:<br />\nMarch 10th 2011<br />\nCredit goes to people who own content in the video',
            'uploader': 'MyEditedVideoSpartan'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)

        }

    },  {
        'url': 'https://www.vidlii.com/watch?v=E8SeUE3J5EV',
        'md5': 'f202427f9b31171f0fdd0ddeacb24720',
        'info_dict': {
            'id': 'E8SeUE3J5EV',
            'ext': 'mp4',
            'title': 'Games make you violent',
            'thumbnail': 'https://www.vidlii.com/usfi/thmp/E8SeUE3J5EV.jpg',
            'upload_date': '20171116',
            'description':'Games are made by the communistic feminist fbi cia jews and they control your mind and make you want to kill',
            'uploader': 'APPle5auc31995'
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }]

    def _real_extract(self, url):
        # get required video properties
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = str_or_none(
            self._html_search_regex(r'<h1>(.+?)</h1>', webpage,
                                    'title', default=None)) or str_or_none(
            self._html_search_regex(r'<title>([^<]+?)</title>', webpage,
                                    'title', default=None)) or str_or_none(
            self._html_search_meta('twitter:title', webpage, 'title',
                                   default=False))
        description = strip_or_none(
            get_element_by_id('des_text', webpage).strip())

        uploader = str_or_none(
            self._html_search_regex(
                r'<div[^>]+class="wt_person"[^>]*>(?:[^<]+)<a href="\/user\/[^>]*?>([^<]*?)<',
                webpage,
                'uploader', default=None)) or str_or_none(
            self._html_search_regex(
                r'<img src="[^>]+?class=["\']avt2\s*["\'][^>]+?alt=["\']([^"\']+?)["\']',
                webpage, 'uploader', default=None))

        url = self._html_search_regex(
            r'videoInfo[\s]*=[\s]*{[^}]*src:[\s]*(?:"|\')([^"]*?)(?:"|\')',
            webpage, 'url', default=None)

        # get additional properties
        uploader_url = "https://www.vidlii.com/user/%s" % uploader

        upload_date = str_or_none(
            self._html_search_meta('datePublished', webpage, 'upload_date',
                                   default=False).replace("-",
                                                          "")) or str_or_none(
            self._html_search_regex(r'<date>(.+?)</date>', webpage,
                                    'upload_date', default="").replace("-",
                                                                       ""))
        categories = self._html_search_regex(
            r'<div>Category:\s*<\/div>[\s\r]*<div>[\s\r]*<a href="\/videos\?c=[^>]*>([^<]*?)<\/a>',
            webpage,
            'categories', default=None)
        tags = re.findall(r'<a href="/results\?q=[^>]*>[\s]*([^<]*)</a>',
                          webpage) or None
        duration = int_or_none(
            self._html_search_meta('video:duration', webpage, 'duration',
                                   default=False)) or int_or_none(
            self._html_search_regex(
                r'videoInfo[^=]*=[^{]*{[^}]*dur:([^,}]*?),', webpage,
                'duration', default=None))
        view_count_fallback = re.findall(r'<strong>([^<]*?)</strong>',
                                         get_element_by_class("w_views",
                                                              webpage))
        view_count_fallback = view_count_fallback[
            0] if view_count_fallback else None
        view_count = int_or_none(self._html_search_regex(
            r'Views:[^<]*<strong>([^<]*?)<\/strong>', webpage,
            'view_count', default=None)) or int_or_none(
            view_count_fallback)

        comment_count = int_or_none(self._html_search_regex(
            r'Comments:[^<]*<strong>([^<]*?)<\/strong>', webpage,
            'comment_count', default=None)) or int_or_none(
            self._html_search_regex(
                r'<span[^>]+id="cmt_num"[^>]*>([^<]+?)<\/span>', webpage,
                'comment_count', default=None))
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
