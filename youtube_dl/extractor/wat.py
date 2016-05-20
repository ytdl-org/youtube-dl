# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    unified_strdate,
)


class WatIE(InfoExtractor):
    _VALID_URL = r'(?:wat:(?P<real_id>\d{8})|https?://www\.wat\.tv/video/(?P<display_id>.*)-(?P<short_id>.*?)_.*?\.html)'
    IE_NAME = 'wat.tv'
    _TESTS = [
        {
            'url': 'http://www.wat.tv/video/soupe-figues-l-orange-aux-epices-6z1uz_2hvf7_.html',
            'md5': 'ce70e9223945ed26a8056d413ca55dc9',
            'info_dict': {
                'id': '11713067',
                'display_id': 'soupe-figues-l-orange-aux-epices',
                'ext': 'mp4',
                'title': 'Soupe de figues à l\'orange et aux épices',
                'description': 'Retrouvez l\'émission "Petits plats en équilibre", diffusée le 18 août 2014.',
                'upload_date': '20140819',
                'duration': 120,
            },
        },
        {
            'url': 'http://www.wat.tv/video/gregory-lemarchal-voix-ange-6z1v7_6ygkj_.html',
            'md5': 'fbc84e4378165278e743956d9c1bf16b',
            'info_dict': {
                'id': '11713075',
                'display_id': 'gregory-lemarchal-voix-ange',
                'ext': 'mp4',
                'title': 'Grégory Lemarchal, une voix d\'ange depuis 10 ans (1/3)',
                'description': 'md5:b7a849cf16a2b733d9cd10c52906dee3',
                'upload_date': '20140816',
                'duration': 2910,
            },
            'skip': "Ce contenu n'est pas disponible pour l'instant.",
        },
    ]

    def download_video_info(self, real_id):
        # 'contentv4' is used in the website, but it also returns the related
        # videos, we don't need them
        info = self._download_json('http://www.wat.tv/interface/contentv3/' + real_id, real_id)
        return info['media']

    def _real_extract(self, url):
        def real_id_for_chapter(chapter):
            return chapter['tc_start'].split('-')[0]
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        real_id = mobj.group('real_id')
        if not real_id:
            short_id = mobj.group('short_id')
            webpage = self._download_webpage(url, display_id or short_id)
            real_id = self._search_regex(r'xtpage = ".*-(.*?)";', webpage, 'real id')

        video_info = self.download_video_info(real_id)

        error_desc = video_info.get('error_desc')
        if error_desc:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_desc), expected=True)

        chapters = video_info['chapters']
        first_chapter = chapters[0]
        files = video_info['files']
        first_file = files[0]

        if real_id_for_chapter(first_chapter) != real_id:
            self.to_screen('Multipart video detected')
            entries = [self.url_result('wat:%s' % real_id_for_chapter(chapter)) for chapter in chapters]
            return self.playlist_result(entries, real_id, video_info['title'])

        upload_date = None
        if 'date_diffusion' in first_chapter:
            upload_date = unified_strdate(first_chapter['date_diffusion'])
        # Otherwise we can continue and extract just one part, we have to use
        # the real id for getting the video url

        formats = [{
            'url': 'http://wat.tv/get/android5/%s.mp4' % real_id,
            'format_id': 'Mobile',
        }]
        formats.extend(self._extract_m3u8_formats(
            'http://wat.tv/get/ipad/%s.m3u8' % real_id,
            real_id, 'mp4', 'm3u8_native', m3u8_id='hls'))
        self._sort_formats(formats)

        return {
            'id': real_id,
            'display_id': display_id,
            'title': first_chapter['title'],
            'thumbnail': first_chapter['preview'],
            'description': first_chapter['description'],
            'view_count': video_info['views'],
            'upload_date': upload_date,
            'duration': first_file['duration'],
            'formats': formats,
        }
