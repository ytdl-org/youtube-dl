# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    find_xpath_attr,
    unified_strdate,
    get_element_by_attribute,
    int_or_none,
    NO_DEFAULT,
    qualities,
)

# There are different sources of video in arte.tv, the extraction process
# is different for each one. The videos usually expire in 7 days, so we can't
# add tests.


class ArteTvIE(InfoExtractor):
    _VALID_URL = r'https?://videos\.arte\.tv/(?P<lang>fr|de|en|es)/.*-(?P<id>.*?)\.html'
    IE_NAME = 'arte.tv'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        lang = mobj.group('lang')
        video_id = mobj.group('id')

        ref_xml_url = url.replace('/videos/', '/do_delegate/videos/')
        ref_xml_url = ref_xml_url.replace('.html', ',view,asPlayerXml.xml')
        ref_xml_doc = self._download_xml(
            ref_xml_url, video_id, note='Downloading metadata')
        config_node = find_xpath_attr(ref_xml_doc, './/video', 'lang', lang)
        config_xml_url = config_node.attrib['ref']
        config = self._download_xml(
            config_xml_url, video_id, note='Downloading configuration')

        formats = [{
            'format_id': q.attrib['quality'],
            # The playpath starts at 'mp4:', if we don't manually
            # split the url, rtmpdump will incorrectly parse them
            'url': q.text.split('mp4:', 1)[0],
            'play_path': 'mp4:' + q.text.split('mp4:', 1)[1],
            'ext': 'flv',
            'quality': 2 if q.attrib['quality'] == 'hd' else 1,
        } for q in config.findall('./urls/url')]
        self._sort_formats(formats)

        title = config.find('.//name').text
        thumbnail = config.find('.//firstThumbnailUrl').text
        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }


class ArteTVBaseIE(InfoExtractor):
    @classmethod
    def _extract_url_info(cls, url):
        mobj = re.match(cls._VALID_URL, url)
        lang = mobj.group('lang')
        query = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
        if 'vid' in query:
            video_id = query['vid'][0]
        else:
            # This is not a real id, it can be for example AJT for the news
            # http://www.arte.tv/guide/fr/emissions/AJT/arte-journal
            video_id = mobj.group('id')
        return video_id, lang

    def _extract_from_json_url(self, json_url, video_id, lang, title=None):
        info = self._download_json(json_url, video_id)
        player_info = info['videoJsonPlayer']

        upload_date_str = player_info.get('shootingDate')
        if not upload_date_str:
            upload_date_str = (player_info.get('VRA') or player_info.get('VDA') or '').split(' ')[0]

        title = (player_info.get('VTI') or title or player_info['VID']).strip()
        subtitle = player_info.get('VSU', '').strip()
        if subtitle:
            title += ' - %s' % subtitle

        info_dict = {
            'id': player_info['VID'],
            'title': title,
            'description': player_info.get('VDE'),
            'upload_date': unified_strdate(upload_date_str),
            'thumbnail': player_info.get('programImage') or player_info.get('VTU', {}).get('IUR'),
        }
        qfunc = qualities(['HQ', 'MQ', 'EQ', 'SQ'])

        LANGS = {
            'fr': 'F',
            'de': 'A',
            'en': 'E[ANG]',
            'es': 'E[ESP]',
        }

        langcode = LANGS.get(lang, lang)

        formats = []
        for format_id, format_dict in player_info['VSR'].items():
            f = dict(format_dict)
            versionCode = f.get('versionCode')
            l = re.escape(langcode)

            # Language preference from most to least priority
            # Reference: section 5.6.3 of
            # http://www.arte.tv/sites/en/corporate/files/complete-technical-guidelines-arte-geie-v1-05.pdf
            PREFERENCES = (
                # original version in requested language, without subtitles
                r'VO{0}$'.format(l),
                # original version in requested language, with partial subtitles in requested language
                r'VO{0}-ST{0}$'.format(l),
                # original version in requested language, with subtitles for the deaf and hard-of-hearing in requested language
                r'VO{0}-STM{0}$'.format(l),
                # non-original (dubbed) version in requested language, without subtitles
                r'V{0}$'.format(l),
                # non-original (dubbed) version in requested language, with subtitles partial subtitles in requested language
                r'V{0}-ST{0}$'.format(l),
                # non-original (dubbed) version in requested language, with subtitles for the deaf and hard-of-hearing in requested language
                r'V{0}-STM{0}$'.format(l),
                # original version in requested language, with partial subtitles in different language
                r'VO{0}-ST(?!{0}).+?$'.format(l),
                # original version in requested language, with subtitles for the deaf and hard-of-hearing in different language
                r'VO{0}-STM(?!{0}).+?$'.format(l),
                # original version in different language, with partial subtitles in requested language
                r'VO(?:(?!{0}).+?)?-ST{0}$'.format(l),
                # original version in different language, with subtitles for the deaf and hard-of-hearing in requested language
                r'VO(?:(?!{0}).+?)?-STM{0}$'.format(l),
                # original version in different language, without subtitles
                r'VO(?:(?!{0}))?$'.format(l),
                # original version in different language, with partial subtitles in different language
                r'VO(?:(?!{0}).+?)?-ST(?!{0}).+?$'.format(l),
                # original version in different language, with subtitles for the deaf and hard-of-hearing in different language
                r'VO(?:(?!{0}).+?)?-STM(?!{0}).+?$'.format(l),
            )

            for pref, p in enumerate(PREFERENCES):
                if re.match(p, versionCode):
                    lang_pref = len(PREFERENCES) - pref
                    break
            else:
                lang_pref = -1

            format = {
                'format_id': format_id,
                'preference': -10 if f.get('videoFormat') == 'M3U8' else None,
                'language_preference': lang_pref,
                'format_note': '%s, %s' % (f.get('versionCode'), f.get('versionLibelle')),
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'tbr': int_or_none(f.get('bitrate')),
                'quality': qfunc(f.get('quality')),
            }

            if f.get('mediaType') == 'rtmp':
                format['url'] = f['streamer']
                format['play_path'] = 'mp4:' + f['url']
                format['ext'] = 'flv'
            else:
                format['url'] = f['url']

            formats.append(format)

        self._check_formats(formats, video_id)
        self._sort_formats(formats)

        info_dict['formats'] = formats
        return info_dict


