# coding: utf-8
from __future__ import unicode_literals

import re

from ..utils import (
    int_or_none,
    get_element_by_id)
from .common import InfoExtractor


class VidliiIE(InfoExtractor):
    _VALID_URL = r'(?:https*?:\/\/)*(?:www\.)*vidlii.com\/watch\?v=(?P<id>[^?\s]{11})'
    _TEST = {
        'url': 'https://yourextractor.com/watch/42',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        # get required video properties
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')
        description = get_element_by_id('des_text', webpage).strip()
        uploader = self._html_search_regex(
            r'<div[^>]+class="wt_person"[^>]*>(?:[^<]+)<a href="\/user\/[^>]*?>([^<]*?)<', webpage, 'uploader')
        url = self._html_search_regex(r'videoInfo[\s]*=[\s]*{[^}]*src:[\s]*(?:"|\')([^"]*?)(?:"|\')', webpage, 'url')

        # get additional properties
        uploader_url = "https://www.vidlii.com/user/%s" % uploader
        upload_date = self._html_search_meta('datePublished', webpage, 'upload_date', default=False).replace('-', '')
        categories = self._html_search_regex(
            r'<div>Category:\s*<\/div>[\s\r]*<div>[\s\r]*<a href="\/videos\?c=[^>]*>([^<]*?)<\/a>', webpage,
            'categories')
        tags = re.findall(r'<a href="/results\?q=[^>]*>[\s]*([^<]*)</a>', webpage)
        duration = int_or_none(self._html_search_meta('video:duration', webpage, 'duration', default=False))
        view_count = int_or_none(
            self._html_search_regex(r'<div[^>]+class="w_views"[^>]*><strong>([^<]+?)<\/strong>', webpage,
                                    'view_count'))
        comment_count = int_or_none(self._html_search_regex(r'<span[^>]+id="cmt_num"[^>]*>([^<]+?)<\/span>', webpage,
                                                            'comment_count'))
        average_rating = int_or_none(
            self._html_search_regex(r'{[\s\r]*\$\("#rateYo"\).rateYo\({[^}]*rating:\s*([0-9]*?),[^}]*}',
                                    webpage, 'average_rating'))
        thumbnail_link = self._html_search_regex(r'videoInfo[\s]*=[\s]*{[^}]*img:[\s]*(?:"|\')([^"]*?)(?:"|\')',
                                                 webpage, 'thumbnail')
        thumbnail = 'https://www.vidlii.com%s' % thumbnail_link
        type = self._og_search_property('type', webpage, 'type')

        # use youtube-dl --print-json to show extracted metadata or debugger (watch value)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'url': url,
            'uploader_url': uploader_url,
            'upload_date': upload_date,  # should we use release_date instead?
            'categories': categories,
            'tags': tags,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'average_rating': average_rating,
            'thumbnail': thumbnail,
            'type': type
        }
