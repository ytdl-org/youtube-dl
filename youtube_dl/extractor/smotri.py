# encoding: utf-8

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
    IE_DESC = u'Smotri.com'
    IE_NAME = u'smotri'
    _VALID_URL = r'^https?://(?:www\.)?(?P<url>smotri\.com/video/view/\?id=(?P<videoid>v(?P<realvideoid>[0-9]+)[a-z0-9]{4}))'

    _TESTS = [
        # real video id 2610366
        {
            u'url': u'http://smotri.com/video/view/?id=v261036632ab',
            u'file': u'v261036632ab.mp4',
            u'md5': u'2a7b08249e6f5636557579c368040eb9',
            u'info_dict': {
                u'title': u'катастрофа с камер видеонаблюдения',
                u'uploader': u'rbc2008',
                u'uploader_id': u'rbc08',
                u'upload_date': u'20131118',
                u'description': u'катастрофа с камер видеонаблюдения, видео катастрофа с камер видеонаблюдения',
                u'thumbnail': u'http://frame6.loadup.ru/8b/a9/2610366.3.3.jpg',
            },
        },
        # real video id 57591
        {
            u'url': u'http://smotri.com/video/view/?id=v57591cb20',
            u'file': u'v57591cb20.flv',
            u'md5': u'830266dfc21f077eac5afd1883091bcd',
            u'info_dict': {
                u'title': u'test',
                u'uploader': u'Support Photofile@photofile',
                u'uploader_id': u'support-photofile',
                u'upload_date': u'20070704',
                u'description': u'test, видео test',
                u'thumbnail': u'http://frame4.loadup.ru/03/ed/57591.2.3.jpg',
            },
        },
        # video-password
        {
            u'url': u'http://smotri.com/video/view/?id=v1390466a13c',
            u'file': u'v1390466a13c.mp4',
            u'md5': u'f6331cef33cad65a0815ee482a54440b',
            u'info_dict': {
                u'title': u'TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1',
                u'uploader': u'timoxa40',
                u'uploader_id': u'timoxa40',
                u'upload_date': u'20100404',
                u'thumbnail': u'http://frame7.loadup.ru/af/3f/1390466.3.3.jpg',
                u'description': u'TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1, видео TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1',
            },
            u'params': {
                u'videopassword': u'qwerty',
            },
        },
        # age limit + video-password
        {
            u'url': u'http://smotri.com/video/view/?id=v15408898bcf',
            u'file': u'v15408898bcf.flv',
            u'md5': u'91e909c9f0521adf5ee86fbe073aad70',
            u'info_dict': {
                u'title': u'этот ролик не покажут по ТВ',
                u'uploader': u'zzxxx',
                u'uploader_id': u'ueggb',
                u'upload_date': u'20101001',
                u'thumbnail': u'http://frame3.loadup.ru/75/75/1540889.1.3.jpg',
                u'age_limit': 18,
                u'description': u'этот ролик не покажут по ТВ, видео этот ролик не покажут по ТВ',
            },
            u'params': {
                u'videopassword': u'333'
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
        video_json_page = self._download_webpage(video_json_url, video_id, u'Downloading video JSON')
        video_json = json.loads(video_json_page)
        
        status = video_json['status']
        if status == self._VIDEO_NOT_FOUND:
            raise ExtractorError(u'Video %s does not exist' % video_id, expected=True)
        elif status == self._PASSWORD_DETECTED:  # The video is protected by a password, retry with
                                                # video-password set
            video_password = self._downloader.params.get('videopassword', None)
            if not video_password:
                raise ExtractorError(u'This video is protected by a password, use the --video-password option', expected=True)
            video_json_url += '&md5pass=%s' % hashlib.md5(video_password.encode('utf-8')).hexdigest()
            video_json_page = self._download_webpage(video_json_url, video_id, u'Downloading video JSON (video-password set)')
            video_json = json.loads(video_json_page)
            status = video_json['status']
            if status == self._PASSWORD_NOT_VERIFIED:
                raise ExtractorError(u'Video password is invalid', expected=True)
        
        if status != self._SUCCESS:
            raise ExtractorError(u'Unexpected status value %s' % status)
        
        # Extract the URL of the video
        video_url = video_json['file_data']
        
        # Video JSON does not provide enough meta data
        # We will extract some from the video web page instead
        video_page_url = 'http://' + mobj.group('url')
        video_page = self._download_webpage(video_page_url, video_id, u'Downloading video page')

        # Warning if video is unavailable
        warning = self._html_search_regex(
            r'<div class="videoUnModer">(.*?)</div>', video_page,
            u'warning message', default=None)
        if warning is not None:
            self._downloader.report_warning(
                u'Video %s may not be available; smotri said: %s ' %
                (video_id, warning))

        # Adult content
        if re.search(u'EroConfirmText">', video_page) is not None:
            self.report_age_confirmation()
            confirm_string = self._html_search_regex(
                r'<a href="/video/view/\?id=%s&confirm=([^"]+)" title="[^"]+">' % video_id,
                video_page, u'confirm string')
            confirm_url = video_page_url + '&confirm=%s' % confirm_string
            video_page = self._download_webpage(confirm_url, video_id, u'Downloading video page (age confirmed)')
            adult_content = True
        else:
            adult_content = False
        
        # Extract the rest of meta data
        video_title = self._search_meta(u'name', video_page, u'title')
        if not video_title:
            video_title = os.path.splitext(url_basename(video_url))[0]

        video_description = self._search_meta(u'description', video_page)
        END_TEXT = u' на сайте Smotri.com'
        if video_description and video_description.endswith(END_TEXT):
            video_description = video_description[:-len(END_TEXT)]
        START_TEXT = u'Смотреть онлайн ролик '
        if video_description and video_description.startswith(START_TEXT):
            video_description = video_description[len(START_TEXT):]
        video_thumbnail = self._search_meta(u'thumbnail', video_page)

        upload_date_str = self._search_meta(u'uploadDate', video_page, u'upload date')
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
        
        duration_str = self._search_meta(u'duration', video_page)
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
            u'<div class="DescrUser"><div>Автор.*?onmouseover="popup_user_info[^"]+">(.*?)</a>',
            video_page, u'uploader', fatal=False, flags=re.MULTILINE|re.DOTALL)
        
        video_uploader_id = self._html_search_regex(
            u'<div class="DescrUser"><div>Автор.*?onmouseover="popup_user_info\\(.*?\'([^\']+)\'\\);">',
            video_page, u'uploader id', fatal=False, flags=re.MULTILINE|re.DOTALL)
        
        video_view_count = self._html_search_regex(
            u'Общее количество просмотров.*?<span class="Number">(\\d+)</span>',
            video_page, u'view count', fatal=False, flags=re.MULTILINE|re.DOTALL)
                
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
    IE_DESC = u'Smotri.com community videos'
    IE_NAME = u'smotri:community'
    _VALID_URL = r'^https?://(?:www\.)?smotri\.com/community/video/(?P<communityid>[0-9A-Za-z_\'-]+)'
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        community_id = mobj.group('communityid')

        url = 'http://smotri.com/export/rss/video/by/community/-/%s/video.xml' % community_id
        rss = self._download_xml(url, community_id, u'Downloading community RSS')

        entries = [self.url_result(video_url.text, 'Smotri')
                   for video_url in rss.findall('./channel/item/link')]

        description_text = rss.find('./channel/description').text
        community_title = self._html_search_regex(
            u'^Видео сообщества "([^"]+)"$', description_text, u'community title')

        return self.playlist_result(entries, community_id, community_title)


class SmotriUserIE(InfoExtractor):
    IE_DESC = u'Smotri.com user videos'
    IE_NAME = u'smotri:user'
    _VALID_URL = r'^https?://(?:www\.)?smotri\.com/user/(?P<userid>[0-9A-Za-z_\'-]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user_id = mobj.group('userid')

        url = 'http://smotri.com/export/rss/user/video/-/%s/video.xml' % user_id
        rss = self._download_xml(url, user_id, u'Downloading user RSS')

        entries = [self.url_result(video_url.text, 'Smotri')
                   for video_url in rss.findall('./channel/item/link')]

        description_text = rss.find('./channel/description').text
        user_nickname = self._html_search_regex(
            u'^Видео режиссера (.*)$', description_text,
            u'user nickname')

        return self.playlist_result(entries, user_id, user_nickname)


class SmotriBroadcastIE(InfoExtractor):
    IE_DESC = u'Smotri.com broadcasts'
    IE_NAME = u'smotri:broadcast'
    _VALID_URL = r'^https?://(?:www\.)?(?P<url>smotri\.com/live/(?P<broadcastid>[^/]+))/?.*'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        broadcast_id = mobj.group('broadcastid')

        broadcast_url = 'http://' + mobj.group('url')
        broadcast_page = self._download_webpage(broadcast_url, broadcast_id, u'Downloading broadcast page')

        if re.search(u'>Режиссер с логином <br/>"%s"<br/> <span>не существует<' % broadcast_id, broadcast_page) is not None:
            raise ExtractorError(u'Broadcast %s does not exist' % broadcast_id, expected=True)

        # Adult content
        if re.search(u'EroConfirmText">', broadcast_page) is not None:

            (username, password) = self._get_login_info()
            if username is None:
                raise ExtractorError(u'Erotic broadcasts allowed only for registered users, '
                    u'use --username and --password options to provide account credentials.', expected=True)

            # Log in
            login_form_strs = {
                u'login-hint53': '1',
                u'confirm_erotic': '1',
                u'login': username,
                u'password': password,
            }
            # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
            # chokes on unicode
            login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k,v in login_form_strs.items())
            login_data = compat_urllib_parse.urlencode(login_form).encode('utf-8')
            login_url = broadcast_url + '/?no_redirect=1'
            request = compat_urllib_request.Request(login_url, login_data)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            broadcast_page = self._download_webpage(
                request, broadcast_id, note=u'Logging in and confirming age')

            if re.search(u'>Неверный логин или пароль<', broadcast_page) is not None:
                raise ExtractorError(u'Unable to log in: bad username or password', expected=True)

            adult_content = True
        else:
            adult_content = False

        ticket = self._html_search_regex(
            u'window\.broadcast_control\.addFlashVar\\(\'file\', \'([^\']+)\'\\);',
            broadcast_page, u'broadcast ticket')

        url = 'http://smotri.com/broadcast/view/url/?ticket=%s' % ticket

        broadcast_password = self._downloader.params.get('videopassword', None)
        if broadcast_password:
            url += '&pass=%s' % hashlib.md5(broadcast_password.encode('utf-8')).hexdigest()

        broadcast_json_page = self._download_webpage(url, broadcast_id, u'Downloading broadcast JSON')

        try:
            broadcast_json = json.loads(broadcast_json_page)

            protected_broadcast = broadcast_json['_pass_protected'] == 1
            if protected_broadcast and not broadcast_password:
                raise ExtractorError(u'This broadcast is protected by a password, use the --video-password option', expected=True)

            broadcast_offline = broadcast_json['is_play'] == 0
            if broadcast_offline:
                raise ExtractorError(u'Broadcast %s is offline' % broadcast_id, expected=True)

            rtmp_url = broadcast_json['_server']
            if not rtmp_url.startswith('rtmp://'):
                raise ExtractorError(u'Unexpected broadcast rtmp URL')

            broadcast_playpath = broadcast_json['_streamName']
            broadcast_thumbnail = broadcast_json['_imgURL']
            broadcast_title = broadcast_json['title']
            broadcast_description = broadcast_json['description']
            broadcaster_nick = broadcast_json['nick']
            broadcaster_login = broadcast_json['login']
            rtmp_conn = 'S:%s' % uuid.uuid4().hex
        except KeyError:
            if protected_broadcast:
                raise ExtractorError(u'Bad broadcast password', expected=True)
            raise ExtractorError(u'Unexpected broadcast JSON')

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
