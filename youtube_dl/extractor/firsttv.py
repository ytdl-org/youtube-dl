# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
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
            'title': 'Гость Людмила Сенчина. Наедине со всеми. Выпуск от 12.02.2015',
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
            'title': 'Весенняя аллергия. Доброе утро. Фрагмент выпуска от 07.04.2016',
            'thumbnail': 're:^https?://.*\.(?:jpg|JPG)$',
            'upload_date': '20160407',
            'duration': 179,
            'formats': 'mincount:3',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://www.1tv.ru/news/issue/2016-12-01/14:00',
        'info_dict': {
            'id': '14:00',
            'title': 'Выпуск новостей в 14:00   1 декабря 2016 года. Новости. Первый канал',
            'description': 'md5:2e921b948f8c1ff93901da78ebdb1dfd',
        },
        'playlist_count': 13,
    }, {
        'url': 'http://www.1tv.ru/shows/tochvtoch-supersezon/vystupleniya/evgeniy-dyatlov-vladimir-vysockiy-koni-priveredlivye-toch-v-toch-supersezon-fragment-vypuska-ot-06-11-2016',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)
        playlist_url = compat_urlparse.urljoin(url, self._search_regex(
            r'data-playlist-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'playlist url', group='url'))

        parsed_url = compat_urlparse.urlparse(playlist_url)
        qs = compat_urlparse.parse_qs(parsed_url.query)
        item_ids = qs.get('videos_ids[]') or qs.get('news_ids[]')

        items = self._download_json(playlist_url, display_id)

        if item_ids:
            items = [
                item for item in items
                if item.get('uid') and compat_str(item['uid']) in item_ids]
        else:
            items = [items[0]]

        entries = []
        QUALITIES = ('ld', 'sd', 'hd', )

        for item in items:
            title = item['title']
            quality = qualities(QUALITIES)
            formats = []
            for f in item.get('mbr', []):
                src = f.get('src')
                if not src or not isinstance(src, compat_str):
                    continue
                tbr = int_or_none(self._search_regex(
                    r'_(\d{3,})\.mp4', src, 'tbr', default=None))
                formats.append({
                    'url': src,
                    'format_id': f.get('name'),
                    'tbr': tbr,
                    'quality': quality(f.get('name')),
                })
            self._sort_formats(formats)

            thumbnail = item.get('poster') or self._og_search_thumbnail(webpage)
            duration = int_or_none(item.get('duration') or self._html_search_meta(
                'video:duration', webpage, 'video duration', fatal=False))
            upload_date = unified_strdate(self._html_search_meta(
                'ya:ovs:upload_date', webpage, 'upload date', default=None))

            entries.append({
                'id': compat_str(item.get('id') or item['uid']),
                'thumbnail': thumbnail,
                'title': title,
                'upload_date': upload_date,
                'duration': int_or_none(duration),
                'formats': formats
            })

        title = self._html_search_regex(
            (r'<div class="tv_translation">\s*<h1><a href="[^"]+">([^<]*)</a>',
             r"'title'\s*:\s*'([^']+)'"),
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None)
        description = self._html_search_regex(
            r'<div class="descr">\s*<div>&nbsp;</div>\s*<p>([^<]*)</p></div>',
            webpage, 'description', default=None) or self._html_search_meta(
            'description', webpage, 'description', default=None)

        return self.playlist_result(entries, display_id, title, description)
