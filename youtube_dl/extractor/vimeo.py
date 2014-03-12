# encoding: utf-8
from __future__ import unicode_literals

import json
import re
import itertools

from .common import InfoExtractor
from .subtitles import SubtitlesInfoExtractor
from ..utils import (
    compat_HTTPError,
    compat_urllib_parse,
    compat_urllib_request,
    clean_html,
    get_element_by_attribute,
    ExtractorError,
    RegexNotFoundError,
    std_headers,
    unsmuggle_url,
)


class VimeoIE(SubtitlesInfoExtractor):
    """Information extractor for vimeo.com."""

    # _VALID_URL matches Vimeo URLs
    _VALID_URL = r'''(?x)
        (?P<proto>(?:https?:)?//)?
        (?:(?:www|(?P<player>player))\.)?
        vimeo(?P<pro>pro)?\.com/
        (?:.*?/)?
        (?:(?:play_redirect_hls|moogaloop\.swf)\?clip_id=)?
        (?:videos?/)?
        (?P<id>[0-9]+)
        /?(?:[?&].*)?(?:[#].*)?$'''
    _NETRC_MACHINE = 'vimeo'
    IE_NAME = 'vimeo'
    _TESTS = [
        {
            'url': 'http://vimeo.com/56015672#at=0',
            'md5': '8879b6cc097e987f02484baf890129e5',
            'info_dict': {
                'id': '56015672',
                'ext': 'mp4',
                "upload_date": "20121220",
                "description": "This is a test case for youtube-dl.\nFor more information, see github.com/rg3/youtube-dl\nTest chars: \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550",
                "uploader_id": "user7108434",
                "uploader": "Filippo Valsorda",
                "title": "youtube-dl test video - \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550",
            },
        },
        {
            'url': 'http://vimeopro.com/openstreetmapus/state-of-the-map-us-2013/video/68093876',
            'file': '68093876.mp4',
            'md5': '3b5ca6aa22b60dfeeadf50b72e44ed82',
            'note': 'Vimeo Pro video (#1197)',
            'info_dict': {
                'uploader_id': 'openstreetmapus',
                'uploader': 'OpenStreetMap US',
                'title': 'Andy Allan - Putting the Carto into OpenStreetMap Cartography',
            },
        },
        {
            'url': 'http://player.vimeo.com/video/54469442',
            'file': '54469442.mp4',
            'md5': '619b811a4417aa4abe78dc653becf511',
            'note': 'Videos that embed the url in the player page',
            'info_dict': {
                'title': 'Kathy Sierra: Building the minimum Badass User, Business of Software',
                'uploader': 'The BLN & Business of Software',
                'uploader_id': 'theblnbusinessofsoftware',
            },
        },
        {
            'url': 'http://vimeo.com/68375962',
            'file': '68375962.mp4',
            'md5': 'aaf896bdb7ddd6476df50007a0ac0ae7',
            'note': 'Video protected with password',
            'info_dict': {
                'title': 'youtube-dl password protected test video',
                'upload_date': '20130614',
                'uploader_id': 'user18948128',
                'uploader': 'Jaime Marquínez Ferrándiz',
            },
            'params': {
                'videopassword': 'youtube-dl',
            },
        },
        {
            'url': 'http://vimeo.com/76979871',
            'md5': '3363dd6ffebe3784d56f4132317fd446',
            'note': 'Video with subtitles',
            'info_dict': {
                'id': '76979871',
                'ext': 'mp4',
                'title': 'The New Vimeo Player (You Know, For Videos)',
                'description': 'md5:2ec900bf97c3f389378a96aee11260ea',
                'upload_date': '20131015',
                'uploader_id': 'staff',
                'uploader': 'Vimeo Staff',
            }
        },
    ]

    @classmethod
    def suitable(cls, url):
        if VimeoChannelIE.suitable(url):
            # Otherwise channel urls like http://vimeo.com/channels/31259 would
            # match
            return False
        else:
            return super(VimeoIE, cls).suitable(url)

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        self.report_login()
        login_url = 'https://vimeo.com/log_in'
        webpage = self._download_webpage(login_url, None, False)
        token = self._search_regex(r'xsrft: \'(.*?)\'', webpage, 'login token')
        data = compat_urllib_parse.urlencode({'email': username,
                                              'password': password,
                                              'action': 'login',
                                              'service': 'vimeo',
                                              'token': token,
                                              })
        login_request = compat_urllib_request.Request(login_url, data)
        login_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        login_request.add_header('Cookie', 'xsrft=%s' % token)
        self._download_webpage(login_request, None, False, 'Wrong login info')

    def _verify_video_password(self, url, video_id, webpage):
        password = self._downloader.params.get('videopassword', None)
        if password is None:
            raise ExtractorError('This video is protected by a password, use the --video-password option')
        token = self._search_regex(r'xsrft: \'(.*?)\'', webpage, 'login token')
        data = compat_urllib_parse.urlencode({'password': password,
                                              'token': token})
        # I didn't manage to use the password with https
        if url.startswith('https'):
            pass_url = url.replace('https','http')
        else:
            pass_url = url
        password_request = compat_urllib_request.Request(pass_url+'/password', data)
        password_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        password_request.add_header('Cookie', 'xsrft=%s' % token)
        self._download_webpage(password_request, video_id,
                               'Verifying the password',
                               'Wrong password')

    def _verify_player_video_password(self, url, video_id):
        password = self._downloader.params.get('videopassword', None)
        if password is None:
            raise ExtractorError('This video is protected by a password, use the --video-password option')
        data = compat_urllib_parse.urlencode({'password': password})
        pass_url = url + '/check-password'
        password_request = compat_urllib_request.Request(pass_url, data)
        password_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        return self._download_json(
            password_request, video_id,
            'Verifying the password',
            'Wrong password')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        url, data = unsmuggle_url(url)
        headers = std_headers
        if data is not None:
            headers = headers.copy()
            headers.update(data)

        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        if mobj.group('pro') or mobj.group('player'):
            url = 'http://player.vimeo.com/video/' + video_id
        else:
            url = 'https://vimeo.com/' + video_id

        # Retrieve video webpage to extract further information
        request = compat_urllib_request.Request(url, None, headers)
        try:
            webpage = self._download_webpage(request, video_id)
        except ExtractorError as ee:
            if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 403:
                errmsg = ee.cause.read()
                if b'Because of its privacy settings, this video cannot be played here' in errmsg:
                    raise ExtractorError(
                        'Cannot download embed-only video without embedding '
                        'URL. Please call youtube-dl with the URL of the page '
                        'that embeds this video.',
                        expected=True)
            raise

        # Now we begin extracting as much information as we can from what we
        # retrieved. First we extract the information common to all extractors,
        # and latter we extract those that are Vimeo specific.
        self.report_extraction(video_id)

        # Extract the config JSON
        try:
            try:
                config_url = self._html_search_regex(
                    r' data-config-url="(.+?)"', webpage, 'config URL')
                config_json = self._download_webpage(config_url, video_id)
                config = json.loads(config_json)
            except RegexNotFoundError:
                # For pro videos or player.vimeo.com urls
                # We try to find out to which variable is assigned the config dic
                m_variable_name = re.search('(\w)\.video\.id', webpage)
                if m_variable_name is not None:
                    config_re = r'%s=({.+?});' % re.escape(m_variable_name.group(1))
                else:
                    config_re = [r' = {config:({.+?}),assets:', r'(?:[abc])=({.+?});']
                config = self._search_regex(config_re, webpage, 'info section',
                    flags=re.DOTALL)
                config = json.loads(config)
        except Exception as e:
            if re.search('The creator of this video has not given you permission to embed it on this domain.', webpage):
                raise ExtractorError('The author has restricted the access to this video, try with the "--referer" option')

            if re.search('<form[^>]+?id="pw_form"', webpage) is not None:
                self._verify_video_password(url, video_id, webpage)
                return self._real_extract(url)
            else:
                raise ExtractorError('Unable to extract info section',
                                     cause=e)
        else:
            if config.get('view') == 4:
                config = self._verify_player_video_password(url, video_id)

        # Extract title
        video_title = config["video"]["title"]

        # Extract uploader and uploader_id
        video_uploader = config["video"]["owner"]["name"]
        video_uploader_id = config["video"]["owner"]["url"].split('/')[-1] if config["video"]["owner"]["url"] else None

        # Extract video thumbnail
        video_thumbnail = config["video"].get("thumbnail")
        if video_thumbnail is None:
            video_thumbs = config["video"].get("thumbs")
            if video_thumbs and isinstance(video_thumbs, dict):
                _, video_thumbnail = sorted((int(width), t_url) for (width, t_url) in video_thumbs.items())[-1]

        # Extract video description
        video_description = None
        try:
            video_description = get_element_by_attribute("itemprop", "description", webpage)
            if video_description: video_description = clean_html(video_description)
        except AssertionError as err:
            # On some pages like (http://player.vimeo.com/video/54469442) the
            # html tags are not closed, python 2.6 cannot handle it
            if err.args[0] == 'we should not get here!':
                pass
            else:
                raise

        # Extract upload date
        video_upload_date = None
        mobj = re.search(r'<meta itemprop="dateCreated" content="(\d{4})-(\d{2})-(\d{2})T', webpage)
        if mobj is not None:
            video_upload_date = mobj.group(1) + mobj.group(2) + mobj.group(3)

        try:
            view_count = int(self._search_regex(r'UserPlays:(\d+)', webpage, 'view count'))
            like_count = int(self._search_regex(r'UserLikes:(\d+)', webpage, 'like count'))
            comment_count = int(self._search_regex(r'UserComments:(\d+)', webpage, 'comment count'))
        except RegexNotFoundError:
            # This info is only available in vimeo.com/{id} urls
            view_count = None
            like_count = None
            comment_count = None

        # Vimeo specific: extract request signature and timestamp
        sig = config['request']['signature']
        timestamp = config['request']['timestamp']

        # Vimeo specific: extract video codec and quality information
        # First consider quality, then codecs, then take everything
        codecs = [('vp6', 'flv'), ('vp8', 'flv'), ('h264', 'mp4')]
        files = {'hd': [], 'sd': [], 'other': []}
        config_files = config["video"].get("files") or config["request"].get("files")
        for codec_name, codec_extension in codecs:
            for quality in config_files.get(codec_name, []):
                format_id = '-'.join((codec_name, quality)).lower()
                key = quality if quality in files else 'other'
                video_url = None
                if isinstance(config_files[codec_name], dict):
                    file_info = config_files[codec_name][quality]
                    video_url = file_info.get('url')
                else:
                    file_info = {}
                if video_url is None:
                    video_url = "http://player.vimeo.com/play_redirect?clip_id=%s&sig=%s&time=%s&quality=%s&codecs=%s&type=moogaloop_local&embed_location=" \
                        %(video_id, sig, timestamp, quality, codec_name.upper())

                files[key].append({
                    'ext': codec_extension,
                    'url': video_url,
                    'format_id': format_id,
                    'width': file_info.get('width'),
                    'height': file_info.get('height'),
                })
        formats = []
        for key in ('other', 'sd', 'hd'):
            formats += files[key]
        if len(formats) == 0:
            raise ExtractorError('No known codec found')

        subtitles = {}
        text_tracks = config['request'].get('text_tracks')
        if text_tracks:
            for tt in text_tracks:
                subtitles[tt['lang']] = 'http://vimeo.com' + tt['url']

        video_subtitles = self.extract_subtitles(video_id, subtitles)
        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, subtitles)
            return

        return {
            'id': video_id,
            'uploader': video_uploader,
            'uploader_id': video_uploader_id,
            'upload_date': video_upload_date,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'description': video_description,
            'formats': formats,
            'webpage_url': url,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'subtitles': video_subtitles,
        }


