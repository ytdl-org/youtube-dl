# coding: utf-8
from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    get_element_by_attribute,
    orderedSet,
)


class TVPIE(InfoExtractor):
    IE_NAME = 'tvp'
    IE_DESC = 'Telewizja Polska'
    _VALID_URL = r'https?://[^/]+\.tvp\.(?:pl|info)/(?:video/(?:[^,\s]*,)*|(?:(?!\d+/)[^/]+/)*)(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://vod.tvp.pl/video/czas-honoru,i-seria-odc-13,194536',
        'md5': 'a21eb0aa862f25414430f15fdfb9e76c',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, odc. 13 – Władek',
            'description': 'md5:437f48b93558370b031740546b696e24',
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
        'url': 'https://wiadomosci.tvp.pl/33908820/28092017-1930',
        'md5': '84cd3c8aec4840046e5ab712416b73d0',
        'info_dict': {
            'id': '33908820',
            'ext': 'mp4',
            'title': 'Wiadomości, 28.09.2017, 19:30',
            'description': 'Wydanie główne codziennego serwisu informacyjnego.'
        },
        'skip': 'HTTP Error 404: Not Found',
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
            'description': self._og_search_description(
                webpage, default=None) or self._html_search_meta(
                'description', webpage, default=None),
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'ie_key': 'TVPEmbed',
        }


class TVPEmbedIE(InfoExtractor):
    IE_NAME = 'tvp:embed'
    IE_DESC = 'Telewizja Polska'
    _VALID_URL = r'(?:tvp:|https?://[^/]+\.tvp\.(?:pl|info)/sess/tvplayer\.php\?.*?object_id=)(?P<id>\d+)'

    _TESTS = [{
        'url': 'tvp:194536',
        'md5': 'a21eb0aa862f25414430f15fdfb9e76c',
        'info_dict': {
            'id': '194536',
            'ext': 'mp4',
            'title': 'Czas honoru, odc. 13 – Władek',
        },
    }, {
        # not available
        'url': 'http://www.tvp.pl/sess/tvplayer.php?object_id=22670268',
        'md5': '8c9cd59d16edabf39331f93bf8a766c7',
        'info_dict': {
            'id': '22670268',
            'ext': 'mp4',
            'title': 'Panorama, 07.12.2015, 15:40',
        },
        'skip': 'Transmisja została zakończona lub materiał niedostępny',
    }, {
        'url': 'tvp:22670268',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.tvp.pl/sess/tvplayer.php?object_id=%s' % video_id, video_id)

        error = self._html_search_regex(
            r'(?s)<p[^>]+\bclass=["\']notAvailable__text["\'][^>]*>(.+?)</p>',
            webpage, 'error', default=None) or clean_html(
            get_element_by_attribute('class', 'msg error', webpage))
        if error:
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, clean_html(error)), expected=True)

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
                lambda f: f.get('vcodec') != 'none', m3u8_formats))
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


