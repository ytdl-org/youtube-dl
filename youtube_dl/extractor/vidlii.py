# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    get_element_by_id, get_element_by_class, strip_or_none,
    float_or_none, urljoin)


class VidliiIE(InfoExtractor):
    _VALID_URL = r'(?:https*?:\/\/)*(?:www\.)*vidlii.com\/watch\?v=(?P<id>[^?\s]{11})'
    _TESTS = [{
        'url': 'https://www.vidlii.com/watch?v=tJluaH4BJ3v',
        'md5': '9bf7d1e005dfa909b6efb0a1ff5175e2',
        'info_dict': {
            'id': 'tJluaH4BJ3v',
            'title': 'Vidlii is against me',
            'description': 'I have HAD it. Vidlii does not like me. I have tried to uplaod videos and submit them to the '
                           'contest and no ne of my videos show up so maybe it is broken for everyone else but this one was '
                           'trying to submit it because I wanted to submit to the contest :) Tanks I hope the website is '
                           'fixed PS: Jan you are cool please add my video',
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

        # extract basic properties of video
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title', default=None) or self._html_search_regex(
            r'<title>([^<]+?)</title>', webpage, 'title', default="").replace(
            " - VidLii", "") or self._html_search_meta('twitter:title', webpage, 'title',
                                                       default="").replace(" - VidLii", "")

        description = strip_or_none(get_element_by_id('des_text', webpage))

        uploader = self._html_search_regex(r'<div[^>]+class="wt_person"[^>]*>(?:[^<]+)<a href="\/user\/[^>]*?>([^<]*?)<',
                                           webpage, 'uploader', default=None) or self._html_search_regex(
            r'<img src="[^>]+?class=["\']avt2\s*["\'][^>]+?alt=["\']([^"\']+?)["\']',
            webpage, 'uploader', default=None)

        url = self._html_search_regex(r'videoInfo[\s]*=[\s]*{[^}]*src:[\s]*(?:"|\')([^"]*?)(?:"|\')', webpage, 'url',
                                      default=None)

        # get additional properties
        uploader_url = urljoin("https://www.vidlii.com/user/", uploader)

        # returns date as YYYYMMDD
        upload_date = self._html_search_meta('datePublished', webpage, 'upload_date', default="").replace("-", "")

        categories = self._html_search_regex(
            r'<div>Category:\s*<\/div>[\s\r]*<div>[\s\r]*<a href="\/videos\?c=[^>]*>([^<]*?)<\/a>', webpage, 'categories',
            default=None)
        tags = re.findall(r'<a href="/results\?q=[^>]*>[\s]*([^<]*)</a>', webpage) or None
        duration = int_or_none(self._html_search_meta('video:duration', webpage, 'duration', default=False)) or int_or_none(
            self._html_search_regex(r'videoInfo[^=]*=[^{]*{[^}]*dur:([^,}]*?),', webpage, 'duration', default=None))

        view_count_fb = re.findall(r'<strong>([^<]*?)</strong>', get_element_by_class("w_views", webpage))
        view_count_fb = view_count_fb[0] if view_count_fb else None
        view_count = int_or_none(self._html_search_regex(r'Views:[^<]*<strong>([^<]*?)<\/strong>', webpage, 'view_count',
                                                         default=None)) or int_or_none(view_count_fb)

        comment_count = int_or_none(
            self._html_search_regex(r'Comments:[^<]*<strong>([^<]*?)<\/strong>', webpage, 'comment_count',
                                    default=None) or
            self._html_search_regex(r'<span[^>]+id="cmt_num"[^>]*>([^<]+?)<\/span>', webpage, 'comment_count', default=None))

        average_rating = float_or_none(
            self._html_search_regex(r'{[\s\r]*\$\("#rateYo"\).rateYo\({[^}]*rating:\s*([^,]*?),[^}.]*}',
                                    webpage, 'average_rating', default=None))
        thumbnail_link = self._html_search_regex(r'videoInfo[\s]*=[\s]*{[^}]*img:[\s]*(?:"|\')([^"]*?)(?:"|\')', webpage,
                                                 'thumbnail', default=None)
        thumbnail = urljoin("https://www.vidlii.com/", thumbnail_link)
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
