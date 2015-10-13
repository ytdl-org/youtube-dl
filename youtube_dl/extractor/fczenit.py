# coding: utf-8
from __future__ import unicode_literals

import os.path
import re
import json

from ..compat import compat_urllib_parse_unquote
from ..utils import url_basename
from .common import InfoExtractor

class fczenitIE(InfoExtractor):
    _VALID_URL = r'(?:https?://(?:www\.)?fc-zenit\.ru/video/gl(?P<id>[0-9]+))'
    _TEST = {
    u'url': u'http://fc-zenit.ru/video/gl6785/',
    u'md5' : '458bacc24549173fe5a5aa29174a5606',
    u'info_dict': {
        u"id": u"6785",
        u"ext": u"mp4",
        u"title": u"«Зенит-ТВ»: как Олег Шатов играл против «Урала»"
    }
}


    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage_url = 'http://fc-zenit.ru/video/gl' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        video_title = self._html_search_regex(r'<div class=\"photoalbum__title\">([^<]+)', webpage, u"title")

        # Log that we are starting to parse the page
        self.report_extraction(video_id)

        bitrates_raw = self._html_search_regex(r'bitrates:.*\n(.*)\]', webpage, u'video URL')
        bitrates = re.findall(r'url:.?\'(.+?)\'.*?bitrate:.?([0-9]{3}?)', bitrates_raw)

        formats = [{
                "url" : sources[0],
                "tbr": sources[1]
        } for sources in bitrates]

        self._sort_formats(formats)

        return {
            'id' : video_id,
            'title' : video_title,
            'url' : webpage_url,
            'ext' : u'mp4',
            'formats' : formats
        }
