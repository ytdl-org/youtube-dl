# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request,
    compat_urllib_parse,
    compat_str,
    unescapeHTML,
    unified_strdate,
    orderedSet)


class VKIE(InfoExtractor):
    IE_NAME = 'vk.com'
    _VALID_URL = r'https?://(?:m\.)?vk\.com/(?:video_ext\.php\?.*?\boid=(?P<oid>-?\d+).*?\bid=(?P<id>\d+)|(?:.+?\?.*?z=)?video(?P<videoid>[^s].*?)(?:\?|%2F|$))'
    _NETRC_MACHINE = 'vk'

    _TESTS = [
        {
            'url': 'http://vk.com/videos-77521?z=video-77521_162222515%2Fclub77521',
            'md5': '0deae91935c54e00003c2a00646315f0',
            'info_dict': {
                'id': '162222515',
                'ext': 'flv',
                'title': 'ProtivoGunz - Хуёвая песня',
                'uploader': 're:Noize MC.*',
                'duration': 195,
                'upload_date': '20120212',
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
                'upload_date': '20130721'
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
                'upload_date': '20121218'
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
            },
            'skip': 'Only works from Russia',
        },
        {
            # removed video, just testing that we match the pattern
            'url': 'http://vk.com/feed?z=video-43215063_166094326%2Fbb50cacd3177146d7a',
            'only_matching': True,
        },
    ]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'act': 'login',
            'role': 'al_frame',
            'expire': '1',
            'email': username,
            'pass': password,
        }

        request = compat_urllib_request.Request('https://login.vk.com/?act=login',
                                                compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        login_page = self._download_webpage(request, None, note='Logging in as %s' % username)

        if re.search(r'onLoginFailed', login_page):
            raise ExtractorError('Unable to login, incorrect username and/or password', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        if not video_id:
            video_id = '%s_%s' % (mobj.group('oid'), mobj.group('id'))

        info_url = 'http://vk.com/al_video.php?act=show&al=1&video=%s' % video_id
        info_page = self._download_webpage(info_url, video_id)

        ERRORS = {
            r'>Видеозапись .*? была изъята из публичного доступа в связи с обращением правообладателя.<':
            'Video %s has been removed from public access due to rightholder complaint.',

            r'<!>Please log in or <':
            'Video %s is only available for registered users, '
            'use --username and --password options to provide account credentials.',

            r'<!>Unknown error':
            'Video %s does not exist.'
        }

        for error_re, error_msg in ERRORS.items():
            if re.search(error_re, info_page):
                raise ExtractorError(error_msg % video_id, expected=True)

        m_yt = re.search(r'src="(http://www.youtube.com/.*?)"', info_page)
        if m_yt is not None:
            self.to_screen('Youtube video detected')
            return self.url_result(m_yt.group(1), 'Youtube')

        m_opts = re.search(r'(?s)var\s+opts\s*=\s*({.*?});', info_page)
        if m_opts:
            m_opts_url = re.search(r"url\s*:\s*'([^']+)", m_opts.group(1))
            if m_opts_url:
                opts_url = m_opts_url.group(1)
                if opts_url.startswith('//'):
                    opts_url = 'http:' + opts_url
                return self.url_result(opts_url)

        data_json = self._search_regex(r'var vars = ({.*?});', info_page, 'vars')
        data = json.loads(data_json)

        # Extract upload date
        upload_date = None
        mobj = re.search(r'id="mv_date_wrap".*?Added ([a-zA-Z]+ [0-9]+), ([0-9]+) at', info_page)
        if mobj is not None:
            mobj.group(1) + ' ' + mobj.group(2)
            upload_date = unified_strdate(mobj.group(1) + ' ' + mobj.group(2))

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
        }


class VKUserVideosIE(InfoExtractor):
    IE_NAME = 'vk.com:user-videos'
    IE_DESC = 'vk.com:All of a user\'s videos'
    _VALID_URL = r'https?://vk\.com/videos(?P<id>[0-9]+)(?:m\?.*)?'
    _TEMPLATE_URL = 'https://vk.com/videos'
    _TEST = {
        'url': 'http://vk.com/videos205387401',
        'playlist_mincount': 4,
    }

    def _real_extract(self, url):
        page_id = self._match_id(url)
        page = self._download_webpage(url, page_id)
        video_ids = orderedSet(
            m.group(1) for m in re.finditer(r'href="/video([0-9_]+)"', page))
        url_entries = [
            self.url_result(
                'http://vk.com/video' + video_id, 'VK', video_id=video_id)
            for video_id in video_ids]
        return self.playlist_result(url_entries, page_id)
