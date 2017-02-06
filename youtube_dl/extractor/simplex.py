# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    str_or_none,
    try_get,
    urljoin,
)


class SimplexIE(InfoExtractor):
    IE_DESC = 'Simplex Player'
    _VALID_URL = r'''(?x)
                simplex:
                (?P<server_url>https?://(?:www\.)?.+):
                (?P<customer_id>\d+):
                (?P<author_id>\d+):
                (?P<project_id>\d+)
                '''

    _TEST = {
        'url': 'simplex:http://video.telebasel.ch:4062:4063:62349',
        'only_matching': True,
    }

    @staticmethod
    def _extract_urls(webpage):
        return ['simplex:%s:%s:%s:%s' % (
                m.group('server_url'), m.group('customer_id'),
                m.group('author_id'), m.group('project_id'))
                for m in re.finditer(r'<iframe[^>]+src=["\']%s.+["\']' % SimplexHostsIE._VALID_URL, webpage)]

    @staticmethod
    def _extract_width_height(resolution):
        try:
            w, h = resolution.split('x')
            w = int_or_none(w)
            h = int_or_none(h)
            return w, h
        except (AttributeError, ValueError):
            return None, None

    def _known_simplex_format(self, simplex_formats, fid):
        for sf in simplex_formats:
            if type(sf['id']) == str and sf['id'] == fid:
                return sf
            elif type(sf['id']) == list and fid in sf['id']:
                return sf
        return None

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        server_url = mobj.group('server_url')
        customer_id = mobj.group('customer_id')
        author_id = mobj.group('author_id')
        project_id = mobj.group('project_id')
        video_id = '%s-%s-%s' % (customer_id, author_id, project_id)

        content_url = urljoin(
            server_url,
            'content/%s/%s/%s/' % (customer_id, author_id, project_id))

        player_data = self._download_json(
            urljoin(content_url, 'data.sid'),
            video_id,
            note='Downloading player data JSON',
            errnote='Unable to download player data JSON')
        video_data = self._download_json(
            urljoin(content_url, 'pl01.sid'),
            video_id,
            note='Downloading video data JSON',
            errnote='Unable to download video data JSON',
            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        title = str_or_none(player_data['title'])
        description = str_or_none(player_data.get('description'))
        timestamp = int_or_none(player_data.get('createDate'))
        language = str_or_none(player_data.get('language'))
        duration = float_or_none(player_data.get('duration'), scale=10)

        file_information = try_get(video_data, lambda x: x['data'], dict)
        if not file_information:
            raise ExtractorError('Cannot extract file information data.')

        filename = str_or_none(file_information.get('filename'))
        thumbname = str_or_none(file_information.get('thumb'))
        thumbnail = urljoin(content_url, thumbname + '.jpg') if thumbname else None

        qualities = try_get(player_data, lambda x: x['qualities'], list)
        if not qualities:
            raise ExtractorError('Cannot find available formats.')

        # simplex_formats is the list of known simplex player formats.
        # There might be some more format ids, but we are not sure, what they do:
        # id 400: It was indicated to be for Apple TV.
        # id 500: No additional information found.
        simplex_formats = [
            {'id': '20', 'filename': filename + '.flv', 'method': 'url'},
            {'id': '40', 'filename': filename + '_40.flv', 'method': 'url'},
            {'id': '200', 'filename': filename + '.mp4', 'method': 'url'},
            {'id': ['300', '350', '355', '360'], 'filename': 'index.m3u8', 'method': 'm3u8'},
        ]

        formats = []

        m3u8_done = False
        format_infos = []
        for quali in qualities:
            fid = str_or_none(quali.get('id'))

            vbr = int_or_none(quali.get('b'))
            resolution = str_or_none(quali.get('s'))
            width, height = SimplexIE._extract_width_height(resolution)
            form_info = {
                'resolution': resolution,
                'width': width,
                'height': height,
                'vbr': vbr,
                'abr': int_or_none(quali.get('ab')),
                'asr': int_or_none(quali.get('ar')),
                'fps': int_or_none(quali.get('r')),
                'language': language,
                'format_id': 'hls-%s' % str_or_none(vbr)
            }
            format_infos.append(form_info)

            simplex_format = self._known_simplex_format(simplex_formats, fid)
            if simplex_format:
                format_url = urljoin(content_url, simplex_format['filename'])
                if simplex_format['method'] == 'url':
                    form = {
                        'url': format_url
                    }
                    form.update(form_info)
                    formats.append(form)
                elif simplex_format['method'] == 'm3u8' and not m3u8_done:
                    forms = self._extract_m3u8_formats(
                        format_url,
                        video_id,
                        ext='mp4',
                        entry_protocol='m3u8_native')
                    formats.extend(forms)
                    m3u8_done = True

        # Try to add additional information to the formats exracted by _extract_m3u8_formats:
        for form in formats:
            if form['url'].endswith('.m3u8'):
                vbr = int_or_none(
                    self._search_regex(r'(\d+)kb.m3u8', form['url'], 'm3u8 vbr', default=None))
                if vbr:
                    try:
                        form_info = next(f for f in format_infos if f['vbr'] == vbr)
                        form.update(form_info)
                    except StopIteration:
                        pass

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'formats': formats,
        }


class SimplexHostsIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                (?P<server_url>https?://(?:www\.)?
                    (?:
                        video\.telebasel\.ch|
                        media10\.simplex\.tv
                    )
                )
                /content/
                (?P<customer_id>\d+)/
                (?P<author_id>\d+)/
                (?P<project_id>\d+)
                '''

    _TESTS = [{
        'url': 'http://media10.simplex.tv/content/906/907/76997/',
        'md5': 'e6b8ebefac5aeae4a6790fec18382ca0',
        'info_dict': {
            'id': '906-907-76997',
            'ext': 'flv',
            'title': '03.02.17: Der Trailer zum Rückrunden-Start',
            'description': None,
            'duration': 44.0,
            'timestamp': 1486135964,
            'upload_date': '20170203',
            'url': 'http://media10.simplex.tv/content/906/907/76997/simvid_1_40.flv',
            'thumbnail': 'http://media10.simplex.tv/content/906/907/76997/simvid_1.jpg',
            'language': 'de',
            'width': 1280,
            'height': 720,
            'vbr': 2304,
            'abr': 160,
            'fps': 25,
            'asr': 44100,
            'resolution': '1280x720'
        }
    }, {
        'url': 'https://video.telebasel.ch/content/4062/4063/77067',
        'info_dict': {
            'id': '4062-4063-77067',
            'ext': 'flv',
            'title': 'News vom 05.02.2017',
            'description': 'md5:23fb960068621263d5d4418996387674',
            'timestamp': 1486314961,
            'upload_date': '20170205',
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        server_url = mobj.group('server_url')
        customer_id = mobj.group('customer_id')
        author_id = mobj.group('author_id')
        project_id = mobj.group('project_id')

        video_id = '%s-%s-%s' % (customer_id, author_id, project_id)
        simplex_url = 'simplex:%s:%s:%s:%s' % (server_url, customer_id, author_id, project_id)

        return self.url_result(
            simplex_url,
            ie=SimplexIE.ie_key(),
            video_id=video_id)
