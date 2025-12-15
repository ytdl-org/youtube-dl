# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    extract_attributes,
    float_or_none,
    get_element_by_attribute,
    int_or_none,
    parse_iso8601,
    strip_or_none,
    urljoin,
)


class SwitchTubeIE(InfoExtractor):
    _VALID_URL = r'https?://tube\.switch\.ch/videos/(?P<id>[\da-zA-Z]+)'
    IE_NAME = 'switchtube'
    _TESTS = [{
        'url': 'https://tube.switch.ch/videos/0T1XfaIFSX',
        'info_dict': {
            'id': '0T1XfaIFSX',
            'title': '2016_ASE_sqC03-Entretien',
            'channel': 'ASE Assistant-e socio-éducatif-ve CFC',
            'channel_url': 'https://tube.switch.ch/channels/bsaer76yoL',
            'channel_id': 'bsaer76yoL',
            'ext': 'mp4',
            'description': None,
            'thumbnail': r're:^https?://tube.switch.ch/image/representations/[\w-]+$',
            'license': 'All rights reserved',
            'creator': 'Jean-Marc Pouly from Eidgenössische Hochschule für Berufsbildung',
            'uploader': 'Jean-Marc Pouly from Eidgenössische Hochschule für Berufsbildung',
            'uploader_url': 'https://tube.switch.ch/profiles/42481',
            'uploader_id': '42481',
            'upload_date': '20220309',
            'timestamp': 1646839068,
        }
    }, {
        'url': 'https://tube.switch.ch/videos/0cf3886d',
        'info_dict': {
            'id': '0cf3886d',
            'ext': 'mp4',
            'title': 'Introduction: Mini-Batches in On- and Off-Policy Deep Reinforcement Learning',
            'license': 'All rights reserved',
            'description': 'One of the challenges in Deep Reinforcement Learning is to decorrelate the data. How this is possible with replay buffers is explained here.',
            'thumbnail': r're:^https?://tube.switch.ch/image/representations/[\w-]+$',
            'channel': 'CS-456 Artificial Neural Networks',
            'channel_url': 'https://tube.switch.ch/channels/1deb03e0',
            'channel_id': '1deb03e0',
            'timestamp': 1590733406,
            'upload_date': '20200529',
            'creator': 'Wulfram Gerstner from École polytechnique fédérale de Lausanne (EPFL)',
            'uploader': 'Wulfram Gerstner from École polytechnique fédérale de Lausanne (EPFL)',
            'uploader_url': 'https://tube.switch.ch/profiles/94248',
            'uploader_id': '94248',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'(?s)<title\b[^>]*>(.+?)</title>', webpage, 'title')

        info = {
            'id': video_id,
            'title': title,
            'is_live': False,
        }

        info['view_count'] = int_or_none(self._html_search_regex(r'(?s)<p\b[^>]*>\s*(\d+)\s+views?\s*</p>', webpage,
                                                                 'view_count', default=None))
        info['license'] = self._html_search_regex(r'''(?s)<span\b[^>]*?\bproperty\s*=\s*["'](?:\b[cd]c:license\b\s*){2,}[^>]+>(.+)</span>''',
                                                  webpage, 'license', default=None)
        info['description'] = strip_or_none(clean_html(
            get_element_by_attribute('property', 'dc:description', webpage)))
        info['duration'] = float_or_none(
            self._search_regex(r'''\bdata-duration\s*=\s*["']([\d.]+)''',
                               webpage, 'duration', default=None))

        channel_groups = self._search_regex(r'''(?s)<a\b[^>]+?\bhref\s*=\s*["']/channels/(.{4,}?)</a>''',
                                            webpage, 'channel groups', default='')
        channel_groups = re.split(r'''(?s)["'][^>]*>\s*''', channel_groups, 1)
        if len(channel_groups) == 2:
            for i, ch in enumerate(('channel_id', 'channel')):
                info[ch] = strip_or_none(channel_groups[i])
            if info['channel_id']:
                info['channel_url'] = 'https://tube.switch.ch/channels/' + info['channel_id']

        def outer_elements_by_attribute(attr, value, html, tag=None, escape_value=True, include_inner=False):
            """generate matching HTML element strings
               if include_inner, tuples of (element, content)"""
            pattern = r'''(?s)(?P<element><(%s)\b[^>]+?\b%s\s*=\s*("|')%s\b[^>]+>)(?P<inner>.*?)</\2>''' % \
                (re.escape(tag) if tag is not None else r'\w+', attr, re.escape(value) if escape_value else value)
            matches = re.finditer(pattern, html)
            for m in matches:
                yield m.group('element', 'inner') if include_inner else m.group('element')

        for dt in outer_elements_by_attribute('property', 'dc:date', webpage, tag='span'):
            dt = extract_attributes(dt)
            if dt.get('class') == 'dt-published':
                info['timestamp'] = parse_iso8601(dt.get('content'))
                break

        creator_groups = self._search_regex(
            r'''(?s)<span\b[^>]+?\bclass\s*=\s*("|')(?:(?!\1).)*\bp-author\b(?:(?!\1).)*\1\s*property\s*=\s*["']dc:creator\b[^>]+>\s*(.*?<span\b[^>]+?\bclass\s*=\s*["']p-name\b.*</span>).*?</span>''',
            webpage, 'creator groups', default='', group=2)
        creator_groups = re.match(r'''(?s)<a\b[^>]+?\bhref\s*=\s*("|')/profiles/(?P<profile_id>.+?)\1[^>]*>\s*<span\b[^>]+>\s*(?P<creator_name>.+?)\s*</span>[,\s]*<span\b[^>]+\bclass\s*=\s*["']p-organization-name\b[^>]+>\s*(?P<organization_name>.+?)\s*</span>''', creator_groups)
        if creator_groups:
            creator_groups = creator_groups.groupdict()
            info['uploader'] = info['creator'] = ' from '.join((creator_groups['creator_name'], creator_groups['organization_name']))
            info['uploader_id'] = creator_groups['profile_id']
            info['uploader_url'] = 'https://tube.switch.ch/profiles/' + info['uploader_id']

        parsed_media_entries = self._parse_html5_media_entries(url, webpage, video_id)[0]
        info['thumbnail'] = parsed_media_entries['thumbnail']
        info['formats'] = parsed_media_entries['formats']
        self._sort_formats(info['formats'])

        return info


class SwitchTubeProfileIE(InfoExtractor):
    _VALID_URL = r'https?://tube\.switch\.ch/profiles/(?P<id>[\da-zA-Z]+)'
    IE_NAME = 'switchtube:profile'
    _TESTS = [{
        'url': 'https://tube.switch.ch/profiles/94248',
        'info_dict': {
            'id': '94248',
            'title': 'Wulfram Gerstner',
            'description': None,
        },
        'playlist_mincount': 94,
    }]

    @classmethod
    def suitable(cls, url):
        return False if SwitchTubeIE.suitable(url) else super(SwitchTubeProfileIE, cls).suitable(url)

    def _real_extract(self, url):
        channel_id = self._match_id(url)
        webpage = self._download_webpage(url, channel_id)
        channel_title = self._html_search_regex(r'(?s)<title\b[^>]*>(.+?)</title>', webpage, 'title', default=None)

        description = self._html_search_regex(r'''(?s)<div\b[^>]+class\s*=\s*("|')p-summary formatted\1[^>]+property\s*=\s*("|')dc:description\2[^>]*>\s*(.+?)\s*</div>''',
                                              webpage, 'description', default=None, group=3)

        entries = []
        next_page = None
        for current_page_number in itertools.count(1):
            if next_page:
                webpage = self._download_webpage(next_page, channel_id, note='Downloading page %d' % (current_page_number, ))

            for _, video_path, video_id, title in re.findall(
                    r'''(?s)<a\b[^>]+\bhref\s*=\s*("|')(/videos/((?:(?!\1).)+?))\1[^>]*>\s*<div\b[^>]+\bclass\s*=\s*["']title\b[^>]+>(.+?)</div>''',
                    webpage):
                video_url = urljoin(url, video_path)
                if video_url:
                    entries.append(self.url_result(video_url, ie=SwitchTubeIE.ie_key(), video_id=video_id))

            next_page = self._search_regex(
                r'''<a\b[^>]+?\bhref\s*=\s*("|')(?P<path>/profiles/%s\?(?:(?!\1).)+)\1[^>]*>\s*Next\s*</a>''' % (channel_id,),
                webpage, 'next page', group='path', default=None)
            if next_page:
                next_page = urljoin(url, next_page)
            if not next_page:
                break

        return self.playlist_result(entries, channel_id, channel_title,
                                    description)


class SwitchTubeChannelIE(InfoExtractor):
    _VALID_URL = r'https?://tube\.switch\.ch/channels/(?P<id>[\da-zA-Z]+)'
    IE_NAME = 'switchtube:channel'
    _TESTS = [{
        'url': 'https://tube.switch.ch/channels/1deb03e0',
        'info_dict': {
            'id': '1deb03e0',
            'title': 'CS-456 Artificial Neural Networks',
            'description': 'Class on Artificial Neural Networks and Reinforcement Learning designed for EPFL master students in CS and related disciplines.'
        },
        'playlist_mincount': 94,
    }]

    @classmethod
    def suitable(cls, url):
        return False if SwitchTubeIE.suitable(url) else super(SwitchTubeChannelIE, cls).suitable(url)

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        entries = []
        for current_page_number in itertools.count(0):
            page_url = urljoin(url, '/channels/%s?order=episodes&page=%d' % (channel_id, current_page_number))
            webpage = self._download_webpage(page_url, channel_id, note='Downloading page %d' % (current_page_number + 1, ))

            if current_page_number == 0:
                channel_title = self._html_search_regex(r'(?s)<title\b[^>]*>(.+?)</title>', webpage, 'title', default=None)
                description = self._html_search_regex(r'''(?s)<div\b[^>]+class\s*=\s*("|')description formatted\1[^>]*>\s*<p>\s*(.+?)\s*</p>\s*</div>''',
                                                      webpage, 'description', default=None, group=2)

            this_page_still_has_something = False
            for _, video_path, video_id in re.findall(
                    r'''(?s)<a\b[^>]+\bhref\s*=\s*("|')(/videos/((?:(?!\1).)+?))\1[^>]*>''',
                    webpage):
                video_url = urljoin(url, video_path)
                if video_url:
                    this_page_still_has_something = True
                    entries.append(self.url_result(video_url, ie=SwitchTubeIE.ie_key(), video_id=video_id))

            if not this_page_still_has_something:
                break

        return self.playlist_result(entries, channel_id, channel_title,
                                    description)
