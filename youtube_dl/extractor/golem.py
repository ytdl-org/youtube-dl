# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import compat_urlparse


class GolemIE(InfoExtractor):
    _VALID_URL = r'^https?://video\.golem\.de/.+?/(?P<id>.+?)/'
    _TEST = {
        'url': 'http://video.golem.de/handy/14095/iphone-6-und-6-plus-test.html',
        'md5': 'c1a2c0a3c863319651c7c992c5ee29bf',
        'info_dict': {
            'id': '14095',
            'format_id': 'high',
            'ext': 'mp4',
            'title': 'iPhone 6 und 6 Plus - Test',
            'duration': 300,
            'filesize': 65309548,
        }
    }

    _CONFIG = 'https://video.golem.de/xml/{0}.xml'
    _PREFIX = 'http://video.golem.de'

    def _warn(self, fmt, *args):
        self.report_warning(fmt.format(*args), self._id)

    def _extract_format(self, elem):
        format_id = elem.tag

        url = elem.findtext('./url')
        if url == '':
            self._warn("{0}: url: empty, skipping", format_id)
            return None

        fmt = {
            'format_id': format_id,
            'url': compat_urlparse.urljoin(self._PREFIX, url)
        }

        try:
            _, ext = elem.findtext('./filename', '').rsplit('.', 1)
        except ValueError:
            self._warn('{0}: ext: missing extension', format_id)
        else:
            fmt['ext'] = ext

        filesize = elem.findtext('./filesize')
        if filesize is not None:
            try:
                fmt['filesize'] = int(filesize)
            except ValueError as e:
                self._warn('{0}: filesize: {1}', format_id, e)

        width = elem.get('width')
        if width is not None:
            try:
                fmt['width'] = int(width)
            except ValueError as e:
                self._warn('{0}: width: {1}', format_id, e)

        height = elem.get('height')
        if height is not None:
            try:
                fmt['height'] = int(height)
            except ValueError as e:
                self._warn('{0}: height: {1}', format_id, e)

        return fmt

    def _extract_thumbnail(self, elem):
        url = elem.findtext('./url')
        if url == '':
            return None
        thumb = {
            'url': compat_urlparse.urljoin(self._PREFIX, url)
        }

        width = elem.get('width')
        if width is not None:
            try:
                thumb['width'] = int(width)
            except ValueError as e:
                self._warn('thumbnail: width: {0}', e)

        height = elem.get('height')
        if height is not None:
            try:
                thumb['height'] = int(height)
            except ValueError as e:
                self._warn('thumbnail: height: {0}', e)

        return thumb

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        self._id = mobj.group('id')

        config = self._download_xml(self._CONFIG.format(self._id), self._id)

        info = {
            'id': self._id,
            'title': config.findtext('./title', 'golem')
        }

        formats = []
        for e in config.findall('./*[url]'):
            fmt = self._extract_format(e)
            if fmt is not None:
                formats.append(fmt)
        self._sort_formats(formats)
        info['formats'] = formats

        thumbnails = []
        for e in config.findall('.//teaser[url]'):
            thumb = self._extract_thumbnail(e)
            if thumb is not None:
                thumbnails.append(thumb)
        info['thumbnails'] = thumbnails

        playtime = config.findtext('./playtime')
        if playtime is not None:
            try:
                info['duration'] = round(float(playtime))
            except ValueError as e:
                self._warn('duration: {0}', e)

        return info
