# coding: utf-8
from __future__ import unicode_literals

import base64
import json
import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    js_to_json,
    InAdvancePagedList,
    int_or_none,
    merge_dicts,
    NO_DEFAULT,
    parse_filesize,
    qualities,
    RegexNotFoundError,
    sanitized_Request,
    smuggle_url,
    std_headers,
    try_get,
    unified_timestamp,
    unsmuggle_url,
    urlencode_postdata,
    unescapeHTML,
)


class VimeoBaseInfoExtractor(InfoExtractor):
    _NETRC_MACHINE = 'vimeo'
    _LOGIN_REQUIRED = False
    _LOGIN_URL = 'https://vimeo.com/log_in'

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return
        webpage = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')
        token, vuid = self._extract_xsrft_and_vuid(webpage)
        data = {
            'action': 'login',
            'email': username,
            'password': password,
            'service': 'vimeo',
            'token': token,
        }
        self._set_vimeo_cookie('vuid', vuid)
        try:
            self._download_webpage(
                self._LOGIN_URL, None, 'Logging in',
                data=urlencode_postdata(data), headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': self._LOGIN_URL,
                })
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 418:
                raise ExtractorError(
                    'Unable to log in: bad username or password',
                    expected=True)
            raise ExtractorError('Unable to log in')

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

    def _vimeo_sort_formats(self, formats):
        # Bitrates are completely broken. Single m3u8 may contain entries in kbps and bps
        # at the same time without actual units specified. This lead to wrong sorting.
        self._sort_formats(formats, field_preference=('preference', 'height', 'width', 'fps', 'tbr', 'format_id'))

    def _parse_config(self, config, video_id):
        video_data = config['video']
        video_title = video_data['title']
        live_event = video_data.get('live_event') or {}
        is_live = live_event.get('status') == 'started'

        formats = []
        config_files = video_data.get('files') or config['request'].get('files', {})
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

        # TODO: fix handling of 308 status code returned for live archive manifest requests
        for files_type in ('hls', 'dash'):
            for cdn_name, cdn_data in config_files.get(files_type, {}).get('cdns', {}).items():
                manifest_url = cdn_data.get('url')
                if not manifest_url:
                    continue
                format_id = '%s-%s' % (files_type, cdn_name)
                if files_type == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        manifest_url, video_id, 'mp4',
                        'm3u8' if is_live else 'm3u8_native', m3u8_id=format_id,
                        note='Downloading %s m3u8 information' % cdn_name,
                        fatal=False))
                elif files_type == 'dash':
                    mpd_pattern = r'/%s/(?:sep/)?video/' % video_id
                    mpd_manifest_urls = []
                    if re.search(mpd_pattern, manifest_url):
                        for suffix, repl in (('', 'video'), ('_sep', 'sep/video')):
                            mpd_manifest_urls.append((format_id + suffix, re.sub(
                                mpd_pattern, '/%s/%s/' % (video_id, repl), manifest_url)))
                    else:
                        mpd_manifest_urls = [(format_id, manifest_url)]
                    for f_id, m_url in mpd_manifest_urls:
                        if 'json=1' in m_url:
                            real_m_url = (self._download_json(m_url, video_id, fatal=False) or {}).get('url')
                            if real_m_url:
                                m_url = real_m_url
                        mpd_formats = self._extract_mpd_formats(
                            m_url.replace('/master.json', '/master.mpd'), video_id, f_id,
                            'Downloading %s MPD information' % cdn_name,
                            fatal=False)
                        for f in mpd_formats:
                            if f.get('vcodec') == 'none':
                                f['preference'] = -50
                            elif f.get('acodec') == 'none':
                                f['preference'] = -40
                        formats.extend(mpd_formats)

        live_archive = live_event.get('archive') or {}
        live_archive_source_url = live_archive.get('source_url')
        if live_archive_source_url and live_archive.get('status') == 'done':
            formats.append({
                'format_id': 'live-archive-source',
                'url': live_archive_source_url,
                'preference': 1,
            })

        subtitles = {}
        text_tracks = config['request'].get('text_tracks')
        if text_tracks:
            for tt in text_tracks:
                subtitles[tt['lang']] = [{
                    'ext': 'vtt',
                    'url': 'https://vimeo.com' + tt['url'],
                }]

        thumbnails = []
        if not is_live:
            for key, thumb in video_data.get('thumbs', {}).items():
                thumbnails.append({
                    'id': key,
                    'width': int_or_none(key),
                    'url': thumb,
                })
            thumbnail = video_data.get('thumbnail')
            if thumbnail:
                thumbnails.append({
                    'url': thumbnail,
                })

        owner = video_data.get('owner') or {}
        video_uploader_url = owner.get('url')

        return {
            'title': self._live_title(video_title) if is_live else video_title,
            'uploader': owner.get('name'),
            'uploader_id': video_uploader_url.split('/')[-1] if video_uploader_url else None,
            'uploader_url': video_uploader_url,
            'thumbnails': thumbnails,
            'duration': int_or_none(video_data.get('duration')),
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
        }

    def _extract_original_format(self, url, video_id):
        download_data = self._download_json(
            url, video_id, fatal=False,
            query={'action': 'load_download_config'},
            headers={'X-Requested-With': 'XMLHttpRequest'})
        if download_data:
            source_file = download_data.get('source_file')
            if isinstance(source_file, dict):
                download_url = source_file.get('download_url')
                if download_url and not source_file.get('is_cold') and not source_file.get('is_defrosting'):
                    source_name = source_file.get('public_name', 'Original')
                    if self._is_valid_url(download_url, video_id, '%s video' % source_name):
                        ext = (try_get(
                            source_file, lambda x: x['extension'],
                            compat_str) or determine_ext(
                            download_url, None) or 'mp4').lower()
                        return {
                            'url': download_url,
                            'ext': ext,
                            'width': int_or_none(source_file.get('width')),
                            'height': int_or_none(source_file.get('height')),
                            'filesize': parse_filesize(source_file.get('size')),
                            'format_id': source_name,
                            'preference': 1,
                        }


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
                        (?!(?:channels|album)/[^/?#]+/?(?:$|[?#])|[^/]+/review/|ondemand/)
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
                'description': 'md5:509a9ad5c9bf97c60faee9203aca4479',
                'timestamp': 1355990239,
                'upload_date': '20121220',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/user7108434',
                'uploader_id': 'user7108434',
                'uploader': 'Filippo Valsorda',
                'duration': 10,
                'license': 'by-sa',
            },
        },
        {
            'url': 'http://vimeopro.com/openstreetmapus/state-of-the-map-us-2013/video/68093876',
            'md5': '3b5ca6aa22b60dfeeadf50b72e44ed82',
            'note': 'Vimeo Pro video (#1197)',
            'info_dict': {
                'id': '68093876',
                'ext': 'mp4',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/openstreetmapus',
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
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/theblnbusinessofsoftware',
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
                'timestamp': 1371200155,
                'upload_date': '20130614',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/user18948128',
                'uploader_id': 'user18948128',
                'uploader': 'Jaime Marquínez Ferrándiz',
                'duration': 10,
                'description': 'md5:dca3ea23adb29ee387127bc4ddfce63f',
            },
            'params': {
                'videopassword': 'youtube-dl',
            },
        },
        {
            'url': 'http://vimeo.com/channels/keypeele/75629013',
            'md5': '2f86a05afe9d7abc0b9126d229bbe15d',
            'info_dict': {
                'id': '75629013',
                'ext': 'mp4',
                'title': 'Key & Peele: Terrorist Interrogation',
                'description': 'md5:8678b246399b070816b12313e8b4eb5c',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/atencio',
                'uploader_id': 'atencio',
                'uploader': 'Peter Atencio',
                'channel_id': 'keypeele',
                'channel_url': r're:https?://(?:www\.)?vimeo\.com/channels/keypeele',
                'timestamp': 1380339469,
                'upload_date': '20130928',
                'duration': 187,
            },
            'expected_warnings': ['Unable to download JSON metadata'],
        },
        {
            'url': 'http://vimeo.com/76979871',
            'note': 'Video with subtitles',
            'info_dict': {
                'id': '76979871',
                'ext': 'mp4',
                'title': 'The New Vimeo Player (You Know, For Videos)',
                'description': 'md5:2ec900bf97c3f389378a96aee11260ea',
                'timestamp': 1381846109,
                'upload_date': '20131015',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/staff',
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
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/user28849593',
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
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/dmci',
                'uploader_id': 'dmci',
                'timestamp': 1324343742,
                'upload_date': '20111220',
                'description': 'md5:ae23671e82d05415868f7ad1aec21147',
            },
        },
        {
            # only available via https://vimeo.com/channels/tributes/6213729 and
            # not via https://vimeo.com/6213729
            'url': 'https://vimeo.com/channels/tributes/6213729',
            'info_dict': {
                'id': '6213729',
                'ext': 'mp4',
                'title': 'Vimeo Tribute: The Shining',
                'uploader': 'Casey Donahue',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/caseydonahue',
                'uploader_id': 'caseydonahue',
                'channel_url': r're:https?://(?:www\.)?vimeo\.com/channels/tributes',
                'channel_id': 'tributes',
                'timestamp': 1250886430,
                'upload_date': '20090821',
                'description': 'md5:bdbf314014e58713e6e5b66eb252f4a6',
            },
            'params': {
                'skip_download': True,
            },
            'expected_warnings': ['Unable to download JSON metadata'],
        },
        {
            # redirects to ondemand extractor and should be passed through it
            # for successful extraction
            'url': 'https://vimeo.com/73445910',
            'info_dict': {
                'id': '73445910',
                'ext': 'mp4',
                'title': 'The Reluctant Revolutionary',
                'uploader': '10Ft Films',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/tenfootfilms',
                'uploader_id': 'tenfootfilms',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://player.vimeo.com/video/68375962',
            'md5': 'aaf896bdb7ddd6476df50007a0ac0ae7',
            'info_dict': {
                'id': '68375962',
                'ext': 'mp4',
                'title': 'youtube-dl password protected test video',
                'uploader_url': r're:https?://(?:www\.)?vimeo\.com/user18948128',
                'uploader_id': 'user18948128',
                'uploader': 'Jaime Marquínez Ferrándiz',
                'duration': 10,
            },
            'params': {
                'videopassword': 'youtube-dl',
            },
        },
        {
            'url': 'http://vimeo.com/moogaloop.swf?clip_id=2539741',
            'only_matching': True,
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
            'url': 'https://vimeo.com/album/2632481/video/79010983',
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
        # https://gettingthingsdone.com/workflowmap/
        # vimeo embed with check-password page protected by Referer header
    ]

    @staticmethod
    def _smuggle_referrer(url, referrer_url):
        return smuggle_url(url, {'http_headers': {'Referer': referrer_url}})

    @staticmethod
    def _extract_urls(url, webpage):
        urls = []
        # Look for embedded (iframe) Vimeo player
        for mobj in re.finditer(
                r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//player\.vimeo\.com/video/\d+.*?)\1',
                webpage):
            urls.append(VimeoIE._smuggle_referrer(unescapeHTML(mobj.group('url')), url))
        PLAIN_EMBED_RE = (
            # Look for embedded (swf embed) Vimeo player
            r'<embed[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?vimeo\.com/moogaloop\.swf.+?)\1',
            # Look more for non-standard embedded Vimeo player
            r'<video[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?vimeo\.com/[0-9]+)\1',
        )
        for embed_re in PLAIN_EMBED_RE:
            for mobj in re.finditer(embed_re, webpage):
                urls.append(mobj.group('url'))
        return urls

    @staticmethod
    def _extract_url(url, webpage):
        urls = VimeoIE._extract_urls(url, webpage)
        return urls[0] if urls else None

    def _verify_player_video_password(self, url, video_id, headers):
        password = self._downloader.params.get('videopassword')
        if password is None:
            raise ExtractorError('This video is protected by a password, use the --video-password option')
        data = urlencode_postdata({
            'password': base64.b64encode(password.encode()),
        })
        headers = merge_dicts(headers, {
            'Content-Type': 'application/x-www-form-urlencoded',
        })
        checked = self._download_json(
            url + '/check-password', video_id,
            'Verifying the password', data=data, headers=headers)
        if checked is False:
            raise ExtractorError('Wrong video password', expected=True)
        return checked

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        url, data = unsmuggle_url(url, {})
        headers = std_headers.copy()
        if 'http_headers' in data:
            headers.update(data['http_headers'])
        if 'Referer' not in headers:
            headers['Referer'] = url

        channel_id = self._search_regex(
            r'vimeo\.com/channels/([^/]+)', url, 'channel id', default=None)

        # Extract ID from URL
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        orig_url = url
        if mobj.group('pro'):
            # some videos require portfolio_id to be present in player url
            # https://github.com/ytdl-org/youtube-dl/issues/20070
            url = self._extract_url(url, self._download_webpage(url, video_id))
        elif mobj.group('player'):
            url = 'https://player.vimeo.com/video/' + video_id
        elif any(p in url for p in ('play_redirect_hls', 'moogaloop.swf')):
            url = 'https://vimeo.com/' + video_id

        # Retrieve video webpage to extract further information
        request = sanitized_Request(url, headers=headers)
        try:
            webpage, urlh = self._download_webpage_handle(request, video_id)
            redirect_url = compat_str(urlh.geturl())
            # Some URLs redirect to ondemand can't be extracted with
            # this extractor right away thus should be passed through
            # ondemand extractor (e.g. https://vimeo.com/73445910)
            if VimeoOndemandIE.suitable(redirect_url):
                return self.url_result(redirect_url, VimeoOndemandIE.ie_key())
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

        cc_license = None
        timestamp = None

        # Extract the config JSON
        try:
            try:
                config_url = self._html_search_regex(
                    r' data-config-url="(.+?)"', webpage,
                    'config URL', default=None)
                if not config_url:
                    # Sometimes new react-based page is served instead of old one that require
                    # different config URL extraction approach (see
                    # https://github.com/ytdl-org/youtube-dl/pull/7209)
                    vimeo_clip_page_config = self._search_regex(
                        r'vimeo\.clip_page_config\s*=\s*({.+?});', webpage,
                        'vimeo clip page config')
                    page_config = self._parse_json(vimeo_clip_page_config, video_id)
                    config_url = page_config['player']['config_url']
                    cc_license = page_config.get('cc_license')
                    timestamp = try_get(
                        page_config, lambda x: x['clip']['uploaded_on'],
                        compat_str)
                config_json = self._download_webpage(config_url, video_id)
                config = json.loads(config_json)
            except RegexNotFoundError:
                # For pro videos or player.vimeo.com urls
                # We try to find out to which variable is assigned the config dic
                m_variable_name = re.search(r'(\w)\.video\.id', webpage)
                if m_variable_name is not None:
                    config_re = [r'%s=({[^}].+?});' % re.escape(m_variable_name.group(1))]
                else:
                    config_re = [r' = {config:({.+?}),assets:', r'(?:[abc])=({.+?});']
                config_re.append(r'\bvar\s+r\s*=\s*({.+?})\s*;')
                config_re.append(r'\bconfig\s*=\s*({.+?})\s*;')
                config = self._search_regex(config_re, webpage, 'info section',
                                            flags=re.DOTALL)
                config = json.loads(config)
        except Exception as e:
            if re.search('The creator of this video has not given you permission to embed it on this domain.', webpage):
                raise ExtractorError('The author has restricted the access to this video, try with the "--referer" option')

            if re.search(r'<form[^>]+?id="pw_form"', webpage) is not None:
                if '_video_password_verified' in data:
                    raise ExtractorError('video password verification failed!')
                self._verify_video_password(redirect_url, video_id, webpage)
                return self._real_extract(
                    smuggle_url(redirect_url, {'_video_password_verified': 'verified'}))
            else:
                raise ExtractorError('Unable to extract info section',
                                     cause=e)
        else:
            if config.get('view') == 4:
                config = self._verify_player_video_password(redirect_url, video_id, headers)

        vod = config.get('video', {}).get('vod', {})

        def is_rented():
            if '>You rented this title.<' in webpage:
                return True
            if config.get('user', {}).get('purchased'):
                return True
            for purchase_option in vod.get('purchase_options', []):
                if purchase_option.get('purchased'):
                    return True
                label = purchase_option.get('label_string')
                if label and (label.startswith('You rented this') or label.endswith(' remaining')):
                    return True
            return False

        if is_rented() and vod.get('is_trailer'):
            feature_id = vod.get('feature_id')
            if feature_id and not data.get('force_feature_id', False):
                return self.url_result(smuggle_url(
                    'https://player.vimeo.com/player/%s' % feature_id,
                    {'force_feature_id': True}), 'Vimeo')

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

        # Extract upload date
        if not timestamp:
            timestamp = self._search_regex(
                r'<time[^>]+datetime="([^"]+)"', webpage,
                'timestamp', default=None)

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

        source_format = self._extract_original_format(
            'https://vimeo.com/' + video_id, video_id)
        if source_format:
            formats.append(source_format)

        info_dict_config = self._parse_config(config, video_id)
        formats.extend(info_dict_config['formats'])
        self._vimeo_sort_formats(formats)

        json_ld = self._search_json_ld(webpage, video_id, default={})

        if not cc_license:
            cc_license = self._search_regex(
                r'<link[^>]+rel=["\']license["\'][^>]+href=(["\'])(?P<license>(?:(?!\1).)+)\1',
                webpage, 'license', default=None, group='license')

        channel_url = 'https://vimeo.com/channels/%s' % channel_id if channel_id else None

        info_dict = {
            'id': video_id,
            'formats': formats,
            'timestamp': unified_timestamp(timestamp),
            'description': video_description,
            'webpage_url': url,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'license': cc_license,
            'channel_id': channel_id,
            'channel_url': channel_url,
        }

        info_dict = merge_dicts(info_dict, info_dict_config, json_ld)

        return info_dict


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
            'uploader_url': r're:https?://(?:www\.)?vimeo\.com/gumfilms',
            'uploader_id': 'gumfilms',
        },
        'params': {
            'format': 'best[protocol=https]',
        },
    }, {
        # requires Referer to be passed along with og:video:url
        'url': 'https://vimeo.com/ondemand/36938/126682985',
        'info_dict': {
            'id': '126682985',
            'ext': 'mp4',
            'title': 'Rävlock, rätt läte på rätt plats',
            'uploader': 'Lindroth & Norin',
            'uploader_url': r're:https?://(?:www\.)?vimeo\.com/user14430847',
            'uploader_id': 'user14430847',
        },
        'params': {
            'skip_download': True,
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
        return self.url_result(
            # Some videos require Referer to be passed along with og:video:url
            # similarly to generic vimeo embeds (e.g.
            # https://vimeo.com/ondemand/36938/126682985).
            VimeoIE._smuggle_referrer(self._og_search_video_url(webpage), url),
            VimeoIE.ie_key())


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

            # Try extracting href first since not all videos are available via
            # short https://vimeo.com/id URL (e.g. https://vimeo.com/channels/tributes/6213729)
            clips = re.findall(
                r'id="clip_(\d+)"[^>]*>\s*<a[^>]+href="(/(?:[^/]+/)*\1)(?:[^>]+\btitle="([^"]+)")?', webpage)
            if clips:
                for video_id, video_url, video_title in clips:
                    yield self.url_result(
                        compat_urlparse.urljoin(base_url, video_url),
                        VimeoIE.ie_key(), video_id=video_id, video_title=video_title)
            # More relaxed fallback
            else:
                for video_id in re.findall(r'id=["\']clip_(\d+)', webpage):
                    yield self.url_result(
                        'https://vimeo.com/%s' % video_id,
                        VimeoIE.ie_key(), video_id=video_id)

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
    _VALID_URL = r'https://vimeo\.com/album/(?P<id>\d+)(?:$|[?#]|/(?!video))'
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
    }, {
        'url': 'https://vimeo.com/album/2632481/sort:plays/format:thumbnail',
        'only_matching': True,
    }, {
        # TODO: respect page number
        'url': 'https://vimeo.com/album/2632481/page:2/sort:plays/format:thumbnail',
        'only_matching': True,
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


class VimeoReviewIE(VimeoBaseInfoExtractor):
    IE_NAME = 'vimeo:review'
    IE_DESC = 'Review pages on vimeo'
    _VALID_URL = r'(?P<url>https://vimeo\.com/[^/]+/review/(?P<id>[^/]+)/[0-9a-f]{10})'
    _TESTS = [{
        'url': 'https://vimeo.com/user21297594/review/75524534/3c257a1b5d',
        'md5': 'c507a72f780cacc12b2248bb4006d253',
        'info_dict': {
            'id': '75524534',
            'ext': 'mp4',
            'title': "DICK HARDWICK 'Comedian'",
            'uploader': 'Richard Hardwick',
            'uploader_id': 'user21297594',
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
            'thumbnail': r're:^https?://.*\.jpg$',
            'uploader_id': 'user22258446',
        }
    }, {
        'note': 'Password protected',
        'url': 'https://vimeo.com/user37284429/review/138823582/c4d865efde',
        'info_dict': {
            'id': '138823582',
            'ext': 'mp4',
            'title': 'EFFICIENT PICKUP MASTERCLASS MODULE 1',
            'uploader': 'TMB',
            'uploader_id': 'user37284429',
        },
        'params': {
            'videopassword': 'holygrail',
        },
        'skip': 'video gone',
    }]

    def _real_initialize(self):
        self._login()

    def _get_config_url(self, webpage_url, video_id, video_password_verified=False):
        webpage = self._download_webpage(webpage_url, video_id)
        config_url = self._html_search_regex(
            r'data-config-url=(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
            'config URL', default=None, group='url')
        if not config_url:
            data = self._parse_json(self._search_regex(
                r'window\s*=\s*_extend\(window,\s*({.+?})\);', webpage, 'data',
                default=NO_DEFAULT if video_password_verified else '{}'), video_id)
            config = data.get('vimeo_esi', {}).get('config', {})
            config_url = config.get('configUrl') or try_get(config, lambda x: x['clipData']['configUrl'])
        if config_url is None:
            self._verify_video_password(webpage_url, video_id, webpage)
            config_url = self._get_config_url(
                webpage_url, video_id, video_password_verified=True)
        return config_url

    def _real_extract(self, url):
        page_url, video_id = re.match(self._VALID_URL, url).groups()
        config_url = self._get_config_url(url, video_id)
        config = self._download_json(config_url, video_id)
        info_dict = self._parse_config(config, video_id)
        source_format = self._extract_original_format(page_url, video_id)
        if source_format:
            info_dict['formats'].append(source_format)
        self._vimeo_sort_formats(info_dict['formats'])
        info_dict['id'] = video_id
        return info_dict


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
    _VALID_URL = r'https://(?:www\.)?vimeo\.com/(?P<id>[^/]+)/likes/?(?:$|[?#]|sort:)'
    IE_NAME = 'vimeo:likes'
    IE_DESC = 'Vimeo user likes'
    _TESTS = [{
        'url': 'https://vimeo.com/user755559/likes/',
        'playlist_mincount': 293,
        'info_dict': {
            'id': 'user755559_likes',
            'description': 'See all the videos urza likes',
            'title': 'Videos urza likes',
        },
    }, {
        'url': 'https://vimeo.com/stormlapse/likes',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        user_id = self._match_id(url)
        webpage = self._download_webpage(url, user_id)
        page_count = self._int(
            self._search_regex(
                r'''(?x)<li><a\s+href="[^"]+"\s+data-page="([0-9]+)">
                    .*?</a></li>\s*<li\s+class="pagination_next">
                ''', webpage, 'page count', default=1),
            'page count', fatal=True)
        PAGE_SIZE = 12
        title = self._html_search_regex(
            r'(?s)<h1>(.+?)</h1>', webpage, 'title', fatal=False)
        description = self._html_search_meta('description', webpage)

        def _get_page(idx):
            page_url = 'https://vimeo.com/%s/likes/page:%d/sort:date' % (
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
            'id': '%s_likes' % user_id,
            'title': title,
            'description': description,
            'entries': pl,
        }


class VHXEmbedIE(InfoExtractor):
    IE_NAME = 'vhx:embed'
    _VALID_URL = r'https?://embed\.vhx\.tv/videos/(?P<id>\d+)'

    def _call_api(self, video_id, access_token, path='', query=None):
        return self._download_json(
            'https://api.vhx.tv/videos/' + video_id + path, video_id, headers={
                'Authorization': 'Bearer ' + access_token,
            }, query=query)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        credentials = self._parse_json(self._search_regex(
            r'(?s)credentials\s*:\s*({.+?}),', webpage,
            'config'), video_id, js_to_json)
        access_token = credentials['access_token']

        query = {}
        for k, v in credentials.items():
            if k in ('authorization', 'authUserToken', 'ticket') and v and v != 'undefined':
                if k == 'authUserToken':
                    query['auth_user_token'] = v
                else:
                    query[k] = v
        files = self._call_api(video_id, access_token, '/files', query)

        formats = []
        for f in files:
            href = try_get(f, lambda x: x['_links']['source']['href'])
            if not href:
                continue
            method = f.get('method')
            if method == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    href, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif method == 'dash':
                formats.extend(self._extract_mpd_formats(
                    href, video_id, mpd_id='dash', fatal=False))
            else:
                fmt = {
                    'filesize': int_or_none(try_get(f, lambda x: x['size']['bytes'])),
                    'format_id': 'http',
                    'preference': 1,
                    'url': href,
                    'vcodec': f.get('codec'),
                }
                quality = f.get('quality')
                if quality:
                    fmt.update({
                        'format_id': 'http-' + quality,
                        'height': int_or_none(self._search_regex(r'(\d+)p', quality, 'height', default=None)),
                    })
                formats.append(fmt)
        self._sort_formats(formats)

        video_data = self._call_api(video_id, access_token)
        title = video_data.get('title') or video_data['name']

        subtitles = {}
        for subtitle in try_get(video_data, lambda x: x['tracks']['subtitles'], list) or []:
            lang = subtitle.get('srclang') or subtitle.get('label')
            for _link in subtitle.get('_links', {}).values():
                href = _link.get('href')
                if not href:
                    continue
                subtitles.setdefault(lang, []).append({
                    'url': href,
                })

        q = qualities(['small', 'medium', 'large', 'source'])
        thumbnails = []
        for thumbnail_id, thumbnail_url in video_data.get('thumbnail', {}).items():
            thumbnails.append({
                'id': thumbnail_id,
                'url': thumbnail_url,
                'preference': q(thumbnail_id),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('description'),
            'duration': int_or_none(try_get(video_data, lambda x: x['duration']['seconds'])),
            'formats': formats,
            'subtitles': subtitles,
            'thumbnails': thumbnails,
            'timestamp': unified_timestamp(video_data.get('created_at')),
            'view_count': int_or_none(video_data.get('plays_count')),
        }