class TVPWebsiteIE(InfoExtractor):
    IE_NAME = 'tvp:series'
    _VALID_URL = r'https?://vod\.tvp\.pl/website/(?P<display_id>[^,]+),(?P<id>\d+)'

    _TESTS = [{
        # series
        'url': 'https://vod.tvp.pl/website/lzy-cennet,38678312/video',
        'info_dict': {
            'id': '38678312',
        },
        'playlist_count': 115,
    }, {
        # film
        'url': 'https://vod.tvp.pl/website/gloria,35139666',
        'info_dict': {
            'id': '36637049',
            'ext': 'mp4',
            'title': 'Gloria, Gloria',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['TVPEmbed'],
    }, {
        'url': 'https://vod.tvp.pl/website/lzy-cennet,38678312',
        'only_matching': True,
    }]

    def _entries(self, display_id, playlist_id):
        url = 'https://vod.tvp.pl/website/%s,%s/video' % (display_id, playlist_id)
        for page_num in itertools.count(1):
            page = self._download_webpage(
                url, display_id, 'Downloading page %d' % page_num,
                query={'page': page_num})

            video_ids = orderedSet(re.findall(
                r'<a[^>]+\bhref=["\']/video/%s,[^,]+,(\d+)' % display_id,
                page))

            if not video_ids:
                break

            for video_id in video_ids:
                yield self.url_result(
                    'tvp:%s' % video_id, ie=TVPEmbedIE.ie_key(),
                    video_id=video_id)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id, playlist_id = mobj.group('display_id', 'id')
        return self.playlist_result(
            self._entries(display_id, playlist_id), playlist_id)


class TVPappIE(InfoExtractor):
    IE_NAME = 'tvp:app'
    # https://vod.tvp.pl/seriale,18/korona-krolow-jagiellonowie-odcinki,292227/odcinek-37,S01E37,392532
    # https://vod.tvp.pl/programy,88/korona-krolow-taka-historia-odcinki,283653/odcinek-1,S02E01,386064
    # https://vod.tvp.pl/filmy-dokumentalne,163/jurek,376503
    # https://vod.tvp.pl/dla-dzieci,24/zubr-pompik-odcinki,282014/odcinek-1,S01E01,319853
    # https://vod.tvp.pl/teatr-telewizji,202/barwy-uczuc,392420
    # https://vod.tvp.pl/filmy-fabularne,136/rozlam,390638
    _VALID_URL = r'https://vod.tvp.pl/(seriale|filmy-fabularne|programy|filmy-dokumentalne|dla-dzieci|teatr-telewizji|informacje-i-publicystyka),[0-9]+/([^,]+,[0-9]+/)?[^,]+,([^,]+,)?(?P<id>[0-9]+)'
    _TESTS = [
            {
                # series
                'url': 'https://vod.tvp.pl/seriale,18/korona-krolow-jagiellonowie-odcinki,292227/odcinek-37,S01E37,392532',
                'info_dict': {
                    'id': '392532',
                    'ext': 'mp4',

                    'series_id': 292227,
                    'title': 'Korona królów. Jagiellonowie - Episode 37 - odc. 37 – Branka',
                    'description': 'Wiosna 1407. Anna z Goraja znika z Wawelu. Jej matka - Beata z Bożego Daru rozpacza. Anna Cylejska  zarządza poszukiwania, a Sofia tajemniczo się uśmiecha. Elżbieta i Katarzyna Gorajskie wyjawiają, że ich siostra pojechała do klasztoru klarysek w Sączu. Na Wawel dociera wieść o śmierci Wielkiego Mistrza Konrada von Jungingena. Rozpoczyna się walka o władzę w Malborku. Jan Falkenberg ma list do papieża, w którym wyjawia sekret Trąby. Bdzigost i Ciołek zdobywają to pismo. Król Jagiełło poznaje wreszcie sekret Mikołaja Trąby i znajduje sposób, by go ochronić.',
                    'thumbnail': r're:^https?://.*\.jpg$',
                    'episode_number': 37,
                },
                'params': {
                    'skip_download': True,
                    'format': 'dash-f1-v1-x3',
                }
            },
            {
                # programs
                'url': 'https://vod.tvp.pl/programy,88/korona-krolow-taka-historia-odcinki,283653/odcinek-1,S02E01,386064',
                'info_dict': {
                    'id': '386064',
                    'ext': 'mp4',

                    'series_id': 283653,
                    'title': 'Korona królów. Taka historia... - Episode 1 - odc. 1 – Jagiełło: życie po Jadwidze',
                    'description': 'Jogaiła był Wielkim Księciem Litewskim, synem Olgierda i wnukiem Giedymina. W 1386 roku został polskim królem, bowiem został mężem polskiej monarchini – Jadwigi Andegaweńskiej. Dwa trony i dwóch władców mających pełnię władzy. Kiedy w 1399 roku Jadwiga zmarła, najważniejsi polscy możni za potwierdzenie praw Jagiełły do korony zapragnęli więcej wpływów na władzę, w następstwie czego Władysław Jagiełło postanowił zrzec się tronu i wrócić na Litwę. Zaczęły się rozmowy i negocjacje. Obu stronom zależało, żeby król pozostał królem. Możni zaproponowali Jagielle kandydatkę na nową żonę – Annę Cylejską. Dziewczyna była wnuczką Kazimierza Wielkiego, więc uznano ją za prawowitą dziedziczkę polskiego tronu, czym miała wzmacniać rolę Jagiełły. Przeprowadzono powtórną elekcję i ustanowiono warunki współpracy z Litwą.',
                    'thumbnail': r're:^https?://.*\.jpg$',
                    'episode_number': 1,
                },
                'params': {
                    'skip_download': True,
                    'format': 'dash-f1-v1-x3',
                }
            },
            {
                # filmy-dokumentalne
                'url': 'https://vod.tvp.pl/filmy-dokumentalne,163/jurek,376503',
                'info_dict': {
                    'id': '376503',
                    'ext': 'mp4',

                    'series_id': None,
                    'title': 'Jurek',
                    'description': 'Obraz człowieka, który pnie się do góry w sensie dosłownym, ale też metaforycznym i symbolicznym. Od socjalistycznego pracownika, po gwiazdę międzynarodowych mediów, od człowieka, który wspina się bez pieniędzy i sprzętu, po pełnoprawnego konkurenta Reinholda Messnera w walce o zdobycie Korony Himalajów i Karakorum. Skromnego, wyrazistego, kochającego góry. Rozmowy z rodziną i przyjaciółmi, archiwalia, zdjęcia, nagrania, fragmenty programów telewizyjnych i wywiadów składają się na portret całego środowiska himalaistów lat 80. To również obraz czasów, w jakich żyli – ciężkich i barwnych jednocześnie, kiedy idealizm miał większą wartość niż sława.',
                    'thumbnail': r're:^https?://.*\.jpg$',
                    'episode_number': None,
                },
                'params': {
                    'skip_download': True,
                    'format': 'dash-f1-v1-x3',
                }
            },
            {
                # dla-dzieci
                'url': 'https://vod.tvp.pl/dla-dzieci,24/zubr-pompik-odcinki,282014/odcinek-1,S01E01,319853',
                'info_dict': {
                    'id': '319853',
                    'ext': 'mp4',

                    'series_id': 282014,
                    'title': 'Żubr Pompik - Episode 1 - Odc. 1  – Duże i małe',
                    'description': 'W głębinach wielkiej, dzikiej, zielonej puszczy mieszka żubr Pompik. Jest niewielki, do tego nie tak silny, szybki i skoczny, jak jego rówieśnicy. Początkowo bardzo się tym martwi. A co, jeżeli nigdy nie urośnie? Odkrywa jednak, że ma wiele innych zalet! Jest najbardziej ciekawskim ze zwierząt w puszczy. Interesuje go wszystko, co dzieje się dookoła. Nie ma takiej leśnej tajemnicy, której Pompik by nie rozwiązał dzięki uważnej obserwacji, cierpliwości i zadawaniu mnóstwa pytań.',
                    'thumbnail': r're:^https?://.*\.jpg$',
                    'episode_number': 1,
                },
                'params': {
                    'skip_download': True,
                    'format': 'dash-f1-v1-x3',
                }
            },
]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'https://vod.tvp.pl/api/products/vods/%s?lang=pl&platform=BROWSER'
        url_p = 'https://vod.tvp.pl/api/products/%s/videos/playlist?platform=BROWSER&videoType=MOVIE'

        _details = self._download_json(url % video_id, video_id, 'Downloading details')
        _playlist = self._download_json(url_p % video_id, video_id, 'Downloading playlist')

        # import json
        # print(json.dumps(_playlist, indent = 2))
        formats = []
        formats.extend(self._extract_mpd_formats(_playlist['sources']['DASH'][0]['src'], video_id, mpd_id='dash', fatal=False))

        return {
            'id': video_id,
            'formats': formats,
            'duraton': _details['duration'],

            'series_id': _details['season']['serial']['id'] if 'season' in _details else None,
            'title': _details['statisticsParameters']['gemiusVideo']['fullTitle'],
            'description': _details['description'],
            'thumbnail': _details['images']['16x9'][0]['url'],
            'episode_number': _details['number'] if 'number' in _details else None,
        }

