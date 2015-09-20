# encoding: utf-8
from __future__ import unicode_literals

import re
import json
import hashlib
import uuid

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    unified_strdate,
)


class SmotriIE(InfoExtractor):
    IE_DESC = 'Smotri.com'
    IE_NAME = 'smotri'
    _VALID_URL = r'^https?://(?:www\.)?(?:smotri\.com/video/view/\?id=|pics\.smotri\.com/(?:player|scrubber_custom8)\.swf\?file=)(?P<id>v(?P<realvideoid>[0-9]+)[a-z0-9]{4})'
    _NETRC_MACHINE = 'smotri'

    _TESTS = [
        # real video id 2610366
        {
            'url': 'http://smotri.com/video/view/?id=v261036632ab',
            'md5': '2a7b08249e6f5636557579c368040eb9',
            'info_dict': {
                'id': 'v261036632ab',
                'ext': 'mp4',
                'title': 'катастрофа с камер видеонаблюдения',
                'uploader': 'rbc2008',
                'uploader_id': 'rbc08',
                'upload_date': '20131118',
                'thumbnail': 'http://frame6.loadup.ru/8b/a9/2610366.3.3.jpg',
            },
        },
        # real video id 57591
        {
            'url': 'http://smotri.com/video/view/?id=v57591cb20',
            'md5': '830266dfc21f077eac5afd1883091bcd',
            'info_dict': {
                'id': 'v57591cb20',
                'ext': 'flv',
                'title': 'test',
                'uploader': 'Support Photofile@photofile',
                'uploader_id': 'support-photofile',
                'upload_date': '20070704',
                'thumbnail': 'http://frame4.loadup.ru/03/ed/57591.2.3.jpg',
            },
        },
        # video-password, not approved by moderator
        {
            'url': 'http://smotri.com/video/view/?id=v1390466a13c',
            'md5': 'f6331cef33cad65a0815ee482a54440b',
            'info_dict': {
                'id': 'v1390466a13c',
                'ext': 'mp4',
                'title': 'TOCCA_A_NOI_-_LE_COSE_NON_VANNO_CAMBIAMOLE_ORA-1',
                'uploader': 'timoxa40',
                'uploader_id': 'timoxa40',
                'upload_date': '20100404',
                'thumbnail': 'http://frame7.loadup.ru/af/3f/1390466.3.3.jpg',
            },
            'params': {
                'videopassword': 'qwerty',
            },
            'skip': 'Video is not approved by moderator',
        },
        # video-password
        {
            'url': 'http://smotri.com/video/view/?id=v6984858774#',
            'md5': 'f11e01d13ac676370fc3b95b9bda11b0',
            'info_dict': {
                'id': 'v6984858774',
                'ext': 'mp4',
                'title': 'Дача Солженицина ПАРОЛЬ 223322',
                'uploader': 'psavari1',
                'uploader_id': 'psavari1',
                'upload_date': '20081103',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'videopassword': '223322',
            },
        },
        # age limit + video-password, not approved by moderator
        {
            'url': 'http://smotri.com/video/view/?id=v15408898bcf',
            'md5': '91e909c9f0521adf5ee86fbe073aad70',
            'info_dict': {
                'id': 'v15408898bcf',
                'ext': 'flv',
                'title': 'этот ролик не покажут по ТВ',
                'uploader': 'zzxxx',
                'uploader_id': 'ueggb',
                'upload_date': '20101001',
                'thumbnail': 'http://frame3.loadup.ru/75/75/1540889.1.3.jpg',
                'age_limit': 18,
            },
            'params': {
                'videopassword': '333'
            },
            'skip': 'Video is not approved by moderator',
        },
        # age limit + video-password
        {
            'url': 'http://smotri.com/video/view/?id=v7780025814',
            'md5': 'b4599b068422559374a59300c5337d72',
            'info_dict': {
                'id': 'v7780025814',
                'ext': 'mp4',
                'title': 'Sexy Beach (пароль 123)',
                'uploader': 'вАся',
                'uploader_id': 'asya_prosto',
                'upload_date': '20081218',
                'thumbnail': 're:^https?://.*\.jpg$',
                'age_limit': 18,
            },
            'params': {
                'videopassword': '123'
            },
        },
        # swf player
        {
            'url': 'http://pics.smotri.com/scrubber_custom8.swf?file=v9188090500',
            'md5': '31099eeb4bc906712c5f40092045108d',
            'info_dict': {
                'id': 'v9188090500',
                'ext': 'mp4',
                'title': 'Shakira - Don\'t Bother',
                'uploader': 'HannahL',
                'uploader_id': 'lisaha95',
                'upload_date': '20090331',
                'thumbnail': 'http://frame8.loadup.ru/44/0b/918809.7.3.jpg',
            },
        },
    ]

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(
            r'<embed[^>]src=(["\'])(?P<url>http://pics\.smotri\.com/(?:player|scrubber_custom8)\.swf\?file=v.+?\1)',
            webpage)
        if mobj is not None:
            return mobj.group('url')

        mobj = re.search(
            r'''(?x)<div\s+class="video_file">http://smotri\.com/video/download/file/[^<]+</div>\s*
                    <div\s+class="video_image">[^<]+</div>\s*
                    <div\s+class="video_id">(?P<id>[^<]+)</div>''', webpage)
        if mobj is not None:
            return 'http://smotri.com/video/view/?id=%s' % mobj.group('id')

    def _search_meta(self, name, html, display_name=None):
        if display_name is None:
            display_name = name
        return self._html_search_meta(name, html, display_name)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_form = {
            'ticket': video_id,
            'video_url': '1',
            'frame_url': '1',
            'devid': 'LoadupFlashPlayer',
            'getvideoinfo': '1',
        }

        video_password = self._downloader.params.get('videopassword', None)
        if video_password:
            video_form['pass'] = hashlib.md5(video_password.encode('utf-8')).hexdigest()

        request = compat_urllib_request.Request(
            'http://smotri.com/video/view/url/bot/', compat_urllib_parse.urlencode(video_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        video = self._download_json(request, video_id, 'Downloading video JSON')

        video_url = video.get('_vidURL') or video.get('_vidURL_mp4')

        if not video_url:
            if video.get('_moderate_no'):
                raise ExtractorError(
                    'Video %s has not been approved by moderator' % video_id, expected=True)

            if video.get('error'):
                raise ExtractorError('Video %s does not exist' % video_id, expected=True)

            if video.get('_pass_protected') == 1:
                msg = ('Invalid video password' if video_password
                       else 'This video is protected by a password, use the --video-password option')
                raise ExtractorError(msg, expected=True)

        title = video['title']
        thumbnail = video['_imgURL']
        upload_date = unified_strdate(video['added'])
        uploader = video['userNick']
        uploader_id = video['userLogin']
        duration = int_or_none(video['duration'])

        # Video JSON does not provide enough meta data
        # We will extract some from the video web page instead
        webpage_url = 'http://smotri.com/video/view/?id=%s' % video_id
        webpage = self._download_webpage(webpage_url, video_id, 'Downloading video page')

        # Warning if video is unavailable
        warning = self._html_search_regex(
            r'<div class="videoUnModer">(.*?)</div>', webpage,
            'warning message', default=None)
        if warning is not None:
            self._downloader.report_warning(
                'Video %s may not be available; smotri said: %s ' %
                (video_id, warning))

        # Adult content
        if re.search('EroConfirmText">', webpage) is not None:
            self.report_age_confirmation()
            confirm_string = self._html_search_regex(
                r'<a href="/video/view/\?id=%s&confirm=([^"]+)" title="[^"]+">' % video_id,
                webpage, 'confirm string')
            confirm_url = webpage_url + '&confirm=%s' % confirm_string
            webpage = self._download_webpage(confirm_url, video_id, 'Downloading video page (age confirmed)')
            adult_content = True
        else:
            adult_content = False

        view_count = self._html_search_regex(
            'Общее количество просмотров.*?<span class="Number">(\\d+)</span>',
            webpage, 'view count', fatal=False, flags=re.MULTILINE | re.DOTALL)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': int_or_none(view_count),
            'age_limit': 18 if adult_content else 0,
        }


class SmotriCommunityIE(InfoExtractor):
    IE_DESC = 'Smotri.com community videos'
    IE_NAME = 'smotri:community'
    _VALID_URL = r'^https?://(?:www\.)?smotri\.com/community/video/(?P<communityid>[0-9A-Za-z_\'-]+)'
    _TEST = {
        'url': 'http://smotri.com/community/video/kommuna',
        'info_dict': {
            'id': 'kommuna',
            'title': 'КПРФ',
        },
        'playlist_mincount': 4,
    }

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
    _TESTS = [{
        'url': 'http://smotri.com/user/inspector',
        'info_dict': {
            'id': 'inspector',
            'title': 'Inspector',
        },
        'playlist_mincount': 9,
    }]

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
            raise ExtractorError(
                'Broadcast %s does not exist' % broadcast_id, expected=True)

        # Adult content
        if re.search('EroConfirmText">', broadcast_page) is not None:

            (username, password) = self._get_login_info()
            if username is None:
                self.raise_login_required('Erotic broadcasts allowed only for registered users')

            login_form = {
                'login-hint53': '1',
                'confirm_erotic': '1',
                'login': username,
                'password': password,
            }

            request = compat_urllib_request.Request(
                broadcast_url + '/?no_redirect=1', compat_urllib_parse.urlencode(login_form))
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            broadcast_page = self._download_webpage(
                request, broadcast_id, 'Logging in and confirming age')

            if re.search('>Неверный логин или пароль<', broadcast_page) is not None:
                raise ExtractorError('Unable to log in: bad username or password', expected=True)

            adult_content = True
        else:
            adult_content = False

        ticket = self._html_search_regex(
            r"window\.broadcast_control\.addFlashVar\('file'\s*,\s*'([^']+)'\)",
            broadcast_page, 'broadcast ticket')

        url = 'http://smotri.com/broadcast/view/url/?ticket=%s' % ticket

        broadcast_password = self._downloader.params.get('videopassword', None)
        if broadcast_password:
            url += '&pass=%s' % hashlib.md5(broadcast_password.encode('utf-8')).hexdigest()

        broadcast_json_page = self._download_webpage(
            url, broadcast_id, 'Downloading broadcast JSON')

        try:
            broadcast_json = json.loads(broadcast_json_page)

            protected_broadcast = broadcast_json['_pass_protected'] == 1
            if protected_broadcast and not broadcast_password:
                raise ExtractorError(
                    'This broadcast is protected by a password, use the --video-password option',
                    expected=True)

            broadcast_offline = broadcast_json['is_play'] == 0
            if broadcast_offline:
                raise ExtractorError('Broadcast %s is offline' % broadcast_id, expected=True)

            rtmp_url = broadcast_json['_server']
            mobj = re.search(r'^rtmp://[^/]+/(?P<app>.+)/?$', rtmp_url)
            if not mobj:
                raise ExtractorError('Unexpected broadcast rtmp URL')

            broadcast_playpath = broadcast_json['_streamName']
            broadcast_app = '%s/%s' % (mobj.group('app'), broadcast_json['_vidURL'])
            broadcast_thumbnail = broadcast_json['_imgURL']
            broadcast_title = self._live_title(broadcast_json['title'])
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
            'player_url': 'http://pics.smotri.com/broadcast_play.swf',
            'app': broadcast_app,
            'rtmp_live': True,
            'rtmp_conn': rtmp_conn,
            'is_live': True,
        }
