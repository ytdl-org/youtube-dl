# coding: utf-8

import json
import netrc
import re
import socket

from .common import InfoExtractor, SearchInfoExtractor
from ..utils import (
    compat_http_client,
    compat_parse_qs,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,
    compat_str,

    clean_html,
    get_element_by_id,
    ExtractorError,
    unescapeHTML,
    unified_strdate,
)


class YoutubeIE(InfoExtractor):
    IE_DESC = u'YouTube.com'
    _VALID_URL = r"""^
                     (
                         (?:https?://)?                                       # http(s):// (optional)
                         (?:youtu\.be/|(?:\w+\.)?youtube(?:-nocookie)?\.com/|
                            tube\.majestyc\.net/)                             # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/)                               # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:watch|movie(?:_popup)?(?:\.php)?)?              # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?&)?                                    # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         )?                                                   # optional -> youtube.com/xxxx is OK
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]+)                                         # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""
    _LANG_URL = r'https://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    _NETRC_MACHINE = 'youtube'
    # Listed in order of quality
    _available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '17', '13']
    _available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '17', '13']
    _video_extensions = {
        '13': '3gp',
        '17': 'mp4',
        '18': 'mp4',
        '22': 'mp4',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',
    }
    _video_dimensions = {
        '5': '240x400',
        '6': '???',
        '13': '???',
        '17': '144x176',
        '18': '360x640',
        '22': '720x1280',
        '34': '360x640',
        '35': '480x854',
        '37': '1080x1920',
        '38': '3072x4096',
        '43': '360x640',
        '44': '480x854',
        '45': '720x1280',
        '46': '1080x1920',
    }
    IE_NAME = u'youtube'
    _TESTS = [
        {
            u"url":  u"http://www.youtube.com/watch?v=BaW_jenozKc",
            u"file":  u"BaW_jenozKc.mp4",
            u"info_dict": {
                u"title": u"youtube-dl test video \"'/\\ä↭𝕐",
                u"uploader": u"Philipp Hagemeister",
                u"uploader_id": u"phihag",
                u"upload_date": u"20121002",
                u"description": u"test chars:  \"'/\\ä↭𝕐\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de ."
            }
        },
        {
            u"url":  u"http://www.youtube.com/watch?v=1ltcDfZMA3U",
            u"file":  u"1ltcDfZMA3U.flv",
            u"note": u"Test VEVO video (#897)",
            u"info_dict": {
                u"upload_date": u"20070518",
                u"title": u"Maps - It Will Find You",
                u"description": u"Music video by Maps performing It Will Find You.",
                u"uploader": u"MuteUSA",
                u"uploader_id": u"MuteUSA"
            }
        },
        {
            u"url":  u"http://www.youtube.com/watch?v=UxxajLWwzqY",
            u"file":  u"UxxajLWwzqY.mp4",
            u"note": u"Test generic use_cipher_signature video (#897)",
            u"info_dict": {
                u"upload_date": u"20120506",
                u"title": u"Icona Pop - I Love It (feat. Charli XCX) [OFFICIAL VIDEO]",
                u"description": u"md5:b085c9804f5ab69f4adea963a2dceb3c",
                u"uploader": u"IconaPop",
                u"uploader_id": u"IconaPop"
            }
        }
    ]


    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        if YoutubePlaylistIE.suitable(url): return False
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def report_lang(self):
        """Report attempt to set language."""
        self.to_screen(u'Setting language')

    def report_login(self):
        """Report attempt to log in."""
        self.to_screen(u'Logging in')

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self.to_screen(u'%s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Downloading video info webpage' % video_id)

    def report_video_subtitles_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Checking available subtitles' % video_id)

    def report_video_subtitles_request(self, video_id, sub_lang, format):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Downloading video subtitles for %s.%s' % (video_id, sub_lang, format))

    def report_video_subtitles_available(self, video_id, sub_lang_list):
        """Report available subtitles."""
        sub_lang = ",".join(list(sub_lang_list.keys()))
        self.to_screen(u'%s: Available subtitles for video: %s' % (video_id, sub_lang))

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self.to_screen(u'%s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        self.to_screen(u'%s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        self.to_screen(u'RTMP download detected')

    def _decrypt_signature(self, s):
        """Turn the encrypted s field into a working signature"""

        if len(s) == 88:
            return s[48] + s[81:67:-1] + s[82] + s[66:62:-1] + s[85] + s[61:48:-1] + s[67] + s[47:12:-1] + s[3] + s[11:3:-1] + s[2] + s[12]
        elif len(s) == 87:
            return s[62] + s[82:62:-1] + s[83] + s[61:52:-1] + s[0] + s[51:2:-1]
        elif len(s) == 86:
            return s[2:63] + s[82] + s[64:82] + s[63]
        elif len(s) == 85:
            return s[76] + s[82:76:-1] + s[83] + s[75:60:-1] + s[0] + s[59:50:-1] + s[1] + s[49:2:-1]
        elif len(s) == 84:
            return s[83:36:-1] + s[2] + s[35:26:-1] + s[3] + s[25:3:-1] + s[26]
        elif len(s) == 83:
            return s[52] + s[81:55:-1] + s[2] + s[54:52:-1] + s[82] + s[51:36:-1] + s[55] + s[35:2:-1] + s[36]
        elif len(s) == 82:
            return s[36] + s[79:67:-1] + s[81] + s[66:40:-1] + s[33] + s[39:36:-1] + s[40] + s[35] + s[0] + s[67] + s[32:0:-1] + s[34]

        else:
            raise ExtractorError(u'Unable to decrypt signature, key length %d not supported; retrying might work' % (len(s)))

    def _get_available_subtitles(self, video_id):
        self.report_video_subtitles_download(video_id)
        request = compat_urllib_request.Request('http://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id)
        try:
            sub_list = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            return (u'unable to download video subtitles: %s' % compat_str(err), None)
        sub_lang_list = re.findall(r'name="([^"]*)"[^>]+lang_code="([\w\-]+)"', sub_list)
        sub_lang_list = dict((l[1], l[0]) for l in sub_lang_list)
        if not sub_lang_list:
            return (u'video doesn\'t have subtitles', None)
        return sub_lang_list

    def _list_available_subtitles(self, video_id):
        sub_lang_list = self._get_available_subtitles(video_id)
        self.report_video_subtitles_available(video_id, sub_lang_list)

    def _request_subtitle(self, sub_lang, sub_name, video_id, format):
        """
        Return tuple:
        (error_message, sub_lang, sub)
        """
        self.report_video_subtitles_request(video_id, sub_lang, format)
        params = compat_urllib_parse.urlencode({
            'lang': sub_lang,
            'name': sub_name,
            'v': video_id,
            'fmt': format,
        })
        url = 'http://www.youtube.com/api/timedtext?' + params
        try:
            sub = compat_urllib_request.urlopen(url).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            return (u'unable to download video subtitles: %s' % compat_str(err), None, None)
        if not sub:
            return (u'Did not fetch video subtitles', None, None)
        return (None, sub_lang, sub)

    def _request_automatic_caption(self, video_id, webpage):
        """We need the webpage for getting the captions url, pass it as an
           argument to speed up the process."""
        sub_lang = self._downloader.params.get('subtitleslang') or 'en'
        sub_format = self._downloader.params.get('subtitlesformat')
        self.to_screen(u'%s: Looking for automatic captions' % video_id)
        mobj = re.search(r';ytplayer.config = ({.*?});', webpage)
        err_msg = u'Couldn\'t find automatic captions for "%s"' % sub_lang
        if mobj is None:
            return [(err_msg, None, None)]
        player_config = json.loads(mobj.group(1))
        try:
            args = player_config[u'args']
            caption_url = args[u'ttsurl']
            timestamp = args[u'timestamp']
            params = compat_urllib_parse.urlencode({
                'lang': 'en',
                'tlang': sub_lang,
                'fmt': sub_format,
                'ts': timestamp,
                'kind': 'asr',
            })
            subtitles_url = caption_url + '&' + params
            sub = self._download_webpage(subtitles_url, video_id, u'Downloading automatic captions')
            return [(None, sub_lang, sub)]
        except KeyError:
            return [(err_msg, None, None)]

    def _extract_subtitle(self, video_id):
        """
        Return a list with a tuple:
        [(error_message, sub_lang, sub)]
        """
        sub_lang_list = self._get_available_subtitles(video_id)
        sub_format = self._downloader.params.get('subtitlesformat')
        if  isinstance(sub_lang_list,tuple): #There was some error, it didn't get the available subtitles
            return [(sub_lang_list[0], None, None)]
        if self._downloader.params.get('subtitleslang', False):
            sub_lang = self._downloader.params.get('subtitleslang')
        elif 'en' in sub_lang_list:
            sub_lang = 'en'
        else:
            sub_lang = list(sub_lang_list.keys())[0]
        if not sub_lang in sub_lang_list:
            return [(u'no closed captions found in the specified language "%s"' % sub_lang, None, None)]

        subtitle = self._request_subtitle(sub_lang, sub_lang_list[sub_lang].encode('utf-8'), video_id, sub_format)
        return [subtitle]

    def _extract_all_subtitles(self, video_id):
        sub_lang_list = self._get_available_subtitles(video_id)
        sub_format = self._downloader.params.get('subtitlesformat')
        if  isinstance(sub_lang_list,tuple): #There was some error, it didn't get the available subtitles
            return [(sub_lang_list[0], None, None)]
        subtitles = []
        for sub_lang in sub_lang_list:
            subtitle = self._request_subtitle(sub_lang, sub_lang_list[sub_lang].encode('utf-8'), video_id, sub_format)
            subtitles.append(subtitle)
        return subtitles

    def _print_formats(self, formats):
        print('Available formats:')
        for x in formats:
            print('%s\t:\t%s\t[%s]' %(x, self._video_extensions.get(x, 'flv'), self._video_dimensions.get(x, '???')))

    def _real_initialize(self):
        if self._downloader is None:
            return

        username = None
        password = None
        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get('username', None) is not None:
            username = downloader_params['username']
            password = downloader_params['password']
        elif downloader_params.get('usenetrc', False):
            try:
                info = netrc.netrc().authenticators(self._NETRC_MACHINE)
                if info is not None:
                    username = info[0]
                    password = info[2]
                else:
                    raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
            except (IOError, netrc.NetrcParseError) as err:
                self._downloader.report_warning(u'parsing .netrc: %s' % compat_str(err))
                return

        # Set language
        request = compat_urllib_request.Request(self._LANG_URL)
        try:
            self.report_lang()
            compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to set language: %s' % compat_str(err))
            return

        # No authentication to be performed
        if username is None:
            return

        request = compat_urllib_request.Request(self._LOGIN_URL)
        try:
            login_page = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to fetch login page: %s' % compat_str(err))
            return

        galx = None
        dsh = None
        match = re.search(re.compile(r'<input.+?name="GALX".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          galx = match.group(1)

        match = re.search(re.compile(r'<input.+?name="dsh".+?value="(.+?)"', re.DOTALL), login_page)
        if match:
          dsh = match.group(1)

        # Log in
        login_form_strs = {
                u'continue': u'https://www.youtube.com/signin?action_handle_signin=true&feature=sign_in_button&hl=en_US&nomobiletemp=1',
                u'Email': username,
                u'GALX': galx,
                u'Passwd': password,
                u'PersistentCookie': u'yes',
                u'_utf8': u'霱',
                u'bgresponse': u'js_disabled',
                u'checkConnection': u'',
                u'checkedDomains': u'youtube',
                u'dnConn': u'',
                u'dsh': dsh,
                u'pstMsg': u'0',
                u'rmShown': u'1',
                u'secTok': u'',
                u'signIn': u'Sign in',
                u'timeStmp': u'',
                u'service': u'youtube',
                u'uilel': u'3',
                u'hl': u'en_US',
        }
        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k,v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')
        request = compat_urllib_request.Request(self._LOGIN_URL, login_data)
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read().decode('utf-8')
            if re.search(r'(?i)<form[^>]* id="gaia_loginform"', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username or password')
                return
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return

        # Confirm age
        age_form = {
                'next_url':     '/',
                'action_confirm':   'Confirm',
                }
        request = compat_urllib_request.Request(self._AGE_URL, compat_urllib_parse.urlencode(age_form))
        try:
            self.report_age_confirmation()
            compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to confirm age: %s' % compat_str(err))

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _real_extract(self, url):
        if re.match(r'(?:https?://)?[^/]+/watch\?feature=[a-z_]+$', url):
            self._downloader.report_warning(u'Did you forget to quote the URL? Remember that & is a meta-character in most shells, so you want to put the URL in quotes, like  youtube-dl \'http://www.youtube.com/watch?feature=foo&v=BaW_jenozKc\' (or simply  youtube-dl BaW_jenozKc  ).')

        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = 'https://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self._extract_id(url)

        # Get video webpage
        self.report_video_webpage_download(video_id)
        url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
        request = compat_urllib_request.Request(url)
        try:
            video_webpage_bytes = compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            raise ExtractorError(u'Unable to download video webpage: %s' % compat_str(err))

        video_webpage = video_webpage_bytes.decode('utf-8', 'ignore')

        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(http:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = None

        # Get video info
        self.report_video_info_webpage_download(video_id)
        for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
            video_info_url = ('https://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                    % (video_id, el_type))
            video_info_webpage = self._download_webpage(video_info_url, video_id,
                                    note=False,
                                    errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
            if 'token' in video_info:
                break
        if 'token' not in video_info:
            if 'reason' in video_info:
                raise ExtractorError(u'YouTube said: %s' % video_info['reason'][0], expected=True)
            else:
                raise ExtractorError(u'"token" parameter not in video info for unknown reason')

        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            raise ExtractorError(u'"rental" videos not supported')

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            raise ExtractorError(u'Unable to extract uploader name')
        video_uploader = compat_urllib_parse.unquote_plus(video_info['author'][0])

        # uploader_id
        video_uploader_id = None
        mobj = re.search(r'<link itemprop="url" href="http://www.youtube.com/(?:user|channel)/([^"]+)">', video_webpage)
        if mobj is not None:
            video_uploader_id = mobj.group(1)
        else:
            self._downloader.report_warning(u'unable to extract uploader nickname')

        # title
        if 'title' not in video_info:
            raise ExtractorError(u'Unable to extract video title')
        video_title = compat_urllib_parse.unquote_plus(video_info['title'][0])

        # thumbnail image
        if 'thumbnail_url' not in video_info:
            self._downloader.report_warning(u'unable to extract video thumbnail')
            video_thumbnail = ''
        else:   # don't panic if we can't find it
            video_thumbnail = compat_urllib_parse.unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = None
        mobj = re.search(r'id="eow-date.*?>(.*?)</span>', video_webpage, re.DOTALL)
        if mobj is not None:
            upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
            upload_date = unified_strdate(upload_date)

        # description
        video_description = get_element_by_id("eow-description", video_webpage)
        if video_description:
            video_description = clean_html(video_description)
        else:
            fd_mobj = re.search(r'<meta name="description" content="([^"]+)"', video_webpage)
            if fd_mobj:
                video_description = unescapeHTML(fd_mobj.group(1))
            else:
                video_description = u''

        # subtitles
        video_subtitles = None

        if self._downloader.params.get('writesubtitles', False):
            video_subtitles = self._extract_subtitle(video_id)
            if video_subtitles:
                (sub_error, sub_lang, sub) = video_subtitles[0]
                if sub_error:
                    self._downloader.report_warning(sub_error)
        
        if self._downloader.params.get('writeautomaticsub', False):
            video_subtitles = self._request_automatic_caption(video_id, video_webpage)
            (sub_error, sub_lang, sub) = video_subtitles[0]
            if sub_error:
                self._downloader.report_warning(sub_error)

        if self._downloader.params.get('allsubtitles', False):
            video_subtitles = self._extract_all_subtitles(video_id)
            for video_subtitle in video_subtitles:
                (sub_error, sub_lang, sub) = video_subtitle
                if sub_error:
                    self._downloader.report_warning(sub_error)

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id)
            return

        if 'length_seconds' not in video_info:
            self._downloader.report_warning(u'unable to extract video duration')
            video_duration = ''
        else:
            video_duration = compat_urllib_parse.unquote_plus(video_info['length_seconds'][0])

        # Decide which formats to download
        req_format = self._downloader.params.get('format', None)

        try:
            mobj = re.search(r';ytplayer.config = ({.*?});', video_webpage)
            if not mobj:
                raise ValueError('Could not find vevo ID')
            info = json.loads(mobj.group(1))
            args = info['args']
            # Easy way to know if the 's' value is in url_encoded_fmt_stream_map
            # this signatures are encrypted
            m_s = re.search(r'[&,]s=', args['url_encoded_fmt_stream_map'])
            if m_s is not None:
                self.to_screen(u'%s: Encrypted signatures detected.' % video_id)
                video_info['url_encoded_fmt_stream_map'] = [args['url_encoded_fmt_stream_map']]
        except ValueError:
            pass

        if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
            self.report_rtmp_download()
            video_url_list = [(None, video_info['conn'][0])]
        elif 'url_encoded_fmt_stream_map' in video_info and len(video_info['url_encoded_fmt_stream_map']) >= 1:
            url_map = {}
            for url_data_str in video_info['url_encoded_fmt_stream_map'][0].split(','):
                url_data = compat_parse_qs(url_data_str)
                if 'itag' in url_data and 'url' in url_data:
                    url = url_data['url'][0]
                    if 'sig' in url_data:
                        url += '&signature=' + url_data['sig'][0]
                    elif 's' in url_data:
                        if self._downloader.params.get('verbose'):
                            s = url_data['s'][0]
                            player = self._search_regex(r'html5player-(.+?)\.js', video_webpage,
                                'html5 player', fatal=False)
                            self.to_screen('encrypted signature length %d (%d.%d), itag %s, html5 player %s' %
                                (len(s), len(s.split('.')[0]), len(s.split('.')[1]), url_data['itag'][0], player))
                        signature = self._decrypt_signature(url_data['s'][0])
                        url += '&signature=' + signature
                    if 'ratebypass' not in url:
                        url += '&ratebypass=yes'
                    url_map[url_data['itag'][0]] = url

            format_limit = self._downloader.params.get('format_limit', None)
            available_formats = self._available_formats_prefer_free if self._downloader.params.get('prefer_free_formats', False) else self._available_formats
            if format_limit is not None and format_limit in available_formats:
                format_list = available_formats[available_formats.index(format_limit):]
            else:
                format_list = available_formats
            existing_formats = [x for x in format_list if x in url_map]
            if len(existing_formats) == 0:
                raise ExtractorError(u'no known formats available for video')
            if self._downloader.params.get('listformats', None):
                self._print_formats(existing_formats)
                return
            if req_format is None or req_format == 'best':
                video_url_list = [(existing_formats[0], url_map[existing_formats[0]])] # Best quality
            elif req_format == 'worst':
                video_url_list = [(existing_formats[-1], url_map[existing_formats[-1]])] # worst quality
            elif req_format in ('-1', 'all'):
                video_url_list = [(f, url_map[f]) for f in existing_formats] # All formats
            else:
                # Specific formats. We pick the first in a slash-delimeted sequence.
                # For example, if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
                req_formats = req_format.split('/')
                video_url_list = None
                for rf in req_formats:
                    if rf in url_map:
                        video_url_list = [(rf, url_map[rf])]
                        break
                if video_url_list is None:
                    raise ExtractorError(u'requested format not available')
        else:
            raise ExtractorError(u'no conn or url_encoded_fmt_stream_map information found in video info')

        results = []
        for format_param, video_real_url in video_url_list:
            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')

            video_format = '{0} - {1}'.format(format_param if format_param else video_extension,
                                              self._video_dimensions.get(format_param, '???'))

            results.append({
                'id':       video_id,
                'url':      video_real_url,
                'uploader': video_uploader,
                'uploader_id': video_uploader_id,
                'upload_date':  upload_date,
                'title':    video_title,
                'ext':      video_extension,
                'format':   video_format,
                'thumbnail':    video_thumbnail,
                'description':  video_description,
                'player_url':   player_url,
                'subtitles':    video_subtitles,
                'duration':     video_duration
            })
        return results

class YoutubePlaylistIE(InfoExtractor):
    IE_DESC = u'YouTube.com playlists'
    _VALID_URL = r"""(?:
                        (?:https?://)?
                        (?:\w+\.)?
                        youtube\.com/
                        (?:
                           (?:course|view_play_list|my_playlists|artist|playlist|watch)
                           \? (?:.*?&)*? (?:p|a|list)=
                        |  p/
                        )
                        ((?:PL|EC|UU)?[0-9A-Za-z-_]{10,})
                        .*
                     |
                        ((?:PL|EC|UU)[0-9A-Za-z-_]{10,})
                     )"""
    _TEMPLATE_URL = 'https://gdata.youtube.com/feeds/api/playlists/%s?max-results=%i&start-index=%i&v=2&alt=json&safeSearch=none'
    _MAX_RESULTS = 50
    IE_NAME = u'youtube:playlist'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def _real_extract(self, url):
        # Extract playlist id
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # Download playlist videos from API
        playlist_id = mobj.group(1) or mobj.group(2)
        page_num = 1
        videos = []

        while True:
            url = self._TEMPLATE_URL % (playlist_id, self._MAX_RESULTS, self._MAX_RESULTS * (page_num - 1) + 1)
            page = self._download_webpage(url, playlist_id, u'Downloading page #%s' % page_num)

            try:
                response = json.loads(page)
            except ValueError as err:
                raise ExtractorError(u'Invalid JSON in API response: ' + compat_str(err))

            if 'feed' not in response:
                raise ExtractorError(u'Got a malformed response from YouTube API')
            playlist_title = response['feed']['title']['$t']
            if 'entry' not in response['feed']:
                # Number of videos is a multiple of self._MAX_RESULTS
                break

            for entry in response['feed']['entry']:
                index = entry['yt$position']['$t']
                if 'media$group' in entry and 'media$player' in entry['media$group']:
                    videos.append((index, entry['media$group']['media$player']['url']))

            if len(response['feed']['entry']) < self._MAX_RESULTS:
                break
            page_num += 1

        videos = [v[1] for v in sorted(videos)]

        url_results = [self.url_result(url, 'Youtube') for url in videos]
        return [self.playlist_result(url_results, playlist_id, playlist_title)]


class YoutubeChannelIE(InfoExtractor):
    IE_DESC = u'YouTube.com channels'
    _VALID_URL = r"^(?:https?://)?(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/([0-9A-Za-z_-]+)"
    _TEMPLATE_URL = 'http://www.youtube.com/channel/%s/videos?sort=da&flow=list&view=0&page=%s&gl=US&hl=en'
    _MORE_PAGES_INDICATOR = 'yt-uix-load-more'
    _MORE_PAGES_URL = 'http://www.youtube.com/channel_ajax?action_load_more_videos=1&flow=list&paging=%s&view=0&sort=da&channel_id=%s'
    IE_NAME = u'youtube:channel'

    def extract_videos_from_page(self, page):
        ids_in_page = []
        for mobj in re.finditer(r'href="/watch\?v=([0-9A-Za-z_-]+)&?', page):
            if mobj.group(1) not in ids_in_page:
                ids_in_page.append(mobj.group(1))
        return ids_in_page

    def _real_extract(self, url):
        # Extract channel id
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        # Download channel page
        channel_id = mobj.group(1)
        video_ids = []
        pagenum = 1

        url = self._TEMPLATE_URL % (channel_id, pagenum)
        page = self._download_webpage(url, channel_id,
                                      u'Downloading page #%s' % pagenum)

        # Extract video identifiers
        ids_in_page = self.extract_videos_from_page(page)
        video_ids.extend(ids_in_page)

        # Download any subsequent channel pages using the json-based channel_ajax query
        if self._MORE_PAGES_INDICATOR in page:
            while True:
                pagenum = pagenum + 1

                url = self._MORE_PAGES_URL % (pagenum, channel_id)
                page = self._download_webpage(url, channel_id,
                                              u'Downloading page #%s' % pagenum)

                page = json.loads(page)

                ids_in_page = self.extract_videos_from_page(page['content_html'])
                video_ids.extend(ids_in_page)

                if self._MORE_PAGES_INDICATOR  not in page['load_more_widget_html']:
                    break

        self._downloader.to_screen(u'[youtube] Channel %s: Found %i videos' % (channel_id, len(video_ids)))

        urls = ['http://www.youtube.com/watch?v=%s' % id for id in video_ids]
        url_entries = [self.url_result(url, 'Youtube') for url in urls]
        return [self.playlist_result(url_entries, channel_id)]


class YoutubeUserIE(InfoExtractor):
    IE_DESC = u'YouTube.com user videos (URL or "ytuser" keyword)'
    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/user/)|ytuser:)([A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'http://gdata.youtube.com/feeds/api/users/%s'
    _GDATA_PAGE_SIZE = 50
    _GDATA_URL = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d'
    _VIDEO_INDICATOR = r'/watch\?v=(.+?)[\<&]'
    IE_NAME = u'youtube:user'

    def _real_extract(self, url):
        # Extract username
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        username = mobj.group(1)

        # Download video ids using YouTube Data API. Result size per
        # query is limited (currently to 50 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        video_ids = []
        pagenum = 0

        while True:
            start_index = pagenum * self._GDATA_PAGE_SIZE + 1

            gdata_url = self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index)
            page = self._download_webpage(gdata_url, username,
                                          u'Downloading video ids from %d to %d' % (start_index, start_index + self._GDATA_PAGE_SIZE))

            # Extract video identifiers
            ids_in_page = []

            for mobj in re.finditer(self._VIDEO_INDICATOR, page):
                if mobj.group(1) not in ids_in_page:
                    ids_in_page.append(mobj.group(1))

            video_ids.extend(ids_in_page)

            # A little optimization - if current page is not
            # "full", ie. does not contain PAGE_SIZE video ids then
            # we can assume that this page is the last one - there
            # are no more ids on further pages - no need to query
            # again.

            if len(ids_in_page) < self._GDATA_PAGE_SIZE:
                break

            pagenum += 1

        urls = ['http://www.youtube.com/watch?v=%s' % video_id for video_id in video_ids]
        url_results = [self.url_result(url, 'Youtube') for url in urls]
        return [self.playlist_result(url_results, playlist_title = username)]

class YoutubeSearchIE(SearchInfoExtractor):
    IE_DESC = u'YouTube.com searches'
    _API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc'
    _MAX_RESULTS = 1000
    IE_NAME = u'youtube:search'
    _SEARCH_KEY = 'ytsearch'

    def report_download_page(self, query, pagenum):
        """Report attempt to download search page with given number."""
        self._downloader.to_screen(u'[youtube] query "%s": Downloading page %s' % (query, pagenum))

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        video_ids = []
        pagenum = 0
        limit = n

        while (50 * pagenum) < limit:
            self.report_download_page(query, pagenum+1)
            result_url = self._API_URL % (compat_urllib_parse.quote_plus(query), (50*pagenum)+1)
            request = compat_urllib_request.Request(result_url)
            try:
                data = compat_urllib_request.urlopen(request).read().decode('utf-8')
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                raise ExtractorError(u'Unable to download API page: %s' % compat_str(err))
            api_response = json.loads(data)['data']

            if not 'items' in api_response:
                raise ExtractorError(u'[youtube] No video results')

            new_ids = list(video['id'] for video in api_response['items'])
            video_ids += new_ids

            limit = min(n, api_response['totalItems'])
            pagenum += 1

        if len(video_ids) > n:
            video_ids = video_ids[:n]
        videos = [self.url_result('http://www.youtube.com/watch?v=%s' % id, 'Youtube') for id in video_ids]
        return self.playlist_result(videos, query)


class YoutubeShowIE(InfoExtractor):
    IE_DESC = u'YouTube.com (multi-season) shows'
    _VALID_URL = r'https?://www\.youtube\.com/show/(.*)'
    IE_NAME = u'youtube:show'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        show_name = mobj.group(1)
        webpage = self._download_webpage(url, show_name, u'Downloading show webpage')
        # There's one playlist for each season of the show
        m_seasons = list(re.finditer(r'href="(/playlist\?list=.*?)"', webpage))
        self.to_screen(u'%s: Found %s seasons' % (show_name, len(m_seasons)))
        return [self.url_result('https://www.youtube.com' + season.group(1), 'YoutubePlaylist') for season in m_seasons]
