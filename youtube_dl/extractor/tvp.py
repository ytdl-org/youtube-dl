# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    clean_html,
    get_element_by_attribute,
    ExtractorError,
)


class TVPIE(InfoExtractor):
    IE_NAME = 'tvp'
    IE_DESC = 'Telewizja Polska'
    _VALID_URL = r'https?://[^/]+\.tvp\.(?:pl|info)/(?:(?!\d+/)[^/]+/)*(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/194536/i-seria-odc-13',
        'md5': '8aa518c15e5cc32dfe8db400dc921fbb',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, I seria – odc. 13',
            'description': 'md5:76649d2014f65c99477be17f23a4dead',
        },
    }, {
        'url': 'http://www.tvp.pl/there-can-be-anything-so-i-shortened-it/17916176',
        'md5': 'b0005b542e5b4de643a9690326ab1257',
        'info_dict': {
            'id': '17916176',
            'ext': 'mp4',
            'title': 'TVP Gorzów pokaże filmy studentów z podroży dookoła świata',
            'description': 'TVP Gorzów pokaże filmy studentów z podroży dookoła świata',
        },
    }, {
        # page id is not the same as video id(#7799)
        'url': 'http://vod.tvp.pl/22704887/08122015-1500',
        'md5': 'cf6a4705dfd1489aef8deb168d6ba742',
        'info_dict': {
            'id': '22680786',
            'ext': 'mp4',
            'title': 'Wiadomości, 08.12.2015, 15:00',
        },
    }, {
        'url': 'http://vod.tvp.pl/seriale/obyczajowe/na-sygnale/sezon-2-27-/odc-39/17834272',
        'only_matching': True,
    }, {
        'url': 'http://wiadomosci.tvp.pl/25169746/24052016-1200',
        'only_matching': True,
    }, {
        'url': 'http://krakow.tvp.pl/25511623/25lecie-mck-wyjatkowe-miejsce-na-mapie-krakowa',
        'only_matching': True,
    }, {
        'url': 'http://teleexpress.tvp.pl/25522307/wierni-wzieli-udzial-w-procesjach',
        'only_matching': True,
    }, {
        'url': 'http://sport.tvp.pl/25522165/krychowiak-uspokaja-w-sprawie-kontuzji-dwa-tygodnie-to-maksimum',
        'only_matching': True,
    }, {
        'url': 'http://www.tvp.info/25511919/trwa-rewolucja-wladza-zdecydowala-sie-na-pogwalcenie-konstytucji',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        video_id = self._search_regex([
            r'<iframe[^>]+src="[^"]*?object_id=(\d+)',
            r"object_id\s*:\s*'(\d+)'",
            r'data-video-id="(\d+)"'], webpage, 'video id', default=page_id)
        return {
            '_type': 'url_transparent',
            'url': 'tvp:' + video_id,
            'description': self._og_search_description(webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage),
            'ie_key': 'TVPEmbed',
        }


class TVPEmbedIE(InfoExtractor):
    IE_NAME = 'tvp:embed'
    IE_DESC = 'Telewizja Polska'
    _VALID_URL = r'(?:tvp:|https?://[^/]+\.tvp\.(?:pl|info)/sess/tvplayer\.php\?.*?object_id=)(?P<id>\d+)'

    _TESTS = [{
        'url': 'http://www.tvp.pl/sess/tvplayer.php?object_id=22670268',
        'md5': '8c9cd59d16edabf39331f93bf8a766c7',
        'info_dict': {
            'id': '22670268',
            'ext': 'mp4',
            'title': 'Panorama, 07.12.2015, 15:40',
        },
    }, {
        'url': 'tvp:22670268',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.tvp.pl/sess/tvplayer.php?object_id=%s' % video_id, video_id)

        error_massage = get_element_by_attribute('class', 'msg error', webpage)
        if error_massage:
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, clean_html(error_massage)), expected=True)

        title = self._search_regex(
            r'name\s*:\s*([\'"])Title\1\s*,\s*value\s*:\s*\1(?P<title>.+?)\1',
            webpage, 'title', group='title')
        series_title = self._search_regex(
            r'name\s*:\s*([\'"])SeriesTitle\1\s*,\s*value\s*:\s*\1(?P<series>.+?)\1',
            webpage, 'series', group='series', default=None)
        if series_title:
            title = '%s, %s' % (series_title, title)

        thumbnail = self._search_regex(
            r"poster\s*:\s*'([^']+)'", webpage, 'thumbnail', default=None)

        video_url = self._search_regex(
            r'0:{src:([\'"])(?P<url>.*?)\1', webpage,
            'formats', group='url', default=None)
        if not video_url or 'material_niedostepny.mp4' in video_url:
            video_url = self._download_json(
                'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s' % video_id,
                video_id)['video_url']

        formats = []
        video_url_base = self._search_regex(
            r'(https?://.+?/video)(?:\.(?:ism|f4m|m3u8)|-\d+\.mp4)',
            video_url, 'video base url', default=None)
        if video_url_base:
            # TODO: <Group> found instead of <AdaptationSet> in MPD manifest.
            # It's not mentioned in MPEG-DASH standard. Figure that out.
            # formats.extend(self._extract_mpd_formats(
            #     video_url_base + '.ism/video.mpd',
            #     video_id, mpd_id='dash', fatal=False))
            formats.extend(self._extract_ism_formats(
                video_url_base + '.ism/Manifest',
                video_id, 'mss', fatal=False))
            formats.extend(self._extract_f4m_formats(
                video_url_base + '.ism/video.f4m',
                video_id, f4m_id='hds', fatal=False))
            m3u8_formats = self._extract_m3u8_formats(
                video_url_base + '.ism/video.m3u8', video_id,
                'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
            self._sort_formats(m3u8_formats)
            m3u8_formats = list(filter(
                lambda f: f.get('vcodec') != 'none' and f.get('resolution') != 'multiple',
                m3u8_formats))
            formats.extend(m3u8_formats)
            for i, m3u8_format in enumerate(m3u8_formats, 2):
                http_url = '%s-%d.mp4' % (video_url_base, i)
                if self._is_valid_url(http_url, video_id):
                    f = m3u8_format.copy()
                    f.update({
                        'url': http_url,
                        'format_id': f['format_id'].replace('hls', 'http'),
                        'protocol': 'http',
                    })
                    formats.append(f)
        else:
            formats = [{
                'format_id': 'direct',
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
            }]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class TVPSeriesIE(InfoExtractor):
    IE_NAME = 'tvp:series'
    _VALID_URL = r'https?://vod\.tvp\.pl/(?:[^/]+/){2}(?P<id>[^/]+)/?$'

    _TESTS = [{
        'url': 'http://vod.tvp.pl/filmy-fabularne/filmy-za-darmo/ogniem-i-mieczem',
        'info_dict': {
            'title': 'Ogniem i mieczem',
            'id': '4278026',
        },
        'playlist_count': 4,
    }, {
        'url': 'http://vod.tvp.pl/audycje/podroze/boso-przez-swiat',
        'info_dict': {
            'title': 'Boso przez świat',
            'id': '9329207',
        },
        'playlist_count': 86,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id, tries=5)

        title = self._html_search_regex(
            r'(?s) id=[\'"]path[\'"]>(?:.*? / ){2}(.*?)</span>', webpage, 'series')
        playlist_id = self._search_regex(r'nodeId:\s*(\d+)', webpage, 'playlist id')
        playlist = self._download_webpage(
            'http://vod.tvp.pl/vod/seriesAjax?type=series&nodeId=%s&recommend'
            'edId=0&sort=&page=0&pageSize=10000' % playlist_id, display_id, tries=5,
            note='Downloading playlist')

        videos_paths = re.findall(
            '(?s)class="shortTitle">.*?href="(/[^"]+)', playlist)
        entries = [
            self.url_result('http://vod.tvp.pl%s' % v_path, ie=TVPIE.ie_key())
            for v_path in videos_paths]

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'display_id': display_id,
            'title': title,
            'entries': entries,
        }