class VimeoChannelIE(InfoExtractor):
    IE_NAME = 'vimeo:channel'
    _VALID_URL = r'(?:https?://)?vimeo\.com/channels/(?P<id>[^/]+)/?(\?.*)?$'
    _MORE_PAGES_INDICATOR = r'<a.+?rel="next"'
    _TITLE_RE = r'<link rel="alternate"[^>]+?title="(.*?)"'

    def _page_url(self, base_url, pagenum):
        return '%s/videos/page:%d/' % (base_url, pagenum)

    def _extract_list_title(self, webpage):
        return self._html_search_regex(self._TITLE_RE, webpage, 'list title')

    def _extract_videos(self, list_id, base_url):
        video_ids = []
        for pagenum in itertools.count(1):
            webpage = self._download_webpage(
                self._page_url(base_url, pagenum) ,list_id,
                'Downloading page %s' % pagenum)
            video_ids.extend(re.findall(r'id="clip_(\d+?)"', webpage))
            if re.search(self._MORE_PAGES_INDICATOR, webpage, re.DOTALL) is None:
                break

        entries = [self.url_result('http://vimeo.com/%s' % video_id, 'Vimeo')
                   for video_id in video_ids]
        return {'_type': 'playlist',
                'id': list_id,
                'title': self._extract_list_title(webpage),
                'entries': entries,
                }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id =  mobj.group('id')
        return self._extract_videos(channel_id, 'http://vimeo.com/channels/%s' % channel_id)


