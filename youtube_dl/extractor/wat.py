# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    ExtractorError,
    unified_strdate,
    HEADRequest,
    int_or_none,
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
            'md5': '34bdfa5ca9fd3c7eb88601b635b0424c',
            'info_dict': {
                'id': '11713075',
                'ext': 'mp4',
                'title': 'Grégory Lemarchal, une voix d\'ange depuis 10 ans (1/3)',
                'upload_date': '20140816',
            },
            'expected_warnings': ["Ce contenu n'est pas disponible pour l'instant."],
        },
    ]

    _FORMATS = (
        (200, 416, 234),
        (400, 480, 270),
        (600, 640, 360),
        (1200, 640, 360),
        (1800, 960, 540),
        (2500, 1280, 720),
    )

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_id = video_id if video_id.isdigit() and len(video_id) > 6 else compat_str(int(video_id, 36))

        # 'contentv4' is used in the website, but it also returns the related
        # videos, we don't need them
        video_data = self._download_json(
            'http://www.wat.tv/interface/contentv4s/' + video_id, video_id)
        video_info = video_data['media']

        error_desc = video_info.get('error_desc')
        if error_desc:
            self.report_warning(
                '%s returned error: %s' % (self.IE_NAME, error_desc))

        chapters = video_info['chapters']
        if chapters:
            first_chapter = chapters[0]

            def video_id_for_chapter(chapter):
                return chapter['tc_start'].split('-')[0]

            if video_id_for_chapter(first_chapter) != video_id:
                self.to_screen('Multipart video detected')
                entries = [self.url_result('wat:%s' % video_id_for_chapter(chapter)) for chapter in chapters]
                return self.playlist_result(entries, video_id, video_info['title'])
            # Otherwise we can continue and extract just one part, we have to use
            # the video id for getting the video url
        else:
            first_chapter = video_info

        title = first_chapter['title']

        def extract_url(path_template, url_type):
            req_url = 'http://www.wat.tv/get/%s' % (path_template % video_id)
            head = self._request_webpage(HEADRequest(req_url), video_id, 'Extracting %s url' % url_type, fatal=False)
            if head:
                red_url = head.geturl()
                if req_url != red_url:
                    return red_url
            return None

        def remove_bitrate_limit(manifest_url):
            return re.sub(r'(?:max|min)_bitrate=\d+&?', '', manifest_url)

        formats = []
        try:
            manifest_urls = self._download_json(
                'http://www.wat.tv/get/webhtml/' + video_id, video_id)
            m3u8_url = manifest_urls.get('hls')
            if m3u8_url:
                m3u8_url = remove_bitrate_limit(m3u8_url)
                m3u8_formats = self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
                if m3u8_formats:
                    formats.extend(m3u8_formats)
                    formats.extend(self._extract_f4m_formats(
                        m3u8_url.replace('ios', 'web').replace('.m3u8', '.f4m'),
                        video_id, f4m_id='hds', fatal=False))
                    http_url = extract_url('android5/%s.mp4', 'http')
                    if http_url:
                        for m3u8_format in m3u8_formats:
                            vbr, abr = m3u8_format.get('vbr'), m3u8_format.get('abr')
                            if not vbr or not abr:
                                continue
                            format_id = m3u8_format['format_id'].replace('hls', 'http')
                            fmt_url = re.sub(r'%s-\d+00-\d+' % video_id, '%s-%d00-%d' % (video_id, round(vbr / 100), round(abr)), http_url)
                            if self._is_valid_url(fmt_url, video_id, format_id):
                                f = m3u8_format.copy()
                                f.update({
                                    'url': fmt_url,
                                    'format_id': format_id,
                                    'protocol': 'http',
                                })
                                formats.append(f)
            mpd_url = manifest_urls.get('mpd')
            if mpd_url:
                formats.extend(self._extract_mpd_formats(remove_bitrate_limit(
                    mpd_url), video_id, mpd_id='dash', fatal=False))
            self._sort_formats(formats)
        except ExtractorError:
            abr = 64
            for vbr, width, height in self._FORMATS:
                tbr = vbr + abr
                format_id = 'http-%s' % tbr
                fmt_url = 'http://dnl.adv.tf1.fr/2/USP-0x0/%s/%s/%s/ssm/%s-%s-64k.mp4' % (video_id[-4:-2], video_id[-2:], video_id, video_id, vbr)
                if self._is_valid_url(fmt_url, video_id, format_id):
                    formats.append({
                        'format_id': format_id,
                        'url': fmt_url,
                        'vbr': vbr,
                        'abr': abr,
                        'width': width,
                        'height': height,
                    })

        date_diffusion = first_chapter.get('date_diffusion') or video_data.get('configv4', {}).get('estatS4')
        upload_date = unified_strdate(date_diffusion) if date_diffusion else None
        duration = None
        files = video_info['files']
        if files:
            duration = int_or_none(files[0].get('duration'))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': first_chapter.get('preview'),
            'description': first_chapter.get('description'),
            'view_count': int_or_none(video_info.get('views')),
            'upload_date': upload_date,
            'duration': duration,
            'formats': formats,
        }