class ArteTVPlus7IE(ArteTVBaseIE):
    IE_NAME = 'arte.tv:+7'
    _VALID_URL = r'https?://(?:(?:www|sites)\.)?arte\.tv/[^/]+/(?P<lang>fr|de|en|es)/(?:[^/]+/)*(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.arte.tv/guide/de/sendungen/XEN/xenius/?vid=055918-015_PLUS7-D',
        'only_matching': True,
    }, {
        'url': 'http://sites.arte.tv/karambolage/de/video/karambolage-22',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if ArteTVPlaylistIE.suitable(url) else super(ArteTVPlus7IE, cls).suitable(url)

    def _real_extract(self, url):
        video_id, lang = self._extract_url_info(url)
        webpage = self._download_webpage(url, video_id)
        return self._extract_from_webpage(webpage, video_id, lang)

    def _extract_from_webpage(self, webpage, video_id, lang):
        patterns_templates = (r'arte_vp_url=["\'](.*?%s.*?)["\']', r'data-url=["\']([^"]+%s[^"]+)["\']')
        ids = (video_id, '')
        # some pages contain multiple videos (like
        # http://www.arte.tv/guide/de/sendungen/XEN/xenius/?vid=055918-015_PLUS7-D),
        # so we first try to look for json URLs that contain the video id from
        # the 'vid' parameter.
        patterns = [t % re.escape(_id) for _id in ids for t in patterns_templates]
        json_url = self._html_search_regex(
            patterns, webpage, 'json vp url', default=None)
        if not json_url:
            def find_iframe_url(webpage, default=NO_DEFAULT):
                return self._html_search_regex(
                    r'<iframe[^>]+src=(["\'])(?P<url>.+\bjson_url=.+?)\1',
                    webpage, 'iframe url', group='url', default=default)

            iframe_url = find_iframe_url(webpage, None)
            if not iframe_url:
                embed_url = self._html_search_regex(
                    r'arte_vp_url_oembed=\'([^\']+?)\'', webpage, 'embed url', default=None)
                if embed_url:
                    player = self._download_json(
                        embed_url, video_id, 'Downloading player page')
                    iframe_url = find_iframe_url(player['html'])
            # en and es URLs produce react-based pages with different layout (e.g.
            # http://www.arte.tv/guide/en/053330-002-A/carnival-italy?zone=world)
            if not iframe_url:
                program = self._search_regex(
                    r'program\s*:\s*({.+?["\']embed_html["\'].+?}),?\s*\n',
                    webpage, 'program', default=None)
                if program:
                    embed_html = self._parse_json(program, video_id)
                    if embed_html:
                        iframe_url = find_iframe_url(embed_html['embed_html'])
            if iframe_url:
                json_url = compat_parse_qs(
                    compat_urllib_parse_urlparse(iframe_url).query)['json_url'][0]
        if json_url:
            title = self._search_regex(
                r'<h3[^>]+title=(["\'])(?P<title>.+?)\1',
                webpage, 'title', default=None, group='title')
            return self._extract_from_json_url(json_url, video_id, lang, title=title)
        # Different kind of embed URL (e.g.
        # http://www.arte.tv/magazine/trepalium/fr/episode-0406-replay-trepalium)
        entries = [
            self.url_result(url)
            for _, url in re.findall(r'<iframe[^>]+src=(["\'])(?P<url>.+?)\1', webpage)]
        return self.playlist_result(entries)


# It also uses the arte_vp_url url from the webpage to extract the information
class ArteTVCreativeIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:creative'
    _VALID_URL = r'https?://creative\.arte\.tv/(?P<lang>fr|de|en|es)/(?:[^/]+/)*(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://creative.arte.tv/fr/episode/osmosis-episode-1',
        'info_dict': {
            'id': '057405-001-A',
            'ext': 'mp4',
            'title': 'OSMOSIS - N\'AYEZ PLUS PEUR D\'AIMER (1)',
            'upload_date': '20150716',
        },
    }, {
        'url': 'http://creative.arte.tv/fr/Monty-Python-Reunion',
        'playlist_count': 11,
        'add_ie': ['Youtube'],
    }, {
        'url': 'http://creative.arte.tv/de/episode/agentur-amateur-4-der-erste-kunde',
        'only_matching': True,
    }]


class ArteTVInfoIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:info'
    _VALID_URL = r'https?://info\.arte\.tv/(?P<lang>fr|de|en|es)/(?:[^/]+/)*(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://info.arte.tv/fr/service-civique-un-cache-misere',
        'info_dict': {
            'id': '067528-000-A',
            'ext': 'mp4',
            'title': 'Service civique, un cache misère ?',
            'upload_date': '20160403',
        },
    }]


class ArteTVFutureIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:future'
    _VALID_URL = r'https?://future\.arte\.tv/(?P<lang>fr|de|en|es)/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://future.arte.tv/fr/info-sciences/les-ecrevisses-aussi-sont-anxieuses',
        'info_dict': {
            'id': '050940-028-A',
            'ext': 'mp4',
            'title': 'Les écrevisses aussi peuvent être anxieuses',
            'upload_date': '20140902',
        },
    }, {
        'url': 'http://future.arte.tv/fr/la-science-est-elle-responsable',
        'only_matching': True,
    }]


class ArteTVDDCIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:ddc'
    _VALID_URL = r'https?://ddc\.arte\.tv/(?P<lang>emission|folge)/(?P<id>[^/?#&]+)'

    _TESTS = []

    def _real_extract(self, url):
        video_id, lang = self._extract_url_info(url)
        if lang == 'folge':
            lang = 'de'
        elif lang == 'emission':
            lang = 'fr'
        webpage = self._download_webpage(url, video_id)
        scriptElement = get_element_by_attribute('class', 'visu_video_block', webpage)
        script_url = self._html_search_regex(r'src="(.*?)"', scriptElement, 'script url')
        javascriptPlayerGenerator = self._download_webpage(script_url, video_id, 'Download javascript player generator')
        json_url = self._search_regex(r"json_url=(.*)&rendering_place.*", javascriptPlayerGenerator, 'json url')
        return self._extract_from_json_url(json_url, video_id, lang)


class ArteTVConcertIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:concert'
    _VALID_URL = r'https?://concert\.arte\.tv/(?P<lang>fr|de|en|es)/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://concert.arte.tv/de/notwist-im-pariser-konzertclub-divan-du-monde',
        'md5': '9ea035b7bd69696b67aa2ccaaa218161',
        'info_dict': {
            'id': '186',
            'ext': 'mp4',
            'title': 'The Notwist im Pariser Konzertclub "Divan du Monde"',
            'upload_date': '20140128',
            'description': 'md5:486eb08f991552ade77439fe6d82c305',
        },
    }]


class ArteTVCinemaIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:cinema'
    _VALID_URL = r'https?://cinema\.arte\.tv/(?P<lang>fr|de|en|es)/(?P<id>.+)'

    _TESTS = [{
        'url': 'http://cinema.arte.tv/fr/article/les-ailes-du-desir-de-julia-reck',
        'md5': 'a5b9dd5575a11d93daf0e3f404f45438',
        'info_dict': {
            'id': '062494-000-A',
            'ext': 'mp4',
            'title': 'Film lauréat du concours web - "Les ailes du désir" de Julia Reck',
            'upload_date': '20150807',
        },
    }]


class ArteTVMagazineIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:magazine'
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/magazine/[^/]+/(?P<lang>fr|de|en|es)/(?P<id>[^/?#&]+)'

    _TESTS = [{
        # Embedded via <iframe src="http://www.arte.tv/arte_vp/index.php?json_url=..."
        'url': 'http://www.arte.tv/magazine/trepalium/fr/entretien-avec-le-realisateur-vincent-lannoo-trepalium',
        'md5': '2a9369bcccf847d1c741e51416299f25',
        'info_dict': {
            'id': '065965-000-A',
            'ext': 'mp4',
            'title': 'Trepalium - Extrait Ep.01',
            'upload_date': '20160121',
        },
    }, {
        # Embedded via <iframe src="http://www.arte.tv/guide/fr/embed/054813-004-A/medium"
        'url': 'http://www.arte.tv/magazine/trepalium/fr/episode-0406-replay-trepalium',
        'md5': 'fedc64fc7a946110fe311634e79782ca',
        'info_dict': {
            'id': '054813-004_PLUS7-F',
            'ext': 'mp4',
            'title': 'Trepalium (4/6)',
            'description': 'md5:10057003c34d54e95350be4f9b05cb40',
            'upload_date': '20160218',
        },
    }, {
        'url': 'http://www.arte.tv/magazine/metropolis/de/frank-woeste-german-paris-metropolis',
        'only_matching': True,
    }]


class ArteTVEmbedIE(ArteTVPlus7IE):
    IE_NAME = 'arte.tv:embed'
    _VALID_URL = r'''(?x)
        http://www\.arte\.tv
        /(?:playerv2/embed|arte_vp/index)\.php\?json_url=
        (?P<json_url>
            http://arte\.tv/papi/tvguide/videos/stream/player/
            (?P<lang>[^/]+)/(?P<id>[^/]+)[^&]*
        )
    '''

    _TESTS = []

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        lang = mobj.group('lang')
        json_url = mobj.group('json_url')
        return self._extract_from_json_url(json_url, video_id, lang)


class TheOperaPlatformIE(ArteTVPlus7IE):
    IE_NAME = 'theoperaplatform'
    _VALID_URL = r'https?://(?:www\.)?theoperaplatform\.eu/(?P<lang>fr|de|en|es)/(?P<id>[^/?#&]+)'

    _TESTS = [{
        'url': 'http://www.theoperaplatform.eu/de/opera/verdi-otello',
        'md5': '970655901fa2e82e04c00b955e9afe7b',
        'info_dict': {
            'id': '060338-009-A',
            'ext': 'mp4',
            'title': 'Verdi - OTELLO',
            'upload_date': '20160927',
        },
    }]


class ArteTVPlaylistIE(ArteTVBaseIE):
    IE_NAME = 'arte.tv:playlist'
    _VALID_URL = r'https?://(?:www\.)?arte\.tv/guide/(?P<lang>fr|de|en|es)/[^#]*#collection/(?P<id>PL-\d+)'

    _TESTS = [{
        'url': 'http://www.arte.tv/guide/de/plus7/?country=DE#collection/PL-013263/ARTETV',
        'info_dict': {
            'id': 'PL-013263',
            'title': 'Areva & Uramin',
            'description': 'md5:a1dc0312ce357c262259139cfd48c9bf',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'http://www.arte.tv/guide/de/playlists?country=DE#collection/PL-013190/ARTETV',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id, lang = self._extract_url_info(url)
        collection = self._download_json(
            'https://api.arte.tv/api/player/v1/collectionData/%s/%s?source=videos'
            % (lang, playlist_id), playlist_id)
        title = collection.get('title')
        description = collection.get('shortDescription') or collection.get('teaserText')
        entries = [
            self._extract_from_json_url(
                video['jsonUrl'], video.get('programId') or playlist_id, lang)
            for video in collection['videos'] if video.get('jsonUrl')]
        return self.playlist_result(entries, playlist_id, title, description)