class VimeoUserIE(VimeoChannelIE):
    IE_NAME = 'vimeo:user'
    _VALID_URL = r'(?:https?://)?vimeo\.com/(?P<name>[^/]+)(?:/videos|[#?]|$)'
    _TITLE_RE = r'<a[^>]+?class="user">([^<>]+?)</a>'

    @classmethod
    def suitable(cls, url):
        if VimeoChannelIE.suitable(url) or VimeoIE.suitable(url) or VimeoAlbumIE.suitable(url) or VimeoGroupsIE.suitable(url):
            return False
        return super(VimeoUserIE, cls).suitable(url)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        return self._extract_videos(name, 'http://vimeo.com/%s' % name)


class VimeoAlbumIE(VimeoChannelIE):
    IE_NAME = 'vimeo:album'
    _VALID_URL = r'(?:https?://)?vimeo\.com/album/(?P<id>\d+)'
    _TITLE_RE = r'<header id="page_header">\n\s*<h1>(.*?)</h1>'

    def _page_url(self, base_url, pagenum):
        return '%s/page:%d/' % (base_url, pagenum)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        album_id = mobj.group('id')
        return self._extract_videos(album_id, 'http://vimeo.com/album/%s' % album_id)


class VimeoGroupsIE(VimeoAlbumIE):
    IE_NAME = 'vimeo:group'
    _VALID_URL = r'(?:https?://)?vimeo\.com/groups/(?P<name>[^/]+)'

    def _extract_list_title(self, webpage):
        return self._og_search_title(webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        return self._extract_videos(name, 'http://vimeo.com/groups/%s' % name)


class VimeoReviewIE(InfoExtractor):
    IE_NAME = 'vimeo:review'
    IE_DESC = 'Review pages on vimeo'
    _VALID_URL = r'(?:https?://)?vimeo\.com/[^/]+/review/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://vimeo.com/user21297594/review/75524534/3c257a1b5d',
        'file': '75524534.mp4',
        'md5': 'c507a72f780cacc12b2248bb4006d253',
        'info_dict': {
            'title': "DICK HARDWICK 'Comedian'",
            'uploader': 'Richard Hardwick',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        player_url = 'https://player.vimeo.com/player/' + video_id
        return self.url_result(player_url, 'Vimeo', video_id)
