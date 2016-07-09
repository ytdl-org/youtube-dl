# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_age_limit,
    parse_iso8601,
    xpath_text,
)


class VideomoreIE(InfoExtractor):
    IE_NAME = 'videomore'
    _VALID_URL = r'videomore:(?P<sid>\d+)$|https?://videomore\.ru/(?:(?:embed|[^/]+/[^/]+)/|[^/]+\?.*\btrack_id=)(?P<id>\d+)(?:[/?#&]|\.(?:xml|json)|$)'
    _TESTS = [{
        'url': 'http://videomore.ru/kino_v_detalayah/5_sezon/367617',
        'md5': '70875fbf57a1cd004709920381587185',
        'info_dict': {
            'id': '367617',
            'ext': 'flv',
            'title': 'В гостях Алексей Чумаков и Юлия Ковальчук',
            'description': 'В гостях – лучшие романтические комедии года, «Выживший» Иньярриту и «Стив Джобс» Дэнни Бойла.',
            'series': 'Кино в деталях',
            'episode': 'В гостях Алексей Чумаков и Юлия Ковальчук',
            'episode_number': None,
            'season': 'Сезон 2015',
            'season_number': 5,
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 2910,
            'age_limit': 16,
            'view_count': int,
        },
    }, {
        'url': 'http://videomore.ru/embed/259974',
        'info_dict': {
            'id': '259974',
            'ext': 'flv',
            'title': '80 серия',
            'description': '«Медведей» ждет решающий матч. Макеев выясняет отношения со Стрельцовым. Парни узнают подробности прошлого Макеева.',
            'series': 'Молодежка',
            'episode': '80 серия',
            'episode_number': 40,
            'season': '2 сезон',
            'season_number': 2,
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 2809,
            'age_limit': 16,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://videomore.ru/molodezhka/sezon_promo/341073',
        'info_dict': {
            'id': '341073',
            'ext': 'flv',
            'title': 'Команда проиграла из-за Бакина?',
            'description': 'Молодежка 3 сезон скоро',
            'series': 'Молодежка',
            'episode': 'Команда проиграла из-за Бакина?',
            'episode_number': None,
            'season': 'Промо',
            'season_number': 99,
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 29,
            'age_limit': 16,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'http://videomore.ru/elki_3?track_id=364623',
        'only_matching': True,
    }, {
        'url': 'http://videomore.ru/embed/364623',
        'only_matching': True,
    }, {
        'url': 'http://videomore.ru/video/tracks/364623.xml',
        'only_matching': True,
    }, {
        'url': 'http://videomore.ru/video/tracks/364623.json',
        'only_matching': True,
    }, {
        'url': 'http://videomore.ru/video/tracks/158031/quotes/33248',
        'only_matching': True,
    }, {
        'url': 'videomore:367617',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<object[^>]+data=(["\'])https?://videomore.ru/player\.swf\?.*config=(?P<url>https?://videomore\.ru/(?:[^/]+/)+\d+\.xml).*\1',
            webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('sid') or mobj.group('id')

        video = self._download_xml(
            'http://videomore.ru/video/tracks/%s.xml' % video_id,
            video_id, 'Downloading video XML')

        video_url = xpath_text(video, './/video_url', 'video url', fatal=True)
        formats = self._extract_f4m_formats(video_url, video_id, f4m_id='hds')
        self._sort_formats(formats)

        data = self._download_json(
            'http://videomore.ru/video/tracks/%s.json' % video_id,
            video_id, 'Downloading video JSON')

        title = data.get('title') or data['project_title']
        description = data.get('description') or data.get('description_raw')
        timestamp = parse_iso8601(data.get('published_at'))
        duration = int_or_none(data.get('duration'))
        view_count = int_or_none(data.get('views'))
        age_limit = parse_age_limit(data.get('min_age'))
        thumbnails = [{
            'url': thumbnail,
        } for thumbnail in data.get('big_thumbnail_urls', [])]

        series = data.get('project_title')
        episode = data.get('title')
        episode_number = int_or_none(data.get('episode_of_season') or None)
        season = data.get('season_title')
        season_number = int_or_none(data.get('season_pos') or None)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'series': series,
            'episode': episode,
            'episode_number': episode_number,
            'season': season,
            'season_number': season_number,
            'thumbnails': thumbnails,
            'timestamp': timestamp,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
            'formats': formats,
        }


class VideomoreVideoIE(InfoExtractor):
    IE_NAME = 'videomore:video'
    _VALID_URL = r'https?://videomore\.ru/(?:(?:[^/]+/){2})?(?P<id>[^/?#&]+)[/?#&]*$'
    _TESTS = [{
        # single video with og:video:iframe
        'url': 'http://videomore.ru/elki_3',
        'info_dict': {
            'id': '364623',
            'ext': 'flv',
            'title': 'Ёлки 3',
            'description': '',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 5579,
            'age_limit': 6,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # season single series with og:video:iframe
        'url': 'http://videomore.ru/poslednii_ment/1_sezon/14_seriya',
        'only_matching': True,
    }, {
        'url': 'http://videomore.ru/sejchas_v_seti/serii_221-240/226_vypusk',
        'only_matching': True,
    }, {
        # single video without og:video:iframe
        'url': 'http://videomore.ru/marin_i_ego_druzya',
        'info_dict': {
            'id': '359073',
            'ext': 'flv',
            'title': '1 серия. Здравствуй, Аквавилль!',
            'description': 'md5:c6003179538b5d353e7bcd5b1372b2d7',
            'thumbnail': 're:^https?://.*\.jpg',
            'duration': 754,
            'age_limit': 6,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }]

    @classmethod
    def suitable(cls, url):
        return False if VideomoreIE.suitable(url) else super(VideomoreVideoIE, cls).suitable(url)

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_url = self._og_search_property(
            'video:iframe', webpage, 'video url', default=None)

        if not video_url:
            video_id = self._search_regex(
                (r'config\s*:\s*["\']https?://videomore\.ru/video/tracks/(\d+)\.xml',
                 r'track-id=["\'](\d+)',
                 r'xcnt_product_id\s*=\s*(\d+)'), webpage, 'video id')
            video_url = 'videomore:%s' % video_id

        return self.url_result(video_url, VideomoreIE.ie_key())


class VideomoreSeasonIE(InfoExtractor):
    IE_NAME = 'videomore:season'
    _VALID_URL = r'https?://videomore\.ru/(?!embed)(?P<id>[^/]+/[^/?#&]+)[/?#&]*$'
    _TESTS = [{
        'url': 'http://videomore.ru/molodezhka/sezon_promo',
        'info_dict': {
            'id': 'molodezhka/sezon_promo',
            'title': 'Молодежка Промо',
        },
        'playlist_mincount': 12,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        title = self._og_search_title(webpage)

        entries = [
            self.url_result(item) for item in re.findall(
                r'<a[^>]+href="((?:https?:)?//videomore\.ru/%s/[^/]+)"[^>]+class="widget-item-desc"'
                % display_id, webpage)]

        return self.playlist_result(entries, display_id, title)
