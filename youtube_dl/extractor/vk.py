# coding: utf-8
from __future__ import unicode_literals

import collections
import re
import sys

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    clean_html,
    ExtractorError,
    get_element_by_class,
    int_or_none,
    orderedSet,
    remove_start,
    str_or_none,
    str_to_int,
    unescapeHTML,
    unified_timestamp,
    url_or_none,
    urlencode_postdata,
)
from .dailymotion import DailymotionIE
from .pladform import PladformIE
from .vimeo import VimeoIE
from .youtube import YoutubeIE


class VKBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'vk'

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login_page, url_handle = self._download_webpage_handle(
            'https://vk.com', None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'email': username.encode('cp1251'),
            'pass': password.encode('cp1251'),
        })

        # https://new.vk.com/ serves two same remixlhk cookies in Set-Cookie header
        # and expects the first one to be set rather than second (see
        # https://github.com/ytdl-org/youtube-dl/issues/9841#issuecomment-227871201).
        # As of RFC6265 the newer one cookie should be set into cookie store
        # what actually happens.
        # We will workaround this VK issue by resetting the remixlhk cookie to
        # the first one manually.
        for header, cookies in url_handle.headers.items():
            if header.lower() != 'set-cookie':
                continue
            if sys.version_info[0] >= 3:
                cookies = cookies.encode('iso-8859-1')
            cookies = cookies.decode('utf-8')
            remixlhk = re.search(r'remixlhk=(.+?);.*?\bdomain=(.+?)(?:[,;]|$)', cookies)
            if remixlhk:
                value, domain = remixlhk.groups()
                self._set_cookie(domain, 'remixlhk', value)
                break

        login_page = self._download_webpage(
            'https://login.vk.com/?act=login', None,
            note='Logging in',
            data=urlencode_postdata(login_form))

        if re.search(r'onLoginFailed', login_page):
            raise ExtractorError(
                'Unable to login, incorrect username and/or password', expected=True)

    def _real_initialize(self):
        self._login()


