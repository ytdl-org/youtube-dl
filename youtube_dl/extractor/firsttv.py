# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    int_or_none,
    qualities,
    unified_strdate,
)


class FirstTVIE(InfoExtractor):
    IE_NAME = '1tv'
    IE_DESC = 'Первый канал'
    _VALID_URL = r'https?://(?:www\.)?1tv\.ru/(?:[^/]+/)+(?P<id>[^/?#]+)'

    _TESTS = [{
        # single format
        'url': 'http://www.1tv.ru/shows/naedine-so-vsemi/vypuski/gost-lyudmila-senchina-naedine-so-vsemi-vypusk-ot-12-02-2015',
        'md5': 'a1b6b60d530ebcf8daacf4565762bbaf',
        'info_dict': {
            'id': '40049',
            'ext': 'mp4',
            'title': 'Гость Людмила Сенчина. Наедине со всеми. Выпуск от 12.02.2015',
            'description': 'md5:36a39c1d19618fec57d12efe212a8370',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'upload_date': '20150212',
            'duration': 2694,
        },
    }, {
        # multiple formats
        'url': 'http://www.1tv.ru/shows/dobroe-utro/pro-zdorove/vesennyaya-allergiya-dobroe-utro-fragment-vypuska-ot-07042016',
        'info_dict': {
            'id': '364746',
            'ext': 'mp4',
            'title': 'Весенняя аллергия. Доброе утро. Фрагмент выпуска от 07.04.2016',
            'description': 'md5:a242eea0031fd180a4497d52640a9572',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'upload_date': '20160407',
            'duration': 179,
            'formats': 'mincount:3',
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        playlist_url = compat_urlparse.urljoin(url, self._search_regex(
            r'data-playlist-url="([^"]+)', webpage, 'playlist url'))

        item = self._download_json(playlist_url, display_id)[0]
        video_id = item['id']
        quality = qualities(('ld', 'sd', 'hd', ))
        formats = []
        for f in item.get('mbr', []):
            src = f.get('src')
            if not src:
                continue
            fname = f.get('name')
            formats.append({
                'url': src,
                'format_id': fname,
                'quality': quality(fname),
            })
        self._sort_formats(formats)

        title = self._html_search_regex(
            (r'<div class="tv_translation">\s*<h1><a href="[^"]+">([^<]*)</a>',
             r"'title'\s*:\s*'([^']+)'"),
            webpage, 'title', default=None) or item['title']
        description = self._html_search_regex(
            r'<div class="descr">\s*<div>&nbsp;</div>\s*<p>([^<]*)</p></div>',
            webpage, 'description', default=None) or self._html_search_meta(
            'description', webpage, 'description')
        duration = int_or_none(self._html_search_meta(
            'video:duration', webpage, 'video duration', fatal=False))
        upload_date = unified_strdate(self._html_search_meta(
            'ya:ovs:upload_date', webpage, 'upload date', fatal=False))

        return {
            'id': video_id,
            'thumbnail': item.get('poster') or self._og_search_thumbnail(webpage),
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'duration': int_or_none(duration),
            'formats': formats
        }
