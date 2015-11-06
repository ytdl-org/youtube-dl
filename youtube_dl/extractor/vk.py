# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    orderedSet,
    str_to_int,
    unescapeHTML,
    unified_strdate,
)
from .vimeo import VimeoIE


class VKIE(InfoExtractor):
    IE_NAME = 'vk'
    IE_DESC = 'VK'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:m\.)?vk\.com/video_ext\.php\?.*?\boid=(?P<oid>-?\d+).*?\bid=(?P<id>\d+)|
                            (?:
                                (?:m\.)?vk\.com/(?:.+?\?.*?z=)?video|
                                (?:www\.)?biqle\.ru/watch/
                            )
                            (?P<videoid>[^s].*?)(?:\?(?:.*\blist=(?P<list_id>[\da-f]+))?|%2F|$)
                        )
                    '''
    _NETRC_MACHINE = 'vk'

    _TESTS = [
        {
            'url': 'http://vk.com/videos-77521?z=video-77521_162222515%2Fclub77521',
            'md5': '0deae91935c54e00003c2a00646315f0',
            'info_dict': {
                'id': '162222515',
                'ext': 'flv',
                'title': 'ProtivoGunz - Хуёвая песня',
                'uploader': 're:(?:Noize MC|Alexander Ilyashenko).*',
                'duration': 195,
                'upload_date': '20120212',
                'view_count': int,
            },
        },
        {
            'url': 'http://vk.com/video205387401_165548505',
            'md5': '6c0aeb2e90396ba97035b9cbde548700',
            'info_dict': {
                'id': '165548505',
                'ext': 'mp4',
                'uploader': 'Tom Cruise',
                'title': 'No name',
                'duration': 9,
                'upload_date': '20130721',
                'view_count': int,
            }
        },
        {
            'note': 'Embedded video',
            'url': 'http://vk.com/video_ext.php?oid=32194266&id=162925554&hash=7d8c2e0d5e05aeaa&hd=1',
            'md5': 'c7ce8f1f87bec05b3de07fdeafe21a0a',
            'info_dict': {
                'id': '162925554',
                'ext': 'mp4',
                'uploader': 'Vladimir Gavrin',
                'title': 'Lin Dan',
                'duration': 101,
                'upload_date': '20120730',
                'view_count': int,
            }
        },
        {
            # VIDEO NOW REMOVED
            # please update if you find a video whose URL follows the same pattern
            'url': 'http://vk.com/video-8871596_164049491',
            'md5': 'a590bcaf3d543576c9bd162812387666',
            'note': 'Only available for registered users',
            'info_dict': {
                'id': '164049491',
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
                'id': '168067957',
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
                'id': '60690',
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
                'id': '171201961',
                'ext': 'mp4',
                'title': 'ТюменцевВВ_09.07.2015',
                'uploader': 'Anton Ivanov',
                'duration': 109,
                'upload_date': '20150709',
                'view_count': int,
            },
        },
        {
            # youtube embed
            'url': 'https://vk.com/video276849682_170681728',
            'info_dict': {
                'id': 'V3K4mi0SYkc',
                'ext': 'mp4',
                'title': "DSWD Awards 'Children's Joy Foundation, Inc.' Certificate of Registration and License to Operate",
                'description': 'md5:bf9c26cfa4acdfb146362682edd3827a',
                'duration': 179,
                'upload_date': '20130116',
                'uploader': "Children's Joy Foundation",
                'uploader_id': 'thecjf',
                'view_count': int,
            },
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
            # vk wrapper
            'url': 'http://www.biqle.ru/watch/847655_160197695',
            'only_matching': True,
        }
    ]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            'https://vk.com', None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'email': username.encode('cp1251'),
            'pass': password.encode('cp1251'),
        })

        request = compat_urllib_request.Request(
            'https://login.vk.com/?act=login',
            compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        login_page = self._download_webpage(
            request, None, note='Logging in as %s' % username)

        if re.search(r'onLoginFailed', login_page):
            raise ExtractorError(
                'Unable to login, incorrect username and/or password', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        if not video_id:
            video_id = '%s_%s' % (mobj.group('oid'), mobj.group('id'))

        info_url = 'https://vk.com/al_video.php?act=show&al=1&module=video&video=%s' % video_id

        # Some videos (removed?) can only be downloaded with list id specified
        list_id = mobj.group('list_id')
        if list_id:
            info_url += '&list=%s' % list_id

        info_page = self._download_webpage(info_url, video_id)

        error_message = self._html_search_regex(
            r'(?s)<!><div[^>]+class="video_layer_message"[^>]*>(.+?)</div>',
            info_page, 'error message', default=None)
        if error_message:
            raise ExtractorError(error_message, expected=True)

        if re.search(r'<!>/login\.php\?.*\bact=security_check', info_page):
            raise ExtractorError(
                'You are trying to log in from an unusual location. You should confirm ownership at vk.com to log in with this IP.',
                expected=True)

        ERRORS = {
            r'>Видеозапись .*? была изъята из публичного доступа в связи с обращением правообладателя.<':
            'Video %s has been removed from public access due to rightholder complaint.',

            r'<!>Please log in or <':
            'Video %s is only available for registered users, '
            'use --username and --password options to provide account credentials.',

            r'<!>Unknown error':
            'Video %s does not exist.',

            r'<!>Видео временно недоступно':
            'Video %s is temporarily unavailable.',

            r'<!>Access denied':
            'Access denied to video %s.',
        }

        for error_re, error_msg in ERRORS.items():
            if re.search(error_re, info_page):
                raise ExtractorError(error_msg % video_id, expected=True)

        youtube_url = self._search_regex(
            r'<iframe[^>]+src="((?:https?:)?//www.youtube.com/embed/[^"]+)"',
            info_page, 'youtube iframe', default=None)
        if youtube_url:
            return self.url_result(youtube_url, 'Youtube')

        vimeo_url = VimeoIE._extract_vimeo_url(url, info_page)
        if vimeo_url is not None:
            return self.url_result(vimeo_url)

        m_rutube = re.search(
            r'\ssrc="((?:https?:)?//rutube\.ru\\?/video\\?/embed(?:.*?))\\?"', info_page)
        if m_rutube is not None:
            self.to_screen('rutube video detected')
            rutube_url = self._proto_relative_url(
                m_rutube.group(1).replace('\\', ''))
            return self.url_result(rutube_url)

        m_opts = re.search(r'(?s)var\s+opts\s*=\s*({.+?});', info_page)
        if m_opts:
            m_opts_url = re.search(r"url\s*:\s*'((?!/\b)[^']+)", m_opts.group(1))
            if m_opts_url:
                opts_url = m_opts_url.group(1)
                if opts_url.startswith('//'):
                    opts_url = 'http:' + opts_url
                return self.url_result(opts_url)

        data_json = self._search_regex(r'var\s+vars\s*=\s*({.+?});', info_page, 'vars')
        data = json.loads(data_json)

        # Extract upload date
        upload_date = None
        mobj = re.search(r'id="mv_date(?:_views)?_wrap"[^>]*>([a-zA-Z]+ [0-9]+), ([0-9]+) at', info_page)
        if mobj is not None:
            mobj.group(1) + ' ' + mobj.group(2)
            upload_date = unified_strdate(mobj.group(1) + ' ' + mobj.group(2))

        view_count = None
        views = self._html_search_regex(
            r'"mv_views_count_number"[^>]*>(.+?\bviews?)<',
            info_page, 'view count', fatal=False)
        if views:
            view_count = str_to_int(self._search_regex(
                r'([\d,.]+)', views, 'view count', fatal=False))

        formats = [{
            'format_id': k,
            'url': v,
            'width': int(k[len('url'):]),
        } for k, v in data.items()
            if k.startswith('url')]
        self._sort_formats(formats)

        return {
            'id': compat_str(data['vid']),
            'formats': formats,
            'title': unescapeHTML(data['md_title']),
            'thumbnail': data.get('jpg'),
            'uploader': data.get('md_author'),
            'duration': data.get('duration'),
            'upload_date': upload_date,
            'view_count': view_count,
        }


class VKUserVideosIE(InfoExtractor):
    IE_NAME = 'vk:uservideos'
    IE_DESC = "VK - User's Videos"
    _VALID_URL = r'https?://vk\.com/videos(?P<id>-?[0-9]+)$'
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
