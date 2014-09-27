# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    get_meta_content,
    parse_iso8601,
)


class HeiseIE(InfoExtractor):
    _VALID_URL = (
        r'^https?://(?:www\.)?heise\.de/video/artikel/' +
        r'.+?(?P<id>[0-9]+)\.html$'
    )
    _TEST = {
        'url': (
            'http://www.heise.de/video/artikel/Podcast-c-t-uplink-3-3-' +
            'Owncloud-Tastaturen-Peilsender-Smartphone-2404147.html'
        ),
        'md5': 'ffed432483e922e88545ad9f2f15d30e',
        'info_dict': {
            'id': '2404147',
            'ext': 'mp4',
            'title': (
                "Podcast: c't uplink 3.3 – Owncloud / Tastaturen / " +
                "Peilsender Smartphone"
            ),
            'format_id': 'mp4_720',
            'timestamp': 1411812600,
            'upload_date': '20140927',
        }
    }

    _CONFIG = (
        r'".+?\?sequenz=(?P<sequenz>.+?)&container=(?P<container>.+?)' +
        r'(?:&hd=(?P<hd>.+?))?(?:&signature=(?P<signature>.+?))?&callback=\?"'
    )
    _PREFIX = 'http://www.heise.de/videout/info?'

    def _warn(self, fmt, *args):
        self.report_warning(fmt.format(*args), self._id)

    def _parse_config_url(self, html):
        m = re.search(self._CONFIG, html)
        if not m:
            raise ExtractorError('No config found')

        qs = compat_urllib_parse.urlencode(dict((k, v) for k, v
                                                in m.groupdict().items()
                                                if v is not None))
        return self._PREFIX + qs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        self._id = mobj.group('id')

        html = self._download_webpage(url, self._id)
        config = self._download_json(self._parse_config_url(html), self._id)

        info = {
            'id': self._id
        }

        title = get_meta_content('fulltitle', html)
        if title:
            info['title'] = title
        elif config.get('title'):
            info['title'] = config['title']
        else:
            self._warn('title: not found')
            info['title'] = 'heise'

        if (not config.get('formats') or
                not hasattr(config['formats'], 'items')):
            raise ExtractorError('No formats found')

        formats = []
        for t, rs in config['formats'].items():
            if not rs or not hasattr(rs, 'items'):
                self._warn('formats: {0}: no resolutions', t)
                continue

            for res, obj in rs.items():
                format_id = '{0}_{1}'.format(t, res)

                if not obj or not obj.get('url'):
                    self._warn('formats: {0}: no url', format_id)
                    continue

                fmt = {
                    'url': obj['url'],
                    'format_id': format_id
                }
                try:
                    fmt['height'] = int(res)
                except ValueError as e:
                    self._warn('formats: {0}: height: {1}', t, e)

                formats.append(fmt)

        self._sort_formats(formats)
        info['formats'] = formats

        if config.get('poster'):
            info['thumbnail'] = config['poster']

        date = get_meta_content('date', html)
        if date:
            try:
                info['timestamp'] = parse_iso8601(date)
            except ValueError as e:
                self._warn('timestamp: {0}', e)

        return info
