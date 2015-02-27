# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from .common import InfoExtractor

import re


class Puls4IE(InfoExtractor):

    _VALID_URL = r'https?://www.puls4.com/video/.+?/play/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.puls4.com/video/pro-und-contra/play/2716816',
        'md5': '49f6a6629747eeec43cef6a46b5df81d',
        'info_dict': {
            'id': '2716816',
            'ext': 'mp4',
            'title': 'Pro und Contra vom 23.02.2015'}},
        {
        'url': 'http://www.puls4.com/video/kult-spielfilme/play/1298106',
        'md5': '6a48316c8903ece8dab9b9a7bf7a59ec',
        'info_dict': {
            'id': '1298106',
            'ext': 'mp4',
            'title': 'Lucky Fritz'}}
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # if fsk-button
        real_url = self._html_search_regex(r'\"fsk-button\".+?href=\"([^"]+)',
                                           webpage, 'fsk_button', default=None)
        if real_url:
            webpage = self._download_webpage(real_url, video_id)

        title = self._html_search_regex(
            r'<div id="bg_brandableContent">.+?<h1>(.+?)</h1>',
            webpage, 'title', flags=re.DOTALL)

        sd_url = self._html_search_regex(
            r'{\"url\":\"([^"]+?)\",\"hd\":false',
            webpage, 'sd_url').replace('\\', '')

        formats = [{'format_id': 'sd', 'url': sd_url, 'quality': -2}]

        hd_url = self._html_search_regex(
            r'{\"url\":\"([^"]+?)\",\"hd\":true',
            webpage, 'hd_url', default=None)
        if hd_url:
            hd_url = hd_url.replace('\\', '')
            formats.append({'format_id': 'hd', 'url': hd_url, 'quality': -1})

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'ext': 'mp4'
        }
