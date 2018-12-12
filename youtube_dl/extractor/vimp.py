# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    xpath_element,
    xpath_text,
)


class ViMPIE(InfoExtractor):
    _INSTANCES_RE = r'''(?:
                            vimp\.schwaebische\.de|
                            www\.videoportal\.uni-freiburg\.de|
                            k100186\.vimp\.mivitec\.net|
                            www\.hd-campus\.tv|
                            media\.hwr-berlin\.de|
                            vimp\.oth-regensburg\.de|
                            video\.irtshdf\.fr|
                            univideo\.uni-kassel\.de|
                            mediathek\.htw-berlin\.de|
                            hd-campus\.de|
                            medien\.hs-merseburg\.de|
                            www\.webdancetv\.com|
                            sign7tv\.com|
                            www\.salzburgtube\.at|
                            medienportal-polizei\.land-bw\.de|
                            www\.bn1\.tv|
                            video\.tanedo\.de|
                            www\.fh-bielefeld\.de/medienportal|
                            framework\.auvica\.net|
                            schanzer\.tv|
                            www\.salzi\.tv|
                            parrotfiles\.com|
                            bestvision\.tv|
                            www\.webtv\.coop|
                            www\.abruzzoinvideo\.tv|
                            www\.medien-tube\.de
                            print7tv\.com|
                            kanutube\.de|
                            www\.bigcitytv\.de|
                            www\.drehzahl\.tv|
                            ursula\.genetics\.emory\.edu|
                            www\.region-bergstrasse\.tv|
                            www2\.univ-sba\.dz|
                            videos\.uni-paderborn\.de

                        )'''
    _UUID_RE = r'[\da-f]{32}'
    _VALID_URL = r'''(?x)
                    (?:
                        vimp:(?P<secure>s?):(?P<host>[^:]+):|
                        http(?P<secure2>s?)://(?P<host2>%s)/(?:media/embed\?key=|(?:category/|channel/)?video/.+/)
                    )
                    (?P<media_key>%s)
                    ''' % (_INSTANCES_RE, _UUID_RE)
    _TESTS = [{
        'url': 'https://www.videoportal.uni-freiburg.de/video/Konzert-des-Akademischen-Orchesters-Freiburg/e2537c92d1d5ff61beba7ed5855c8f7e',
        'md5': '569c906738571d4e17cd91502720b981',
        'info_dict': {
            'id': '6030',
            'ext': 'mp4',
            'title': 'Konzert des Akademischen Orchesters Freiburg',
            'description': 'md5:da634544fde2c5b7556a129eb3c7674b',
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader': 'un0',
        }
    }, {
        'url': 'vimp::vimp.schwaebische.de:e72974cd8a604c8e9c8970d237f07bbf',
        'only_matching': True,
    }, {
        'url': 'https://univideo.uni-kassel.de/category/video/12-13-Bauer-et-al/57562e3ed05bc4d74896aa984d518cb1/10',
        'only_matching': True,
    }, {
        'url': 'https://univideo.uni-kassel.de/channel/video/Allgemeine-Chemie-vom-04122018/22bc28a5c2cf908cc6ad0f84c0368a89/27',
        'only_matching': True,
    }, {
        'url': 'http://vimp.schwaebische.de/media/embed?key=870a38f3dbd9ed10b4e1a1b189e3cf9f',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage, source_url):
        entries = re.findall(
            r'''(?x)<iframe[^>]+\bdata-src=["\'](?P<url>(?:https?:)?//%s/media/embed\?key=%s)'''
            % (ViMPIE._INSTANCES_RE, ViMPIE._UUID_RE), webpage)
        return entries

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        secure = mobj.group('secure') or mobj.group('secure2') or ''
        host = mobj.group('host') or mobj.group('host2')
        media_key = mobj.group('media_key')

        webpage = self._download_webpage(
            'http%s://%s/media/embed?key=%s' % (secure, host, media_key),
            media_key)
        sources = re.findall(
            r'addSource\(\'(?P<url>.+)\'\s*,\s*\'video/(?P<ext>.+)\'\)', webpage)
        if not sources:
            sources = re.findall(
                r'<source\s+src="(?P<url>.+)"\s+type="video/(?P<ext>.+)"\s*/>', webpage)

        formats = []
        height = int_or_none(
            self._search_regex(
                r'preSetVideoHeight\((\d+)\)', webpage,
                'height', default=None))
        width = int_or_none(
            self._search_regex(
                r'preSetVideoWidth\((\d+)\)', webpage,
                'width', default=None))
        for source in sources:
            formats.append({
                'url': source[0],
                'ext': source[1],
                'height': height,
                'width': width,
            })

        media_id = self._search_regex(
            r'(?:preSetCurrendID\((\d+)\)|mediaid=(\d+))', webpage, 'media id')

        media_info = self._download_xml(
            'http%s://%s/media/flashcomm?action=getmediainfo&context=normal&mediaid=%s' % (
                secure, host, media_id), media_id)
        media_path = './active_media/media'
        title = clean_html(
            xpath_text(media_info, '%s/title' % media_path, fatal=True))
        description = clean_html(
            xpath_text(media_info, '%s/description' % media_path))
        uploader = xpath_text(
            media_info, '%s/author' % media_path)
        url = xpath_text(
            media_info, '%s/file' % media_path)
        duration = int_or_none(
            xpath_text(media_info, '%s/duration_sec' % media_path))
        height = int_or_none(
            xpath_text(media_info, '%s/height' % media_path))
        width = int_or_none(
            xpath_text(media_info, '%s/width' % media_path))
        view_count = int_or_none(
            xpath_text(media_info, '%s/views' % media_path))
        thumbnail = xpath_text(
            media_info, '%s/previewpic' % media_path) or xpath_text(
                media_info, '%s/description_pic' % media_path)

        if url:
            formats.append({
                'url': url,
                'width': width,
                'height': height,
            })

        formats_info = self._download_xml(
            'http%s://%s/webplayer/flashcomm?action=getmediaformats&key=%s' % (
                secure, host, media_key),
            'media formats', fatal=False)
        if formats_info:
            format_params = []
            files = xpath_element(formats_info, './files')
            for f in files:
                fkey = xpath_text(f, './key')
                ftype = xpath_text(f, './type')
                if fkey and fkey != 'default' and ftype:
                    format_params.append(
                        {
                            'format': fkey,
                            'type': ftype,
                        })

            for fp in format_params:
                url = 'http%s://%s/getMedium/%s.%s?format=%s' % (
                    secure, host, media_key, fp['type'], fp['format'])
                formats.append(
                    {
                        'url': url,
                        'height': int_or_none(fp['format'].strip('p'))
                    })
        if not formats:
            formats.append({
                'url': 'http%s://%s/getMedia.php?key=%s&type=mp4' % (
                    secure, host, media_key),
                'ext': 'mp4',
            })

        self._sort_formats(formats)

        return {
            'id': media_id,
            'title': title,
            'uploader': uploader,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'formats': formats,
        }
