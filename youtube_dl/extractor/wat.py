# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
)


class WatIE(InfoExtractor):
    _VALID_URL = r'http://www\.wat\.tv/.*-(?P<shortID>.*?)_.*?\.html'
    IE_NAME = 'wat.tv'
    _TEST = {
        'url': 'http://www.wat.tv/video/world-war-philadelphia-vost-6bv55_2fjr7_.html',
        'info_dict': {
            'id': '10631273',
            'ext': 'mp4',
            'title': 'World War Z - Philadelphia VOST',
            'description': 'La menace est partout. Que se passe-t-il à Philadelphia ?\r\nWORLD WAR Z, avec Brad Pitt, au cinéma le 3 juillet.\r\nhttp://www.worldwarz.fr',
        },
        'params': {
            # Sometimes wat serves the whole file with the --test option
            'skip_download': True,
        },
    }

    def download_video_info(self, real_id):
        # 'contentv4' is used in the website, but it also returns the related
        # videos, we don't need them
        info = self._download_json('http://www.wat.tv/interface/contentv3/' + real_id, real_id)
        return info['media']

    def _real_extract(self, url):
        def real_id_for_chapter(chapter):
            return chapter['tc_start'].split('-')[0]
        mobj = re.match(self._VALID_URL, url)
        short_id = mobj.group('shortID')
        webpage = self._download_webpage(url, short_id)
        real_id = self._search_regex(r'xtpage = ".*-(.*?)";', webpage, 'real id')

        video_info = self.download_video_info(real_id)
        chapters = video_info['chapters']
        first_chapter = chapters[0]

        if real_id_for_chapter(first_chapter) != real_id:
            self.to_screen('Multipart video detected')
            chapter_urls = []
            for chapter in chapters:
                chapter_id = real_id_for_chapter(chapter)
                # Yes, when we this chapter is processed by WatIE,
                # it will download the info again
                chapter_info = self.download_video_info(chapter_id)
                chapter_urls.append(chapter_info['url'])
            entries = [self.url_result(chapter_url) for chapter_url in chapter_urls]
            return self.playlist_result(entries, real_id, video_info['title'])

        upload_date = None
        if 'date_diffusion' in first_chapter:
            upload_date = unified_strdate(first_chapter['date_diffusion'])
        # Otherwise we can continue and extract just one part, we have to use
        # the short id for getting the video url
        return {
            'id': real_id,
            'url': 'http://wat.tv/get/android5/%s.mp4' % real_id,
            'title': first_chapter['title'],
            'thumbnail': first_chapter['preview'],
            'description': first_chapter['description'],
            'view_count': video_info['views'],
            'upload_date': upload_date,
        }
