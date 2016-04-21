# encoding: utf-8
from __future__ import unicode_literals

import json
import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    InAdvancePagedList,
    int_or_none,
    RegexNotFoundError,
    sanitized_Request,
    smuggle_url,
    std_headers,
    unified_strdate,
    unsmuggle_url,
    urlencode_postdata,
    unescapeHTML,
    parse_filesize,
)


class VimeoBaseInfoExtractor(InfoExtractor):
    _NETRC_MACHINE = 'vimeo'
    _LOGIN_REQUIRED = False
    _LOGIN_URL = 'https://vimeo.com/log_in'

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return
        self.report_login()
        webpage = self._download_webpage(self._LOGIN_URL, None, False)
        token, vuid = self._extract_xsrft_and_vuid(webpage)
        data = urlencode_postdata({
            'action': 'login',
            'email': username,
            'password': password,
            'service': 'vimeo',
            'token': token,
        })
        login_request = sanitized_Request(self._LOGIN_URL, data)
        login_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        login_request.add_header('Referer', self._LOGIN_URL)
        self._set_vimeo_cookie('vuid', vuid)
        self._download_webpage(login_request, None, False, 'Wrong login info')

    def _extract_xsrft_and_vuid(self, webpage):
        xsrft = self._search_regex(
            r'(?:(?P<q1>["\'])xsrft(?P=q1)\s*:|xsrft\s*[=:])\s*(?P<q>["\'])(?P<xsrft>.+?)(?P=q)',
            webpage, 'login token', group='xsrft')
        vuid = self._search_regex(
            r'["\']vuid["\']\s*:\s*(["\'])(?P<vuid>.+?)\1',
            webpage, 'vuid', group='vuid')
        return xsrft, vuid

    def _set_vimeo_cookie(self, name, value):
        self._set_cookie('vimeo.com', name, value)


