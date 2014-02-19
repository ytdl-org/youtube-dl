# encoding: utf-8
from __future__ import unicode_literals

import os.path
import re
import json
import hashlib
import uuid

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    ExtractorError,
    url_basename,
)


class SmotriIE(InfoExtractor):
    IE_DESC = 'Smotri.com'
    IE_NAME = 'smotri'
    _VALID_URL = r'^https?://(?:www\.)?(?P<url>smotri\.com/video/view/\?id=(?P<videoid>v(?P<realvideoid>[0-9]+)[a-z0-9]{4}))'
    _NETRC_MACHINE = 'smotri'

    _TESTS = [
        # real video id 2610366
        {
            'url': 'http://smotri.com/video/view/?id=v261036632ab',
            'file': 'v261036632ab.mp4',
            'md5': '2a7b08249e6f5636557579c368040eb9',
            'info_dict': {
                'title': 'катастрофа с камер видеонаблюдения',
                'uploader': 'rbc2008',
                'uploader_id': 'rbc08',
                'upload_date': '20131118',
                'description': 'катастрофа с камер видеонаблюдения, видео катастрофа с камер видеонаблюдения',
                'thumbnail': 'http://frame6.loadup.ru/8b/a9/2610366.3.3.jpg',
            },
        },
        # real video id 57591
        {
            'url': 'http://smotri.com/video/view/?id=v57591cb20',
            'file': 'v57591cb20.flv',
            'md5': '830266dfc21f077eac5afd1883091bcd',
            'info_dict': {
                'title': 'test',
                'uploader': 'Support Photofile@photofile',
                'uploader_id': 'support-photofile',
                'upload_date': '20070704',
                'description': 'test, видео test',
                'thumbnail': 'http://frame4.loadup.ru/03/ed/57591.2.3.jpg',
            },
        },
        # video-password
        {
            'url': 'http://smotri.com/video/view/?id=v1390466a13c',
            'file': 'v1390466a13c.mp4',
            'md5': 'f6331cef33cad65a0815ee482a54440b',
            'info_dict': {
                'title': 'TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1',
                'uploader': 'timoxa40',
                'uploader_id': 'timoxa40',
                'upload_date': '20100404',
                'thumbnail': 'http://frame7.loadup.ru/af/3f/1390466.3.3.jpg',
                'description': 'TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1, видео TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1',
            },
            'params': {
                'videopassword': 'qwerty',
            },
        },
        # age limit + video-password
        {
            'url': 'http://smotri.com/video/view/?id=v15408898bcf',
            'file': 'v15408898bcf.flv',
            'md5': '91e909c9f0521adf5ee86fbe073aad70',
            'info_dict': {
                'title': 'этот ролик не покажут по ТВ',
                'uploader': 'zzxxx',
                'uploader_id': 'ueggb',
                'upload_date': '20101001',
                'thumbnail': 'http://frame3.loadup.ru/75/75/1540889.1.3.jpg',
                'age_limit': 18,
                'description': 'этот ролик не покажут по ТВ, видео этот ролик не покажут по ТВ',
            },
            'params': {
                'videopassword': '333'
            }
        }
    ]

    _SUCCESS = 0
    _PASSWORD_NOT_VERIFIED = 1
    _PASSWORD_DETECTED = 2
    _VIDEO_NOT_FOUND = 3

    def _search_meta(self, name, html, display_name=None):
        if display_name is None:
            display_name = name
        return self._html_search_regex(
            r'<meta itemprop="%s" content="([^"]+)" />' % re.escape(name),
            html, display_name, fatal=False)
        return self._html_search_meta(name, html, display_name)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        real_video_id = mobj.group('realvideoid')

        # Download video JSON data
        video_json_url = 'http://smotri.com/vt.php?id=%s' % real_video_id
        video_json_page = self._download_webpage(video_json_url, video_id, 'Downloading video JSON')
        video_json = json.loads(video_json_page)

        status = video_json['status']
        if status == self._VIDEO_NOT_FOUND:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)
        elif status == self._PASSWORD_DETECTED: # The video is protected by a password, retry with
                                                # video-password set
            video_password = self._downloader.params.get('videopassword', None)
            if not video_password:
                raise ExtractorError('This video is protected by a password, use the --video-password option', expected=True)
            video_json_url += '&md5pass=%s' % hashlib.md5(video_password.encode('utf-8')).hexdigest()
            video_json_page = self._download_webpage(video_json_url, video_id, 'Downloading video JSON (video-password set)')
            video_json = json.loads(video_json_page)
            status = video_json['status']
            if status == self._PASSWORD_NOT_VERIFIED:
                raise ExtractorError('Video password is invalid', expected=True)

        if status != self._SUCCESS:
            raise ExtractorError('Unexpected status value %s' % status)

        # Extract the URL of the video
        video_url = video_json['file_data']

        # Video JSON does not provide enough meta data
        # We will extract some from the video web page instead
        video_page_url = 'http://' + mobj.group('url')
        video_page = self._download_webpage(video_page_url, video_id, 'Downloading video page')

        # Warning if video is unavailable
        warning = self._html_search_regex(
            r'<div class="videoUnModer">(.*?)</div>', video_page,
            'warning message', default=None)
        if warning is not None:
            self._downloader.report_warning(
                'Video %s may not be available; smotri said: %s ' %
                (video_id, warning))

        # Adult content
        if re.search('EroConfirmText">', video_page) is not None:
            self.report_age_confirmation()
            confirm_string = self._html_search_regex(
                r'<a href="/video/view/\?id=%s&confirm=([^"]+)" title="[^"]+">' % video_id,
                video_page, 'confirm string')
            confirm_url = video_page_url + '&confirm=%s' % confirm_string
            video_page = self._download_webpage(confirm_url, video_id, 'Downloading video page (age confirmed)')
            adult_content = True
        else:
            adult_content = False

        # Extract the rest of meta data
        video_title = self._search_meta('name', video_page, 'title')
        if not video_title:
            video_title = os.path.splitext(url_basename(video_url))[0]

        video_description = self._search_meta('description', video_page)
        END_TEXT = ' на сайте Smotri.com'
        if video_description and video_description.endswith(END_TEXT):
            video_description = video_description[:-len(END_TEXT)]
        START_TEXT = 'Смотреть онлайн ролик '
        if video_description and video_description.startswith(START_TEXT):
            video_description = video_description[len(START_TEXT):]
        video_thumbnail = self._search_meta('thumbnail', video_page)

        upload_date_str = self._search_meta('uploadDate', video_page, 'upload date')
        if upload_date_str:
            upload_date_m = re.search(r'(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<day>\d{2})T', upload_date_str)
            video_upload_date = (
                (
                    upload_date_m.group('year') +
                    upload_date_m.group('month') +
                    upload_date_m.group('day')
                )
                if upload_date_m else None
            )
        else:
            video_upload_date = None

        duration_str = self._search_meta('duration', video_page)
        if duration_str:
            duration_m = re.search(r'T(?P<hours>[0-9]{2})H(?P<minutes>[0-9]{2})M(?P<seconds>[0-9]{2})S', duration_str)
            video_duration = (
                (
                    (int(duration_m.group('hours')) * 60 * 60) +
                    (int(duration_m.group('minutes')) * 60) +
                    int(duration_m.group('seconds'))
                )
                if duration_m else None
            )
        else:
            video_duration = None

        video_uploader = self._html_search_regex(
            '<div class="DescrUser"><div>Автор.*?onmouseover="popup_user_info[^"]+">(.*?)</a>',
            video_page, 'uploader', fatal=False, flags=re.MULTILINE|re.DOTALL)

        video_uploader_id = self._html_search_regex(
            '<div class="DescrUser"><div>Автор.*?onmouseover="popup_user_info\\(.*?\'([^\']+)\'\\);">',
            video_page, 'uploader id', fatal=False, flags=re.MULTILINE|re.DOTALL)

        video_view_count = self._html_search_regex(
            'Общее количество просмотров.*?<span class="Number">(\\d+)</span>',
            video_page, 'view count', fatal=False, flags=re.MULTILINE|re.DOTALL)

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'description': video_description,
            'uploader': video_uploader,
            'upload_date': video_upload_date,
            'uploader_id': video_uploader_id,
            'duration': video_duration,
            'view_count': video_view_count,
            'age_limit': 18 if adult_content else 0,
            'video_page_url': video_page_url
        }


