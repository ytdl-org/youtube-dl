# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import random


class AutoHomeIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/chejiahao\.autohome\.com\.cn\/info\/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://chejiahao.autohome.com.cn/info/2775092',
        'md5': 'addbf30e168433f5538b50f58965fc56',
        'info_dict': {
            'id': '2775092',
            'ext': 'mp4',
            'title': '宝马的8AT与马自达的6AT谁好！二手RX-8值得买吗？',
            'release_date': '2018-09-25',
            'description': '极速拍档第九期：买车还要看公司领导的喜好吗？'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<div class="title ">(.+?)</div>', webpage, 'title')
        description = self._html_search_regex(r'<div class="videoText">\s*<span>简介：</span>\s*<p class="text">(.+?)</p>\s*</div>', webpage, 'description')
        release_date = self._html_search_regex(r'<div class="articleTag">\s*(?:<span>.+?</span>\s*)(?:<span>.+?</span>\s*)(?:<span>(.+?)</span>\s*)</div>', webpage, 'release_date')
        vid = self._html_search_regex(r'vid: "(.+?)"', webpage, 'vid')

        def _call_api(self, mid, video_id):
            return self._download_json('http://p-vp.autohome.com.cn/api/gpi?mid=%s&ft=mp4&strategy=1&r=%s' % (
                mid, random.random()), video_id)
        url_dict = _call_api(self, vid, video_id)["result"]["media"]["qualities"]
        url = [url["copy"] for url in url_dict if url["value"] == 400][0]

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'description': description,
            'release_date': release_date
        }
