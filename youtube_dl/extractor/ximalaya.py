# coding: utf-8
from __future__ import unicode_literals

import re

import itertools

from ..compat import (
    compat_str,
)

from .common import InfoExtractor


class XimalayaBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ['CN']


class XimalayaIE(XimalayaBaseIE):
    IE_NAME = 'ximalaya'
    IE_DESC = 'ximalaya.com'
    _VALID_URL = r'https?://(?:www\.|m\.)?ximalaya\.com/(?P<uid>[0-9]+)/sound/(?P<id>[0-9]+)/?'
    _USER_URL_FORMAT = 'http://www.ximalaya.com/zhubo/%i/'
    _TESTS = [
        {
            'url': 'http://www.ximalaya.com/61425525/sound/47740352/',
            # 'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
            'info_dict': {
                'id': '47740352',
                'ext': 'm4a',
                'title': '261.唐诗三百首.卷八.送孟浩然之广陵.李白',
                'description': 'contains:孤帆远影碧空尽，惟见长江天际流。',
                'uploader': '小彬彬爱听书',
                'uploader_id': 61425525,
                'view_count': int,
                'like_count': int,
            }
        },
        {
            'url': 'http://m.ximalaya.com/61425525/sound/47740352/',
            'info_dict': {
                'id': '47740352',
                'ext': 'm4a',
                'title': '261.唐诗三百首.卷八.送孟浩然之广陵.李白',
                'description': 'contains:孤帆远影碧空尽，惟见长江天际流。',
                'uploader': '小彬彬爱听书',
                'uploader_id': 61425525,
            }
        },
    ]

    def _real_extract(self, url):

        is_m = 'm.ximalaya' in url

        audio_id = self._match_id(url)
        webpage = self._download_webpage(url, audio_id,
                                         note='Download sound page for %s' % audio_id,
                                         errnote='Unable to get sound page')

        audio_info_file = 'http://m.ximalaya.com/tracks/%s.json' % audio_id
        audio_info = self._download_json(audio_info_file, audio_id,
                                         'Downloading info json %s' % audio_info_file,
                                         'Unable to download info file', fatal=True)

        formats = []
        for bps, k in (('24k', 'play_path_32'), ('64k', 'play_path_64')):
            if audio_info.get(k):
                formats.append({
                    'format_id': bps,
                    'url': audio_info[k],
                    'ext': 'm4a',
                })

        # cover pics kyes like: cover_url', 'cover_url_142'
        thumbnails = [{'name': k, 'url': audio_info.get(k)} for k in audio_info.keys() if k.startswith('cover_url')]

        audio_uploader_id = audio_info.get('uid')

        if is_m:
            intro = re.search(r'(?s)<section class=["\']content[^>]+>(.+)</section>', webpage)
        else:
            intro = re.search(r'(?s)<div class="rich_intro"[^>]*>(.+?</article>)', webpage)

        if intro:
            audio_description = intro.group(1).strip()
        else:
            audio_description_file = 'http://www.ximalaya.com/sounds/%s/rich_intro' % audio_id
            audio_description = self._download_webpage(audio_description_file, audio_id,
                                                       note='Downloading description file %s' % audio_description_file,
                                                       errnote='Unable to download descrip file, try to parse web page',
                                                       fatal=False)
            audio_description = audio_description.strip()

        return {
            'id': audio_id,
            'uploader': audio_info.get('nickname'),
            'uploader_id': audio_uploader_id,
            'uploader_url': self._USER_URL_FORMAT % audio_uploader_id,
            'title': audio_info.get('title'),
            'thumbnails': thumbnails,
            'description': audio_description,
            'categories': audio_info.get('category_title'),
            'duration': audio_info.get('duration'),
            'view_count': audio_info.get('play_count'),
            'like_count': audio_info.get('favorites_count'),
            'formats': formats,
        }


class XimalayaAlbumIE(XimalayaBaseIE):
    IE_NAME = 'ximalaya.com:album'
    IE_DESC = 'ximalaya album'
    _VALID_URL = r'https?://(?:www\.|m\.)?ximalaya\.com/(?P<uid>[0-9]+)/album/(?P<id>[0-9]+)/?'
    _TEMPLATE_URL = 'http://www.ximalaya.com/%s/album/%s/'
    _BASE_URL_TEMPL = 'http://www.ximalaya.com%s'
    _TESTS = [{
        'url': 'http://www.ximalaya.com/61425525/album/5534601/',
        'info_dict': {
            'title': 'contains:唐诗三百首（含赏析）',
            'id': '5534601',
        },
        'playlist_count': 312,
    }, {
        'url': 'http://m.ximalaya.com/61425525/album/5534601',
        'info_dict': {
            'title': 'contains:唐诗三百首（含赏析）',
            'id': '5534601',
        },
        'playlist_count': 312,
    },
    ]

    def _real_extract(self, url):
        uid, playlist_id = self._match_uid_an_id(url)
        assert uid.isdecimal()
        webpage = self._download_webpage(self._TEMPLATE_URL % (uid, playlist_id), playlist_id,
                                         note='Download album page for %s' % playlist_id,
                                         errnote='Unable to get album info'
                                         )

        mobj = re.search(r'detailContent_title(?:[^>]+)?><h1(?:[^>]+)?>([^<]+)</h1>', webpage)
        title = mobj.group(1) if mobj else self._meta_regex('title')

        return self.playlist_result(self._entries(webpage, playlist_id, uid), playlist_id, title)

    def _entries(self, page, playlist_id, uid):
        html = page
        for page_num in itertools.count(1):
            for entry in self._process_page(html, uid):
                yield entry

            mobj = re.search(r'<a href=(["\'])(?P<more>[^\'"]+)\1'
                             r'[^>]+rel=(["\'])next\3', html)
            if not mobj:
                break

            next_url = self._BASE_URL_TEMPL % mobj.group('more')
            self.report_download_webpage('%d %s' % (page_num, next_url))
            html = self._download_webpage(next_url, playlist_id)
            if not html.strip():
                # Some webpages show a "Load more" button but they don't
                # have more videos
                break

    def _process_page(self, html, uid):
        find_from = html.index('album_soundlist')
        for mobj in re.finditer(r'<a[^>]+?href="(?P<url>/' +
                                uid +
                                r'/sound/(?P<id>\d+)/?)"[^>]+?title="(?P<title>[^>]+)">',
                                html[find_from:]):
            if 'url' in mobj.groupdict():
                yield self.url_result(self._BASE_URL_TEMPL % mobj.group('url'),
                                      'Ximalaya',
                                      mobj.group('id'),
                                      mobj.group('title'))

    @classmethod
    def _match_uid_an_id(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        m = cls._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group('uid')), compat_str(m.group('id'))