class VimeoIE(VimeoBaseInfoExtractor):
    """Information extractor for vimeo.com."""

    # _VALID_URL matches Vimeo URLs
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:
                                www|
                                (?P<player>player)
                            )
                            \.
                        )?
                        vimeo(?P<pro>pro)?\.com/
                        (?!channels/[^/?#]+/?(?:$|[?#])|[^/]+/review/|(?:album|ondemand)/)
                        (?:.*?/)?
                        (?:
                            (?:
                                play_redirect_hls|
                                moogaloop\.swf)\?clip_id=
                            )?
                        (?:videos?/)?
                        (?P<id>[0-9]+)
                        (?:/[\da-f]+)?
                        /?(?:[?&].*)?(?:[#].*)?$
                    '''
    IE_NAME = 'vimeo'
    _TESTS = [
        {
            'url': 'http://vimeo.com/56015672#at=0',
            'md5': '8879b6cc097e987f02484baf890129e5',
            'info_dict': {
                'id': '56015672',
                'ext': 'mp4',
                'title': "youtube-dl test video - \u2605 \" ' \u5e78 / \\ \u00e4 \u21ad \U0001d550",
                'description': 'md5:2d3305bad981a06ff79f027f19865021',
                'upload_date': '20121220',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/user7108434',
                'uploader_id': 'user7108434',
                'uploader': 'Filippo Valsorda',
                'duration': 10,
            },
        },
        {
            'url': 'http://vimeopro.com/openstreetmapus/state-of-the-map-us-2013/video/68093876',
            'md5': '3b5ca6aa22b60dfeeadf50b72e44ed82',
            'note': 'Vimeo Pro video (#1197)',
            'info_dict': {
                'id': '68093876',
                'ext': 'mp4',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/openstreetmapus',
                'uploader_id': 'openstreetmapus',
                'uploader': 'OpenStreetMap US',
                'title': 'Andy Allan - Putting the Carto into OpenStreetMap Cartography',
                'description': 'md5:fd69a7b8d8c34a4e1d2ec2e4afd6ec30',
                'duration': 1595,
            },
        },
        {
            'url': 'http://player.vimeo.com/video/54469442',
            'md5': '619b811a4417aa4abe78dc653becf511',
            'note': 'Videos that embed the url in the player page',
            'info_dict': {
                'id': '54469442',
                'ext': 'mp4',
                'title': 'Kathy Sierra: Building the minimum Badass User, Business of Software 2012',
                'uploader': 'The BLN & Business of Software',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/theblnbusinessofsoftware',
                'uploader_id': 'theblnbusinessofsoftware',
                'duration': 3610,
                'description': None,
            },
        },
        {
            'url': 'http://vimeo.com/68375962',
            'md5': 'aaf896bdb7ddd6476df50007a0ac0ae7',
            'note': 'Video protected with password',
            'info_dict': {
                'id': '68375962',
                'ext': 'mp4',
                'title': 'youtube-dl password protected test video',
                'upload_date': '20130614',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/user18948128',
                'uploader_id': 'user18948128',
                'uploader': 'Jaime Marquínez Ferrándiz',
                'duration': 10,
                'description': 'This is "youtube-dl password protected test video" by Jaime Marquínez Ferrándiz on Vimeo, the home for high quality videos and the people\u2026',
            },
            'params': {
                'videopassword': 'youtube-dl',
            },
        },
        {
            'url': 'http://vimeo.com/channels/keypeele/75629013',
            'md5': '2f86a05afe9d7abc0b9126d229bbe15d',
            'note': 'Video is freely available via original URL '
                    'and protected with password when accessed via http://vimeo.com/75629013',
            'info_dict': {
                'id': '75629013',
                'ext': 'mp4',
                'title': 'Key & Peele: Terrorist Interrogation',
                'description': 'md5:8678b246399b070816b12313e8b4eb5c',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/atencio',
                'uploader_id': 'atencio',
                'uploader': 'Peter Atencio',
                'upload_date': '20130927',
                'duration': 187,
            },
        },
        {
            'url': 'http://vimeo.com/76979871',
            'note': 'Video with subtitles',
            'info_dict': {
                'id': '76979871',
                'ext': 'mp4',
                'title': 'The New Vimeo Player (You Know, For Videos)',
                'description': 'md5:2ec900bf97c3f389378a96aee11260ea',
                'upload_date': '20131015',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/staff',
                'uploader_id': 'staff',
                'uploader': 'Vimeo Staff',
                'duration': 62,
            }
        },
        {
            # from https://www.ouya.tv/game/Pier-Solar-and-the-Great-Architects/
            'url': 'https://player.vimeo.com/video/98044508',
            'note': 'The js code contains assignments to the same variable as the config',
            'info_dict': {
                'id': '98044508',
                'ext': 'mp4',
                'title': 'Pier Solar OUYA Official Trailer',
                'uploader': 'Tulio Gonçalves',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/user28849593',
                'uploader_id': 'user28849593',
            },
        },
        {
            # contains original format
            'url': 'https://vimeo.com/33951933',
            'md5': '53c688fa95a55bf4b7293d37a89c5c53',
            'info_dict': {
                'id': '33951933',
                'ext': 'mp4',
                'title': 'FOX CLASSICS - Forever Classic ID - A Full Minute',
                'uploader': 'The DMCI',
                'uploader_url': 're:https?://(?:www\.)?vimeo\.com/dmci',
                'uploader_id': 'dmci',
                'upload_date': '20111220',
                'description': 'md5:ae23671e82d05415868f7ad1aec21147',
            },
        },
        {
            'url': 'https://vimeo.com/109815029',
            'note': 'Video not completely processed, "failed" seed status',
            'only_matching': True,
        },
        {
            'url': 'https://vimeo.com/groups/travelhd/videos/22439234',
            'only_matching': True,
        },
        {
            # source file returns 403: Forbidden
            'url': 'https://vimeo.com/7809605',
            'only_matching': True,
        },
        {
            'url': 'https://vimeo.com/160743502/abd0e13fb4',
            'only_matching': True,
        }
    ]

    @staticmethod
    def _extract_vimeo_url(url, webpage):
        # Look for embedded (iframe) Vimeo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//player\.vimeo\.com/video/.+?)\1', webpage)
        if mobj:
            player_url = unescapeHTML(mobj.group('url'))
            surl = smuggle_url(player_url, {'http_headers': {'Referer': url}})
            return surl
        # Look for embedded (swf embed) Vimeo player
        mobj = re.search(
            r'<embed[^>]+?src="((?:https?:)?//(?:www\.)?vimeo\.com/moogaloop\.swf.+?)"', webpage)
        if mobj:
            return mobj.group(1)

    def _verify_video_password(self, url, video_id, webpage):
        password = self._downloader.params.get('videopassword')
        if password is None:
            raise ExtractorError('This video is protected by a password, use the --video-password option', expected=True)
        token, vuid = self._extract_xsrft_and_vuid(webpage)
        data = urlencode_postdata({
            'password': password,
            'token': token,
        })
        if url.startswith('http://'):
            # vimeo only supports https now, but the user can give an http url
            url = url.replace('http://', 'https://')
        password_request = sanitized_Request(url + '/password', data)
        password_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        password_request.add_header('Referer', url)
        self._set_vimeo_cookie('vuid', vuid)
        return self._download_webpage(
            password_request, video_id,
            'Verifying the password', 'Wrong password')

    def _verify_player_video_password(self, url, video_id):
        password = self._downloader.params.get('videopassword')
        if password is None:
            raise ExtractorError('This video is protected by a password, use the --video-password option')
        data = urlencode_postdata({'password': password})
        pass_url = url + '/check-password'
        password_request = sanitized_Request(pass_url, data)
        password_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        password_request.add_header('Referer', url)
        return self._download_json(
            password_request, video_id,
            'Verifying the password', 'Wrong password')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        headers = std_headers.copy()
        if 'http_headers' in data:
            headers.update(data['http_headers'])
        if 'Referer' not in headers:
            headers['Referer'] = url

        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        orig_url = url
        if mobj.group('pro') or mobj.group('player'):
            url = 'https://player.vimeo.com/video/' + video_id
        else:
            url = 'https://vimeo.com/' + video_id

        # Retrieve video webpage to extract further information
        request = sanitized_Request(url, headers=headers)
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

        vimeo_config = self._search_regex(
            r'vimeo\.config\s*=\s*(?:({.+?})|_extend\([^,]+,\s+({.+?})\));', webpage,
            'vimeo config', default=None)
        if vimeo_config:
            seed_status = self._parse_json(vimeo_config, video_id).get('seed_status', {})
            if seed_status.get('state') == 'failed':
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, seed_status['title']),
                    expected=True)

        # Extract the config JSON
        try:
            try:
                config_url = self._html_search_regex(
                    r' data-config-url="(.+?)"', webpage,
                    'config URL', default=None)
                if not config_url:
                    # Sometimes new react-based page is served instead of old one that require
                    # different config URL extraction approach (see
                    # https://github.com/rg3/youtube-dl/pull/7209)
                    vimeo_clip_page_config = self._search_regex(
                        r'vimeo\.clip_page_config\s*=\s*({.+?});', webpage,
                        'vimeo clip page config')
                    config_url = self._parse_json(
                        vimeo_clip_page_config, video_id)['player']['config_url']
                config_json = self._download_webpage(config_url, video_id)
                config = json.loads(config_json)
            except RegexNotFoundError:
                # For pro videos or player.vimeo.com urls
                # We try to find out to which variable is assigned the config dic
                m_variable_name = re.search('(\w)\.video\.id', webpage)
                if m_variable_name is not None:
                    config_re = r'%s=({[^}].+?});' % re.escape(m_variable_name.group(1))
                else:
                    config_re = [r' = {config:({.+?}),assets:', r'(?:[abc])=({.+?});']
                config = self._search_regex(config_re, webpage, 'info section',
                                            flags=re.DOTALL)
                config = json.loads(config)
        except Exception as e:
            if re.search('The creator of this video has not given you permission to embed it on this domain.', webpage):
                raise ExtractorError('The author has restricted the access to this video, try with the "--referer" option')

            if re.search(r'<form[^>]+?id="pw_form"', webpage) is not None:
                if '_video_password_verified' in data:
                    raise ExtractorError('video password verification failed!')
                self._verify_video_password(url, video_id, webpage)
                return self._real_extract(
                    smuggle_url(url, {'_video_password_verified': 'verified'}))
            else:
                raise ExtractorError('Unable to extract info section',
                                     cause=e)
        else:
            if config.get('view') == 4:
                config = self._verify_player_video_password(url, video_id)

        if '>You rented this title.<' in webpage:
            feature_id = config.get('video', {}).get('vod', {}).get('feature_id')
            if feature_id and not data.get('force_feature_id', False):
                return self.url_result(smuggle_url(
                    'https://player.vimeo.com/player/%s' % feature_id,
                    {'force_feature_id': True}), 'Vimeo')

        # Extract title
        video_title = config['video']['title']

        # Extract uploader, uploader_url and uploader_id
        video_uploader = config['video'].get('owner', {}).get('name')
        video_uploader_url = config['video'].get('owner', {}).get('url')
        video_uploader_id = video_uploader_url.split('/')[-1] if video_uploader_url else None

        # Extract video thumbnail
        video_thumbnail = config['video'].get('thumbnail')
        if video_thumbnail is None:
            video_thumbs = config['video'].get('thumbs')
            if video_thumbs and isinstance(video_thumbs, dict):
                _, video_thumbnail = sorted((int(width if width.isdigit() else 0), t_url) for (width, t_url) in video_thumbs.items())[-1]

        # Extract video description

        video_description = self._html_search_regex(
            r'(?s)<div\s+class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            webpage, 'description', default=None)
        if not video_description:
            video_description = self._html_search_meta(
                'description', webpage, default=None)
        if not video_description and mobj.group('pro'):
            orig_webpage = self._download_webpage(
                orig_url, video_id,
                note='Downloading webpage for description',
                fatal=False)
            if orig_webpage:
                video_description = self._html_search_meta(
                    'description', orig_webpage, default=None)
        if not video_description and not mobj.group('player'):
            self._downloader.report_warning('Cannot find video description')

        # Extract video duration
        video_duration = int_or_none(config['video'].get('duration'))

        # Extract upload date
        video_upload_date = None
        mobj = re.search(r'<time[^>]+datetime="([^"]+)"', webpage)
        if mobj is not None:
            video_upload_date = unified_strdate(mobj.group(1))

        try:
            view_count = int(self._search_regex(r'UserPlays:(\d+)', webpage, 'view count'))
            like_count = int(self._search_regex(r'UserLikes:(\d+)', webpage, 'like count'))
            comment_count = int(self._search_regex(r'UserComments:(\d+)', webpage, 'comment count'))
        except RegexNotFoundError:
            # This info is only available in vimeo.com/{id} urls
            view_count = None
            like_count = None
            comment_count = None

        formats = []
        download_request = sanitized_Request('https://vimeo.com/%s?action=load_download_config' % video_id, headers={
            'X-Requested-With': 'XMLHttpRequest'})
        download_data = self._download_json(download_request, video_id, fatal=False)
        if download_data:
            source_file = download_data.get('source_file')
            if isinstance(source_file, dict):
                download_url = source_file.get('download_url')
                if download_url and not source_file.get('is_cold') and not source_file.get('is_defrosting'):
                    source_name = source_file.get('public_name', 'Original')
                    if self._is_valid_url(download_url, video_id, '%s video' % source_name):
                        ext = source_file.get('extension', determine_ext(download_url)).lower()
                        formats.append({
                            'url': download_url,
                            'ext': ext,
                            'width': int_or_none(source_file.get('width')),
                            'height': int_or_none(source_file.get('height')),
                            'filesize': parse_filesize(source_file.get('size')),
                            'format_id': source_name,
                            'preference': 1,
                        })
        config_files = config['video'].get('files') or config['request'].get('files', {})
        for f in config_files.get('progressive', []):
            video_url = f.get('url')
            if not video_url:
                continue
            formats.append({
                'url': video_url,
                'format_id': 'http-%s' % f.get('quality'),
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'fps': int_or_none(f.get('fps')),
                'tbr': int_or_none(f.get('bitrate')),
            })
        m3u8_url = config_files.get('hls', {}).get('url')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
        # Bitrates are completely broken. Single m3u8 may contain entries in kbps and bps
        # at the same time without actual units specified. This lead to wrong sorting.
        self._sort_formats(formats, field_preference=('preference', 'height', 'width', 'fps', 'format_id'))

        subtitles = {}
        text_tracks = config['request'].get('text_tracks')
        if text_tracks:
            for tt in text_tracks:
                subtitles[tt['lang']] = [{
                    'ext': 'vtt',
                    'url': 'https://vimeo.com' + tt['url'],
                }]

        return {
            'id': video_id,
            'uploader': video_uploader,
            'uploader_url': video_uploader_url,
            'uploader_id': video_uploader_id,
            'upload_date': video_upload_date,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'description': video_description,
            'duration': video_duration,
            'formats': formats,
            'webpage_url': url,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'subtitles': subtitles,
        }


class VimeoOndemandIE(VimeoBaseInfoExtractor):
    IE_NAME = 'vimeo:ondemand'
    _VALID_URL = r'https?://(?:www\.)?vimeo\.com/ondemand/(?P<id>[^/?#&]+)'
    _TESTS = [{
        # ondemand video not available via https://vimeo.com/id
        'url': 'https://vimeo.com/ondemand/20704',
        'md5': 'c424deda8c7f73c1dfb3edd7630e2f35',
        'info_dict': {
            'id': '105442900',
            'ext': 'mp4',
            'title': 'המעבדה - במאי יותם פלדמן',
            'uploader': 'גם סרטים',
            'uploader_url': 're:https?://(?:www\.)?vimeo\.com/gumfilms',
            'uploader_id': 'gumfilms',
        },
    }, {
        'url': 'https://vimeo.com/ondemand/nazmaalik',
        'only_matching': True,
    }, {
        'url': 'https://vimeo.com/ondemand/141692381',
        'only_matching': True,
    }, {
        'url': 'https://vimeo.com/ondemand/thelastcolony/150274832',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        return self.url_result(self._og_search_video_url(webpage), VimeoIE.ie_key())


class VimeoChannelIE(VimeoBaseInfoExtractor):
    IE_NAME = 'vimeo:channel'
    _VALID_URL = r'https://vimeo\.com/channels/(?P<id>[^/?#]+)/?(?:$|[?#])'
    _MORE_PAGES_INDICATOR = r'<a.+?rel="next"'
    _TITLE = None
    _TITLE_RE = r'<link rel="alternate"[^>]+?title="(.*?)"'
    _TESTS = [{
        'url': 'https://vimeo.com/channels/tributes',
        'info_dict': {
            'id': 'tributes',
            'title': 'Vimeo Tributes',
        },
        'playlist_mincount': 25,
    }]

    def _page_url(self, base_url, pagenum):
        return '%s/videos/page:%d/' % (base_url, pagenum)

    def _extract_list_title(self, webpage):
        return self._TITLE or self._html_search_regex(self._TITLE_RE, webpage, 'list title')

    def _login_list_password(self, page_url, list_id, webpage):
        login_form = self._search_regex(
            r'(?s)<form[^>]+?id="pw_form"(.*?)</form>',
            webpage, 'login form', default=None)
        if not login_form:
            return webpage

        password = self._downloader.params.get('videopassword')
        if password is None:
            raise ExtractorError('This album is protected by a password, use the --video-password option', expected=True)
        fields = self._hidden_inputs(login_form)
        token, vuid = self._extract_xsrft_and_vuid(webpage)
        fields['token'] = token
        fields['password'] = password
        post = urlencode_postdata(fields)
        password_path = self._search_regex(
            r'action="([^"]+)"', login_form, 'password URL')
        password_url = compat_urlparse.urljoin(page_url, password_path)
        password_request = sanitized_Request(password_url, post)
        password_request.add_header('Content-type', 'application/x-www-form-urlencoded')
        self._set_vimeo_cookie('vuid', vuid)
        self._set_vimeo_cookie('xsrft', token)

        return self._download_webpage(
            password_request, list_id,
            'Verifying the password', 'Wrong password')

    def _title_and_entries(self, list_id, base_url):
        for pagenum in itertools.count(1):
            page_url = self._page_url(base_url, pagenum)
            webpage = self._download_webpage(
                page_url, list_id,
                'Downloading page %s' % pagenum)

            if pagenum == 1:
                webpage = self._login_list_password(page_url, list_id, webpage)
                yield self._extract_list_title(webpage)

            for video_id in re.findall(r'id="clip_(\d+?)"', webpage):
                yield self.url_result('https://vimeo.com/%s' % video_id, 'Vimeo')

            if re.search(self._MORE_PAGES_INDICATOR, webpage, re.DOTALL) is None:
                break

    def _extract_videos(self, list_id, base_url):
        title_and_entries = self._title_and_entries(list_id, base_url)
        list_title = next(title_and_entries)
        return self.playlist_result(title_and_entries, list_id, list_title)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        return self._extract_videos(channel_id, 'https://vimeo.com/channels/%s' % channel_id)


class VimeoUserIE(VimeoChannelIE):
    IE_NAME = 'vimeo:user'
    _VALID_URL = r'https://vimeo\.com/(?!(?:[0-9]+|watchlater)(?:$|[?#/]))(?P<name>[^/]+)(?:/videos|[#?]|$)'
    _TITLE_RE = r'<a[^>]+?class="user">([^<>]+?)</a>'
    _TESTS = [{
        'url': 'https://vimeo.com/nkistudio/videos',
        'info_dict': {
            'title': 'Nki',
            'id': 'nkistudio',
        },
        'playlist_mincount': 66,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        return self._extract_videos(name, 'https://vimeo.com/%s' % name)


class VimeoAlbumIE(VimeoChannelIE):
    IE_NAME = 'vimeo:album'
    _VALID_URL = r'https://vimeo\.com/album/(?P<id>\d+)'
    _TITLE_RE = r'<header id="page_header">\n\s*<h1>(.*?)</h1>'
    _TESTS = [{
        'url': 'https://vimeo.com/album/2632481',
        'info_dict': {
            'id': '2632481',
            'title': 'Staff Favorites: November 2013',
        },
        'playlist_mincount': 13,
    }, {
        'note': 'Password-protected album',
        'url': 'https://vimeo.com/album/3253534',
        'info_dict': {
            'title': 'test',
            'id': '3253534',
        },
        'playlist_count': 1,
        'params': {
            'videopassword': 'youtube-dl',
        }
    }]

    def _page_url(self, base_url, pagenum):
        return '%s/page:%d/' % (base_url, pagenum)

    def _real_extract(self, url):
        album_id = self._match_id(url)
        return self._extract_videos(album_id, 'https://vimeo.com/album/%s' % album_id)


class VimeoGroupsIE(VimeoAlbumIE):
    IE_NAME = 'vimeo:group'
    _VALID_URL = r'https://vimeo\.com/groups/(?P<name>[^/]+)(?:/(?!videos?/\d+)|$)'
    _TESTS = [{
        'url': 'https://vimeo.com/groups/rolexawards',
        'info_dict': {
            'id': 'rolexawards',
            'title': 'Rolex Awards for Enterprise',
        },
        'playlist_mincount': 73,
    }]

    def _extract_list_title(self, webpage):
        return self._og_search_title(webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        return self._extract_videos(name, 'https://vimeo.com/groups/%s' % name)


class VimeoReviewIE(InfoExtractor):
    IE_NAME = 'vimeo:review'
    IE_DESC = 'Review pages on vimeo'
    _VALID_URL = r'https://vimeo\.com/[^/]+/review/(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'https://vimeo.com/user21297594/review/75524534/3c257a1b5d',
        'md5': 'c507a72f780cacc12b2248bb4006d253',
        'info_dict': {
            'id': '75524534',
            'ext': 'mp4',
            'title': "DICK HARDWICK 'Comedian'",
            'uploader': 'Richard Hardwick',
        }
    }, {
        'note': 'video player needs Referer',
        'url': 'https://vimeo.com/user22258446/review/91613211/13f927e053',
        'md5': '6295fdab8f4bf6a002d058b2c6dce276',
        'info_dict': {
            'id': '91613211',
            'ext': 'mp4',
            'title': 're:(?i)^Death by dogma versus assembling agile . Sander Hoogendoorn',
            'uploader': 'DevWeek Events',
            'duration': 2773,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        player_url = 'https://player.vimeo.com/player/' + video_id
        return self.url_result(player_url, 'Vimeo', video_id)


class VimeoWatchLaterIE(VimeoChannelIE):
    IE_NAME = 'vimeo:watchlater'
    IE_DESC = 'Vimeo watch later list, "vimeowatchlater" keyword (requires authentication)'
    _VALID_URL = r'https://vimeo\.com/(?:home/)?watchlater|:vimeowatchlater'
    _TITLE = 'Watch Later'
    _LOGIN_REQUIRED = True
    _TESTS = [{
        'url': 'https://vimeo.com/watchlater',
        'only_matching': True,
    }]

    def _real_initialize(self):
        self._login()

    def _page_url(self, base_url, pagenum):
        url = '%s/page:%d/' % (base_url, pagenum)
        request = sanitized_Request(url)
        # Set the header to get a partial html page with the ids,
        # the normal page doesn't contain them.
        request.add_header('X-Requested-With', 'XMLHttpRequest')
        return request

    def _real_extract(self, url):
        return self._extract_videos('watchlater', 'https://vimeo.com/watchlater')


class VimeoLikesIE(InfoExtractor):
    _VALID_URL = r'https://(?:www\.)?vimeo\.com/user(?P<id>[0-9]+)/likes/?(?:$|[?#]|sort:)'
    IE_NAME = 'vimeo:likes'
    IE_DESC = 'Vimeo user likes'
    _TEST = {
        'url': 'https://vimeo.com/user755559/likes/',
        'playlist_mincount': 293,
        'info_dict': {
            'id': 'user755559_likes',
            'description': 'See all the videos urza likes',
            'title': 'Videos urza likes',
        },
    }

    def _real_extract(self, url):
        user_id = self._match_id(url)
        webpage = self._download_webpage(url, user_id)
        page_count = self._int(
            self._search_regex(
                r'''(?x)<li><a\s+href="[^"]+"\s+data-page="([0-9]+)">
                    .*?</a></li>\s*<li\s+class="pagination_next">
                ''', webpage, 'page count'),
            'page count', fatal=True)
        PAGE_SIZE = 12
        title = self._html_search_regex(
            r'(?s)<h1>(.+?)</h1>', webpage, 'title', fatal=False)
        description = self._html_search_meta('description', webpage)

        def _get_page(idx):
            page_url = 'https://vimeo.com/user%s/likes/page:%d/sort:date' % (
                user_id, idx + 1)
            webpage = self._download_webpage(
                page_url, user_id,
                note='Downloading page %d/%d' % (idx + 1, page_count))
            video_list = self._search_regex(
                r'(?s)<ol class="js-browse_list[^"]+"[^>]*>(.*?)</ol>',
                webpage, 'video content')
            paths = re.findall(
                r'<li[^>]*>\s*<a\s+href="([^"]+)"', video_list)
            for path in paths:
                yield {
                    '_type': 'url',
                    'url': compat_urlparse.urljoin(page_url, path),
                }

        pl = InAdvancePagedList(_get_page, page_count, PAGE_SIZE)

        return {
            '_type': 'playlist',
            'id': 'user%s_likes' % user_id,
            'title': title,
            'description': description,
            'entries': pl,
        }