class SmotriCommunityIE(InfoExtractor):
    IE_DESC = 'Smotri.com community videos'
    IE_NAME = 'smotri:community'
    _VALID_URL = r'^https?://(?:www\.)?smotri\.com/community/video/(?P<communityid>[0-9A-Za-z_\'-]+)'
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        community_id = mobj.group('communityid')

        url = 'http://smotri.com/export/rss/video/by/community/-/%s/video.xml' % community_id
        rss = self._download_xml(url, community_id, 'Downloading community RSS')

        entries = [self.url_result(video_url.text, 'Smotri')
                   for video_url in rss.findall('./channel/item/link')]

        description_text = rss.find('./channel/description').text
        community_title = self._html_search_regex(
            '^Видео сообщества "([^"]+)"$', description_text, 'community title')

        return self.playlist_result(entries, community_id, community_title)


class SmotriUserIE(InfoExtractor):
    IE_DESC = 'Smotri.com user videos'
    IE_NAME = 'smotri:user'
    _VALID_URL = r'^https?://(?:www\.)?smotri\.com/user/(?P<userid>[0-9A-Za-z_\'-]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('userid')

        url = 'http://smotri.com/export/rss/user/video/-/%s/video.xml' % user_id
        rss = self._download_xml(url, user_id, 'Downloading user RSS')

        entries = [self.url_result(video_url.text, 'Smotri')
                   for video_url in rss.findall('./channel/item/link')]

        description_text = rss.find('./channel/description').text
        user_nickname = self._html_search_regex(
            '^Видео режиссера (.*)$', description_text,
            'user nickname')

        return self.playlist_result(entries, user_id, user_nickname)


