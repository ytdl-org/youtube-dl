# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    unified_strdate,
    HEADRequest,
)


class WatIE(InfoExtractor):
    _VALID_URL = r'(?:wat:|https?://(?:www\.)?wat\.tv/video/.*-)(?P<id>[0-9a-z]+)'
    IE_NAME = 'wat.tv'
    _TESTS = [
        {
            'url': 'http://www.wat.tv/video/soupe-figues-l-orange-aux-epices-6z1uz_2hvf7_.html',
            'md5': '83d882d9de5c9d97f0bb2c6273cde56a',
            'info_dict': {
                'id': '11713067',
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
                'ext': 'mp4',
                'title': 'Grégory Lemarchal, une voix d\'ange depuis 10 ans (1/3)',
                'description': 'md5:b7a849cf16a2b733d9cd10c52906dee3',
                'upload_date': '20140816',
                'duration': 2910,
            },
            'skip': "Ce contenu n'est pas disponible pour l'instant.",
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_id = video_id if video_id.isdigit() and len(video_id) > 6 else compat_str(int(video_id, 36))

        # 'contentv4' is used in the website, but it also returns the related
        # videos, we don't need them
        video_info = self._download_json(
            'http://www.wat.tv/interface/contentv3/' + video_id, video_id)['media']

        error_desc = video_info.get('error_desc')
        if error_desc:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error_desc), expected=True)

        chapters = video_info['chapters']
        first_chapter = chapters[0]

        def video_id_for_chapter(chapter):
            return chapter['tc_start'].split('-')[0]

        if video_id_for_chapter(first_chapter) != video_id:
            self.to_screen('Multipart video detected')
            entries = [self.url_result('wat:%s' % video_id_for_chapter(chapter)) for chapter in chapters]
            return self.playlist_result(entries, video_id, video_info['title'])
        # Otherwise we can continue and extract just one part, we have to use
        # the video id for getting the video url

        date_diffusion = first_chapter.get('date_diffusion')
        upload_date = unified_strdate(date_diffusion) if date_diffusion else None

        def extract_url(path_template, url_type):
            req_url = 'http://www.wat.tv/get/%s' % (path_template % video_id)
            head = self._request_webpage(HEADRequest(req_url), video_id, 'Extracting %s url' % url_type)
            red_url = head.geturl()
            if req_url == red_url:
                raise ExtractorError(
                    '%s said: Sorry, this video is not available from your country.' % self.IE_NAME,
                    expected=True)
            return red_url

        m3u8_url = extract_url('ipad/%s.m3u8', 'm3u8')
        http_url = extract_url('android5/%s.mp4', 'http')

        formats = []
        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls')
        formats.extend(m3u8_formats)
        formats.extend(self._extract_f4m_formats(
            m3u8_url.replace('ios.', 'web.').replace('.m3u8', '.f4m'),
            video_id, f4m_id='hds', fatal=False))
        for m3u8_format in m3u8_formats:
            vbr, abr = m3u8_format.get('vbr'), m3u8_format.get('abr')
            if not vbr or not abr:
                continue
            f = m3u8_format.copy()
            f.update({
                'url': re.sub(r'%s-\d+00-\d+' % video_id, '%s-%d00-%d' % (video_id, round(vbr / 100), round(abr)), http_url),
                'format_id': f['format_id'].replace('hls', 'http'),
                'protocol': 'http',
            })
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': first_chapter['title'],
            'thumbnail': first_chapter['preview'],
            'description': first_chapter['description'],
            'view_count': video_info['views'],
            'upload_date': upload_date,
            'duration': video_info['files'][0]['duration'],
            'formats': formats,
        }