class VKIE(VKBaseIE):
    IE_NAME = 'vk'
    IE_DESC = 'VK'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:
                                (?:(?:m|new)\.)?vk\.com/video_|
                                (?:www\.)?daxab.com/
                            )
                            ext\.php\?(?P<embed_query>.*?\boid=(?P<oid>-?\d+).*?\bid=(?P<id>\d+).*)|
                            (?:
                                (?:(?:m|new)\.)?vk\.com/(?:.+?\?.*?z=)?video|
                                (?:www\.)?daxab.com/embed/
                            )
                            (?P<videoid>-?\d+_\d+)(?:.*\blist=(?P<list_id>[\da-f]+))?
                        )
                    '''
    _TESTS = [
        {
            'url': 'http://vk.com/videos-77521?z=video-77521_162222515%2Fclub77521',
            'md5': '7babad3b85ea2e91948005b1b8b0cb84',
            'info_dict': {
                'id': '-77521_162222515',
                'ext': 'mp4',
                'title': 'ProtivoGunz - Хуёвая песня',
                'uploader': 're:(?:Noize MC|Alexander Ilyashenko).*',
                'uploader_id': '-77521',
                'duration': 195,
                'timestamp': 1329049880,
                'upload_date': '20120212',
            },
        },
        {
            'url': 'http://vk.com/video205387401_165548505',
            'md5': '6c0aeb2e90396ba97035b9cbde548700',
            'info_dict': {
                'id': '205387401_165548505',
                'ext': 'mp4',
                'title': 'No name',
                'uploader': 'Tom Cruise',
                'uploader_id': '205387401',
                'duration': 9,
                'timestamp': 1374364108,
                'upload_date': '20130720',
            }
        },
        {
            'note': 'Embedded video',
            'url': 'http://vk.com/video_ext.php?oid=32194266&id=162925554&hash=7d8c2e0d5e05aeaa&hd=1',
            'md5': 'c7ce8f1f87bec05b3de07fdeafe21a0a',
            'info_dict': {
                'id': '32194266_162925554',
                'ext': 'mp4',
                'uploader': 'Vladimir Gavrin',
                'title': 'Lin Dan',
                'duration': 101,
                'upload_date': '20120730',
                'view_count': int,
            },
            'skip': 'This video has been removed from public access.',
        },
        {
            # VIDEO NOW REMOVED
            # please update if you find a video whose URL follows the same pattern
            'url': 'http://vk.com/video-8871596_164049491',
            'md5': 'a590bcaf3d543576c9bd162812387666',
            'note': 'Only available for registered users',
            'info_dict': {
                'id': '-8871596_164049491',
                'ext': 'mp4',
                'uploader': 'Триллеры',
                'title': '► Бойцовский клуб / Fight Club 1999 [HD 720]',
                'duration': 8352,
                'upload_date': '20121218',
                'view_count': int,
            },
            'skip': 'Requires vk account credentials',
        },
        {
            'url': 'http://vk.com/hd_kino_mania?z=video-43215063_168067957%2F15c66b9b533119788d',
            'md5': '4d7a5ef8cf114dfa09577e57b2993202',
            'info_dict': {
                'id': '-43215063_168067957',
                'ext': 'mp4',
                'uploader': 'Киномания - лучшее из мира кино',
                'title': ' ',
                'duration': 7291,
                'upload_date': '20140328',
            },
            'skip': 'Requires vk account credentials',
        },
        {
            'url': 'http://m.vk.com/video-43215063_169084319?list=125c627d1aa1cebb83&from=wall-43215063_2566540',
            'md5': '0c45586baa71b7cb1d0784ee3f4e00a6',
            'note': 'ivi.ru embed',
            'info_dict': {
                'id': '-43215063_169084319',
                'ext': 'mp4',
                'title': 'Книга Илая',
                'duration': 6771,
                'upload_date': '20140626',
                'view_count': int,
            },
            'skip': 'Only works from Russia',
        },
        {
            # video (removed?) only available with list id
            'url': 'https://vk.com/video30481095_171201961?list=8764ae2d21f14088d4',
            'md5': '091287af5402239a1051c37ec7b92913',
            'info_dict': {
                'id': '30481095_171201961',
                'ext': 'mp4',
                'title': 'ТюменцевВВ_09.07.2015',
                'uploader': 'Anton Ivanov',
                'duration': 109,
                'upload_date': '20150709',
                'view_count': int,
            },
            'skip': 'Removed',
        },
        {
            # youtube embed
            'url': 'https://vk.com/video276849682_170681728',
            'info_dict': {
                'id': 'V3K4mi0SYkc',
                'ext': 'mp4',
                'title': "DSWD Awards 'Children's Joy Foundation, Inc.' Certificate of Registration and License to Operate",
                'description': 'md5:bf9c26cfa4acdfb146362682edd3827a',
                'duration': 178,
                'upload_date': '20130116',
                'uploader': "Children's Joy Foundation Inc.",
                'uploader_id': 'thecjf',
                'view_count': int,
            },
        },
        {
            # dailymotion embed
            'url': 'https://vk.com/video-37468416_456239855',
            'info_dict': {
                'id': 'k3lz2cmXyRuJQSjGHUv',
                'ext': 'mp4',
                'title': 'md5:d52606645c20b0ddbb21655adaa4f56f',
                # TODO: fix test by fixing dailymotion description extraction
                'description': 'md5:c651358f03c56f1150b555c26d90a0fd',
                'uploader': 'AniLibria.Tv',
                'upload_date': '20160914',
                'uploader_id': 'x1p5vl5',
                'timestamp': 1473877246,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # video key is extra_data not url\d+
            'url': 'http://vk.com/video-110305615_171782105',
            'md5': 'e13fcda136f99764872e739d13fac1d1',
            'info_dict': {
                'id': '-110305615_171782105',
                'ext': 'mp4',
                'title': 'S-Dance, репетиции к The way show',
                'uploader': 'THE WAY SHOW | 17 апреля',
                'uploader_id': '-110305615',
                'timestamp': 1454859345,
                'upload_date': '20160207',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # finished live stream, postlive_mp4
            'url': 'https://vk.com/videos-387766?z=video-387766_456242764%2Fpl_-387766_-2',
            'info_dict': {
                'id': '-387766_456242764',
                'ext': 'mp4',
                'title': 'ИгроМир 2016 День 1 — Игромания Утром',
                'uploader': 'Игромания',
                'duration': 5239,
                # TODO: use act=show to extract view_count
                # 'view_count': int,
                'upload_date': '20160929',
                'uploader_id': '-387766',
                'timestamp': 1475137527,
            },
        },
        {
            # live stream, hls and rtmp links, most likely already finished live
            # stream by the time you are reading this comment
            'url': 'https://vk.com/video-140332_456239111',
            'only_matching': True,
        },
        {
            # removed video, just testing that we match the pattern
            'url': 'http://vk.com/feed?z=video-43215063_166094326%2Fbb50cacd3177146d7a',
            'only_matching': True,
        },
        {
            # age restricted video, requires vk account credentials
            'url': 'https://vk.com/video205387401_164765225',
            'only_matching': True,
        },
        {
            # pladform embed
            'url': 'https://vk.com/video-76116461_171554880',
            'only_matching': True,
        },
        {
            'url': 'http://new.vk.com/video205387401_165548505',
            'only_matching': True,
        },
        {
            # This video is no longer available, because its author has been blocked.
            'url': 'https://vk.com/video-10639516_456240611',
            'only_matching': True,
        },
        {
            # The video is not available in your region.
            'url': 'https://vk.com/video-51812607_171445436',
            'only_matching': True,
        }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        if video_id:
            info_url = 'https://vk.com/al_video.php?act=show_inline&al=1&video=' + video_id
            # Some videos (removed?) can only be downloaded with list id specified
            list_id = mobj.group('list_id')
            if list_id:
                info_url += '&list=%s' % list_id
        else:
            info_url = 'http://vk.com/video_ext.php?' + mobj.group('embed_query')
            video_id = '%s_%s' % (mobj.group('oid'), mobj.group('id'))

        info_page = self._download_webpage(info_url, video_id)

        error_message = self._html_search_regex(
            [r'(?s)<!><div[^>]+class="video_layer_message"[^>]*>(.+?)</div>',
                r'(?s)<div[^>]+id="video_ext_msg"[^>]*>(.+?)</div>'],
            info_page, 'error message', default=None)
        if error_message:
            raise ExtractorError(error_message, expected=True)

        if re.search(r'<!>/login\.php\?.*\bact=security_check', info_page):
            raise ExtractorError(
                'You are trying to log in from an unusual location. You should confirm ownership at vk.com to log in with this IP.',
                expected=True)

        ERROR_COPYRIGHT = 'Video %s has been removed from public access due to rightholder complaint.'

        ERRORS = {
            r'>Видеозапись .*? была изъята из публичного доступа в связи с обращением правообладателя.<':
            ERROR_COPYRIGHT,

            r'>The video .*? was removed from public access by request of the copyright holder.<':
            ERROR_COPYRIGHT,

            r'<!>Please log in or <':
            'Video %s is only available for registered users, '
            'use --username and --password options to provide account credentials.',

            r'<!>Unknown error':
            'Video %s does not exist.',

            r'<!>Видео временно недоступно':
            'Video %s is temporarily unavailable.',

            r'<!>Access denied':
            'Access denied to video %s.',

            r'<!>Видеозапись недоступна, так как её автор был заблокирован.':
            'Video %s is no longer available, because its author has been blocked.',

            r'<!>This video is no longer available, because its author has been blocked.':
            'Video %s is no longer available, because its author has been blocked.',

            r'<!>This video is no longer available, because it has been deleted.':
            'Video %s is no longer available, because it has been deleted.',

            r'<!>The video .+? is not available in your region.':
            'Video %s is not available in your region.',
        }

        for error_re, error_msg in ERRORS.items():
            if re.search(error_re, info_page):
                raise ExtractorError(error_msg % video_id, expected=True)

        youtube_url = YoutubeIE._extract_url(info_page)
        if youtube_url:
            return self.url_result(youtube_url, ie=YoutubeIE.ie_key())

        vimeo_url = VimeoIE._extract_url(url, info_page)
        if vimeo_url is not None:
            return self.url_result(vimeo_url)

        pladform_url = PladformIE._extract_url(info_page)
        if pladform_url:
            return self.url_result(pladform_url)

        m_rutube = re.search(
            r'\ssrc="((?:https?:)?//rutube\.ru\\?/(?:video|play)\\?/embed(?:.*?))\\?"', info_page)
        if m_rutube is not None:
            rutube_url = self._proto_relative_url(
                m_rutube.group(1).replace('\\', ''))
            return self.url_result(rutube_url)

        dailymotion_urls = DailymotionIE._extract_urls(info_page)
        if dailymotion_urls:
            return self.url_result(dailymotion_urls[0], DailymotionIE.ie_key())

        m_opts = re.search(r'(?s)var\s+opts\s*=\s*({.+?});', info_page)
        if m_opts:
            m_opts_url = re.search(r"url\s*:\s*'((?!/\b)[^']+)", m_opts.group(1))
            if m_opts_url:
                opts_url = m_opts_url.group(1)
                if opts_url.startswith('//'):
                    opts_url = 'http:' + opts_url
                return self.url_result(opts_url)

        # vars does not look to be served anymore since 24.10.2016
        data = self._parse_json(
            self._search_regex(
                r'var\s+vars\s*=\s*({.+?});', info_page, 'vars', default='{}'),
            video_id, fatal=False)

        # <!json> is served instead
        if not data:
            data = self._parse_json(
                self._search_regex(
                    [r'<!json>\s*({.+?})\s*<!>', r'<!json>\s*({.+})'],
                    info_page, 'json', default='{}'),
                video_id)
            if data:
                data = data['player']['params'][0]

        if not data:
            data = self._parse_json(
                self._search_regex(
                    r'var\s+playerParams\s*=\s*({.+?})\s*;\s*\n', info_page,
                    'player params'),
                video_id)['params'][0]

        title = unescapeHTML(data['md_title'])

        # 2 = live
        # 3 = post live (finished live)
        is_live = data.get('live') == 2
        if is_live:
            title = self._live_title(title)

        timestamp = unified_timestamp(self._html_search_regex(
            r'class=["\']mv_info_date[^>]+>([^<]+)(?:<|from)', info_page,
            'upload date', default=None)) or int_or_none(data.get('date'))

        view_count = str_to_int(self._search_regex(
            r'class=["\']mv_views_count[^>]+>\s*([\d,.]+)',
            info_page, 'view count', default=None))

        formats = []
        for format_id, format_url in data.items():
            format_url = url_or_none(format_url)
            if not format_url or not format_url.startswith(('http', '//', 'rtmp')):
                continue
            if (format_id.startswith(('url', 'cache'))
                    or format_id in ('extra_data', 'live_mp4', 'postlive_mp4')):
                height = int_or_none(self._search_regex(
                    r'^(?:url|cache)(\d+)', format_id, 'height', default=None))
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'height': height,
                })
            elif format_id == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False, live=is_live))
            elif format_id == 'rtmp':
                formats.append({
                    'format_id': format_id,
                    'url': format_url,
                    'ext': 'flv',
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': data.get('jpg'),
            'uploader': data.get('md_author'),
            'uploader_id': str_or_none(data.get('author_id')),
            'duration': data.get('duration'),
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': int_or_none(data.get('liked')),
            'dislike_count': int_or_none(data.get('nolikes')),
            'is_live': is_live,
        }


class VKUserVideosIE(VKBaseIE):
    IE_NAME = 'vk:uservideos'
    IE_DESC = "VK - User's Videos"
    _VALID_URL = r'https?://(?:(?:m|new)\.)?vk\.com/videos(?P<id>-?[0-9]+)(?!\?.*\bz=video)(?:[/?#&]|$)'
    _TEMPLATE_URL = 'https://vk.com/videos'
    _TESTS = [{
        'url': 'http://vk.com/videos205387401',
        'info_dict': {
            'id': '205387401',
            'title': "Tom Cruise's Videos",
        },
        'playlist_mincount': 4,
    }, {
        'url': 'http://vk.com/videos-77521',
        'only_matching': True,
    }, {
        'url': 'http://vk.com/videos-97664626?section=all',
        'only_matching': True,
    }, {
        'url': 'http://m.vk.com/videos205387401',
        'only_matching': True,
    }, {
        'url': 'http://new.vk.com/videos205387401',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        page_id = self._match_id(url)

        webpage = self._download_webpage(url, page_id)

        entries = [
            self.url_result(
                'http://vk.com/video' + video_id, 'VK', video_id=video_id)
            for video_id in orderedSet(re.findall(r'href="/video(-?[0-9_]+)"', webpage))]

        title = unescapeHTML(self._search_regex(
            r'<title>\s*([^<]+?)\s+\|\s+\d+\s+videos',
            webpage, 'title', default=page_id))

        return self.playlist_result(entries, page_id, title)


class VKWallPostIE(VKBaseIE):
    IE_NAME = 'vk:wallpost'
    _VALID_URL = r'https?://(?:(?:(?:(?:m|new)\.)?vk\.com/(?:[^?]+\?.*\bw=)?wall(?P<id>-?\d+_\d+)))'
    _TESTS = [{
        # public page URL, audio playlist
        'url': 'https://vk.com/bs.official?w=wall-23538238_35',
        'info_dict': {
            'id': '23538238_35',
            'title': 'Black Shadow - Wall post 23538238_35',
            'description': 'md5:3f84b9c4f9ef499731cf1ced9998cc0c',
        },
        'playlist': [{
            'md5': '5ba93864ec5b85f7ce19a9af4af080f6',
            'info_dict': {
                'id': '135220665_111806521',
                'ext': 'mp3',
                'title': 'Black Shadow - Слепое Верование',
                'duration': 370,
                'uploader': 'Black Shadow',
                'artist': 'Black Shadow',
                'track': 'Слепое Верование',
            },
        }, {
            'md5': '4cc7e804579122b17ea95af7834c9233',
            'info_dict': {
                'id': '135220665_111802303',
                'ext': 'mp3',
                'title': 'Black Shadow - Война - Негасимое Бездны Пламя!',
                'duration': 423,
                'uploader': 'Black Shadow',
                'artist': 'Black Shadow',
                'track': 'Война - Негасимое Бездны Пламя!',
            },
            'params': {
                'skip_download': True,
            },
        }],
        'params': {
            'usenetrc': True,
        },
        'skip': 'Requires vk account credentials',
    }, {
        # single YouTube embed, no leading -
        'url': 'https://vk.com/wall85155021_6319',
        'info_dict': {
            'id': '85155021_6319',
            'title': 'Sergey Gorbunov - Wall post 85155021_6319',
        },
        'playlist_count': 1,
        'params': {
            'usenetrc': True,
        },
        'skip': 'Requires vk account credentials',
    }, {
        # wall page URL
        'url': 'https://vk.com/wall-23538238_35',
        'only_matching': True,
    }, {
        # mobile wall page URL
        'url': 'https://m.vk.com/wall-23538238_35',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        post_id = self._match_id(url)

        wall_url = 'https://vk.com/wall%s' % post_id

        post_id = remove_start(post_id, '-')

        webpage = self._download_webpage(wall_url, post_id)

        error = self._html_search_regex(
            r'>Error</div>\s*<div[^>]+class=["\']body["\'][^>]*>([^<]+)',
            webpage, 'error', default=None)
        if error:
            raise ExtractorError('VK said: %s' % error, expected=True)

        description = clean_html(get_element_by_class('wall_post_text', webpage))
        uploader = clean_html(get_element_by_class('author', webpage))
        thumbnail = self._og_search_thumbnail(webpage)

        entries = []

        audio_ids = re.findall(r'data-full-id=["\'](\d+_\d+)', webpage)
        if audio_ids:
            al_audio = self._download_webpage(
                'https://vk.com/al_audio.php', post_id,
                note='Downloading audio info', fatal=False,
                data=urlencode_postdata({
                    'act': 'reload_audio',
                    'al': '1',
                    'ids': ','.join(audio_ids)
                }))
            if al_audio:
                Audio = collections.namedtuple(
                    'Audio', ['id', 'user_id', 'url', 'track', 'artist', 'duration'])
                audios = self._parse_json(
                    self._search_regex(
                        r'<!json>(.+?)<!>', al_audio, 'audios', default='[]'),
                    post_id, fatal=False, transform_source=unescapeHTML)
                if isinstance(audios, list):
                    for audio in audios:
                        a = Audio._make(audio[:6])
                        entries.append({
                            'id': '%s_%s' % (a.user_id, a.id),
                            'url': a.url,
                            'title': '%s - %s' % (a.artist, a.track) if a.artist and a.track else a.id,
                            'thumbnail': thumbnail,
                            'duration': a.duration,
                            'uploader': uploader,
                            'artist': a.artist,
                            'track': a.track,
                        })

        for video in re.finditer(
                r'<a[^>]+href=(["\'])(?P<url>/video(?:-?[\d_]+).*?)\1', webpage):
            entries.append(self.url_result(
                compat_urlparse.urljoin(url, video.group('url')), VKIE.ie_key()))

        title = 'Wall post %s' % post_id

        return self.playlist_result(
            orderedSet(entries), post_id,
            '%s - %s' % (uploader, title) if uploader else title,
            description)