class SmotriBroadcastIE(InfoExtractor):
    IE_DESC = 'Smotri.com broadcasts'
    IE_NAME = 'smotri:broadcast'
    _VALID_URL = r'^https?://(?:www\.)?(?P<url>smotri\.com/live/(?P<broadcastid>[^/]+))/?.*'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        broadcast_id = mobj.group('broadcastid')

        broadcast_url = 'http://' + mobj.group('url')
        broadcast_page = self._download_webpage(broadcast_url, broadcast_id, 'Downloading broadcast page')

        if re.search('>Режиссер с логином <br/>"%s"<br/> <span>не существует<' % broadcast_id, broadcast_page) is not None:
            raise ExtractorError('Broadcast %s does not exist' % broadcast_id, expected=True)

        # Adult content
        if re.search('EroConfirmText">', broadcast_page) is not None:

            (username, password) = self._get_login_info()
            if username is None:
                raise ExtractorError('Erotic broadcasts allowed only for registered users, '
                    'use --username and --password options to provide account credentials.', expected=True)

            login_form = {
                'login-hint53': '1',
                'confirm_erotic': '1',
                'login': username,
                'password': password,
            }

            request = compat_urllib_request.Request(broadcast_url + '/?no_redirect=1', compat_urllib_parse.urlencode(login_form))
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            broadcast_page = self._download_webpage(request, broadcast_id, 'Logging in and confirming age')

            if re.search('>Неверный логин или пароль<', broadcast_page) is not None:
                raise ExtractorError('Unable to log in: bad username or password', expected=True)

            adult_content = True
        else:
            adult_content = False

        ticket = self._html_search_regex(
            'window\.broadcast_control\.addFlashVar\\(\'file\', \'([^\']+)\'\\);',
            broadcast_page, 'broadcast ticket')

        url = 'http://smotri.com/broadcast/view/url/?ticket=%s' % ticket

        broadcast_password = self._downloader.params.get('videopassword', None)
        if broadcast_password:
            url += '&pass=%s' % hashlib.md5(broadcast_password.encode('utf-8')).hexdigest()

        broadcast_json_page = self._download_webpage(url, broadcast_id, 'Downloading broadcast JSON')

        try:
            broadcast_json = json.loads(broadcast_json_page)

            protected_broadcast = broadcast_json['_pass_protected'] == 1
            if protected_broadcast and not broadcast_password:
                raise ExtractorError('This broadcast is protected by a password, use the --video-password option', expected=True)

            broadcast_offline = broadcast_json['is_play'] == 0
            if broadcast_offline:
                raise ExtractorError('Broadcast %s is offline' % broadcast_id, expected=True)

            rtmp_url = broadcast_json['_server']
            if not rtmp_url.startswith('rtmp://'):
                raise ExtractorError('Unexpected broadcast rtmp URL')

            broadcast_playpath = broadcast_json['_streamName']
            broadcast_thumbnail = broadcast_json['_imgURL']
            broadcast_title = broadcast_json['title']
            broadcast_description = broadcast_json['description']
            broadcaster_nick = broadcast_json['nick']
            broadcaster_login = broadcast_json['login']
            rtmp_conn = 'S:%s' % uuid.uuid4().hex
        except KeyError:
            if protected_broadcast:
                raise ExtractorError('Bad broadcast password', expected=True)
            raise ExtractorError('Unexpected broadcast JSON')

        return {
            'id': broadcast_id,
            'url': rtmp_url,
            'title': broadcast_title,
            'thumbnail': broadcast_thumbnail,
            'description': broadcast_description,
            'uploader': broadcaster_nick,
            'uploader_id': broadcaster_login,
            'age_limit': 18 if adult_content else 0,
            'ext': 'flv',
            'play_path': broadcast_playpath,
            'rtmp_live': True,
            'rtmp_conn': rtmp_conn
        }
