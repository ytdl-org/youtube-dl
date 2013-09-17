# coding: utf-8

import json
import netrc
import re
import socket
import itertools
import xml.etree.ElementTree

from .common import InfoExtractor, SearchInfoExtractor
from .subtitles import SubtitlesInfoExtractor
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
    orderedSet,
)

class YoutubeBaseInfoExtractor(InfoExtractor):
    """Provide base functions for Youtube extractors"""
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _LANG_URL = r'https://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NETRC_MACHINE = 'youtube'
    # If True it will raise an error if no login info is provided
    _LOGIN_REQUIRED = False

    def report_lang(self):
        """Report attempt to set language."""
        self.to_screen(u'Setting language')

    def _set_language(self):
        request = compat_urllib_request.Request(self._LANG_URL)
        try:
            self.report_lang()
            compat_urllib_request.urlopen(request).read()
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to set language: %s' % compat_str(err))
            return False
        return True

    def _login(self):
        (username, password) = self._get_login_info()
        # No authentication to be performed
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError(u'No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return False

        request = compat_urllib_request.Request(self._LOGIN_URL)
        try:
            login_page = compat_urllib_request.urlopen(request).read().decode('utf-8')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to fetch login page: %s' % compat_str(err))
            return False

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
                return False
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return False
        return True

    def _confirm_age(self):
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
        return True

    def _real_initialize(self):
        if self._downloader is None:
            return
        if not self._set_language():
            return
        if not self._login():
            return
        self._confirm_age()


class YoutubeIE(YoutubeBaseInfoExtractor, SubtitlesInfoExtractor):
    IE_DESC = u'YouTube.com'
    _VALID_URL = r"""^
                     (
                         (?:https?://)?                                       # http(s):// (optional)
                         (?:(?:(?:(?:\w+\.)?youtube(?:-nocookie)?\.com/|
                            tube\.majestyc\.net/|
                            youtube\.googleapis\.com/)                        # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/)                               # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:(?:watch|movie)(?:_popup)?(?:\.php)?)?    # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?&)?                                    # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         ))
                         |youtu\.be/                                          # just youtu.be/xxxx
                         )
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]{11})                                      # here is it! the YouTube video ID
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    # Listed in order of quality
    _available_formats = ['38', '37', '46', '22', '45', '35', '44', '34', '18', '43', '6', '5', '36', '17', '13',
                          # Apple HTTP Live Streaming
                          '96', '95', '94', '93', '92', '132', '151',
                          # 3D
                          '85', '84', '102', '83', '101', '82', '100',
                          # Dash video
                          '138', '137', '248', '136', '247', '135', '246',
                          '245', '244', '134', '243', '133', '242', '160',
                          # Dash audio
                          '141', '172', '140', '171', '139',
                          ]
    _available_formats_prefer_free = ['38', '46', '37', '45', '22', '44', '35', '43', '34', '18', '6', '5', '36', '17', '13',
                                      # Apple HTTP Live Streaming
                                      '96', '95', '94', '93', '92', '132', '151',
                                      # 3D
                                      '85', '102', '84', '101', '83', '100', '82',
                                      # Dash video
                                      '138', '248', '137', '247', '136', '246', '245',
                                      '244', '135', '243', '134', '242', '133', '160',
                                      # Dash audio
                                      '172', '141', '171', '140', '139',
                                      ]
    _video_formats_map = {
        'flv': ['35', '34', '6', '5'],
        '3gp': ['36', '17', '13'],
        'mp4': ['38', '37', '22', '18'],
        'webm': ['46', '45', '44', '43'],
    }
    _video_extensions = {
        '13': '3gp',
        '17': '3gp',
        '18': 'mp4',
        '22': 'mp4',
        '36': '3gp',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',

        # 3d videos
        '82': 'mp4',
        '83': 'mp4',
        '84': 'mp4',
        '85': 'mp4',
        '100': 'webm',
        '101': 'webm',
        '102': 'webm',

        # Apple HTTP Live Streaming
        '92': 'mp4',
        '93': 'mp4',
        '94': 'mp4',
        '95': 'mp4',
        '96': 'mp4',
        '132': 'mp4',
        '151': 'mp4',

        # Dash mp4
        '133': 'mp4',
        '134': 'mp4',
        '135': 'mp4',
        '136': 'mp4',
        '137': 'mp4',
        '138': 'mp4',
        '139': 'mp4',
        '140': 'mp4',
        '141': 'mp4',
        '160': 'mp4',

        # Dash webm
        '171': 'webm',
        '172': 'webm',
        '242': 'webm',
        '243': 'webm',
        '244': 'webm',
        '245': 'webm',
        '246': 'webm',
        '247': 'webm',
        '248': 'webm',
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
        '36': '240x320',
        '37': '1080x1920',
        '38': '3072x4096',
        '43': '360x640',
        '44': '480x854',
        '45': '720x1280',
        '46': '1080x1920',
        '82': '360p',
        '83': '480p',
        '84': '720p',
        '85': '1080p',
        '92': '240p',
        '93': '360p',
        '94': '480p',
        '95': '720p',
        '96': '1080p',
        '100': '360p',
        '101': '480p',
        '102': '720p',
        '132': '240p',
        '151': '72p',
        '133': '240p',
        '134': '360p',
        '135': '480p',
        '136': '720p',
        '137': '1080p',
        '138': '>1080p',
        '139': '48k',
        '140': '128k',
        '141': '256k',
        '160': '192p',
        '171': '128k',
        '172': '256k',
        '242': '240p',
        '243': '360p',
        '244': '480p',
        '245': '480p',
        '246': '480p',
        '247': '720p',
        '248': '1080p',
    }
    _special_itags = {
        '82': '3D',
        '83': '3D',
        '84': '3D',
        '85': '3D',
        '100': '3D',
        '101': '3D',
        '102': '3D',
        '133': 'DASH Video',
        '134': 'DASH Video',
        '135': 'DASH Video',
        '136': 'DASH Video',
        '137': 'DASH Video',
        '138': 'DASH Video',
        '139': 'DASH Audio',
        '140': 'DASH Audio',
        '141': 'DASH Audio',
        '160': 'DASH Video',
        '171': 'DASH Audio',
        '172': 'DASH Audio',
        '242': 'DASH Video',
        '243': 'DASH Video',
        '244': 'DASH Video',
        '245': 'DASH Video',
        '246': 'DASH Video',
        '247': 'DASH Video',
        '248': 'DASH Video',
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
                u"description": u"md5:3e2666e0a55044490499ea45fe9037b7",
                u"uploader": u"Icona Pop",
                u"uploader_id": u"IconaPop"
            }
        },
        {
            u"url":  u"https://www.youtube.com/watch?v=07FYdnEawAQ",
            u"file":  u"07FYdnEawAQ.mp4",
            u"note": u"Test VEVO video with age protection (#956)",
            u"info_dict": {
                u"upload_date": u"20130703",
                u"title": u"Justin Timberlake - Tunnel Vision (Explicit)",
                u"description": u"md5:64249768eec3bc4276236606ea996373",
                u"uploader": u"justintimberlakeVEVO",
                u"uploader_id": u"justintimberlakeVEVO"
            }
        },
        {
            u'url': u'https://www.youtube.com/watch?v=TGi3HqYrWHE',
            u'file': u'TGi3HqYrWHE.mp4',
            u'note': u'm3u8 video',
            u'info_dict': {
                u'title': u'Triathlon - Men - London 2012 Olympic Games',
                u'description': u'- Men -  TR02 - Triathlon - 07 August 2012 - London 2012 Olympic Games',
                u'uploader': u'olympic',
                u'upload_date': u'20120807',
                u'uploader_id': u'olympic',
            },
            u'params': {
                u'skip_download': True,
            },
        },
    ]


    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        if YoutubePlaylistIE.suitable(url): return False
        return re.match(cls._VALID_URL, url, re.VERBOSE) is not None

    def report_video_webpage_download(self, video_id):
        """Report attempt to download video webpage."""
        self.to_screen(u'%s: Downloading video webpage' % video_id)

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen(u'%s: Downloading video info webpage' % video_id)

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

        if len(s) == 92:
            return s[25] + s[3:25] + s[0] + s[26:42] + s[79] + s[43:79] + s[91] + s[80:83]
        elif len(s) == 90:
            return s[25] + s[3:25] + s[2] + s[26:40] + s[77] + s[41:77] + s[89] + s[78:81]
        elif len(s) == 89:
            return s[84:78:-1] + s[87] + s[77:60:-1] + s[0] + s[59:3:-1]
        elif len(s) == 88:
            return s[7:28] + s[87] + s[29:45] + s[55] + s[46:55] + s[2] + s[56:87] + s[28]
        elif len(s) == 87:
            return s[6:27] + s[4] + s[28:39] + s[27] + s[40:59] + s[2] + s[60:]
        elif len(s) == 86:
            return s[5:34] + s[0] + s[35:38] + s[3] + s[39:45] + s[38] + s[46:53] + s[73] + s[54:73] + s[85] + s[74:85] + s[53]
        elif len(s) == 85:
            return s[3:11] + s[0] + s[12:55] + s[84] + s[56:84]
        elif len(s) == 84:
            return s[81:36:-1] + s[0] + s[35:2:-1]
        elif len(s) == 83:
            return s[81:64:-1] + s[82] + s[63:52:-1] + s[45] + s[51:45:-1] + s[1] + s[44:1:-1] + s[0]
        elif len(s) == 82:
            return s[80:73:-1] + s[81] + s[72:54:-1] + s[2] + s[53:43:-1] + s[0] + s[42:2:-1] + s[43] + s[1] + s[54]
        elif len(s) == 81:
            return s[56] + s[79:56:-1] + s[41] + s[55:41:-1] + s[80] + s[40:34:-1] + s[0] + s[33:29:-1] + s[34] + s[28:9:-1] + s[29] + s[8:0:-1] + s[9]
        elif len(s) == 80:
            return s[1:19] + s[0] + s[20:68] + s[19] + s[69:80]
        elif len(s) == 79:
            return s[54] + s[77:54:-1] + s[39] + s[53:39:-1] + s[78] + s[38:34:-1] + s[0] + s[33:29:-1] + s[34] + s[28:9:-1] + s[29] + s[8:0:-1] + s[9]

        else:
            raise ExtractorError(u'Unable to decrypt signature, key length %d not supported; retrying might work' % (len(s)))

    def _decrypt_signature_age_gate(self, s):
        # The videos with age protection use another player, so the algorithms
        # can be different.
        if len(s) == 86:
            return s[2:63] + s[82] + s[64:82] + s[63]
        else:
            # Fallback to the other algortihms
            return self._decrypt_signature(s)

    def _get_available_subtitles(self, video_id):
        try:
            sub_list = self._download_webpage(
                'http://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id,
                video_id, note=False)
        except ExtractorError as err:
            self._downloader.report_warning(u'unable to download video subtitles: %s' % compat_str(err))
            return {}
        lang_list = re.findall(r'name="([^"]*)"[^>]+lang_code="([\w\-]+)"', sub_list)

        sub_lang_list = {}
        for l in lang_list:
            lang = l[1]
            params = compat_urllib_parse.urlencode({
                'lang': lang,
                'v': video_id,
                'fmt': self._downloader.params.get('subtitlesformat'),
            })
            url = u'http://www.youtube.com/api/timedtext?' + params
            sub_lang_list[lang] = url
        if not sub_lang_list:
            self._downloader.report_warning(u'video doesn\'t have subtitles')
            return {}
        return sub_lang_list

    def _get_available_automatic_caption(self, video_id, webpage):
        """We need the webpage for getting the captions url, pass it as an
           argument to speed up the process."""
        sub_format = self._downloader.params.get('subtitlesformat')
        self.to_screen(u'%s: Looking for automatic captions' % video_id)
        mobj = re.search(r';ytplayer.config = ({.*?});', webpage)
        err_msg = u'Couldn\'t find automatic captions for %s' % video_id
        if mobj is None:
            self._downloader.report_warning(err_msg)
            return {}
        player_config = json.loads(mobj.group(1))
        try:
            args = player_config[u'args']
            caption_url = args[u'ttsurl']
            timestamp = args[u'timestamp']
            # We get the available subtitles
            list_params = compat_urllib_parse.urlencode({
                'type': 'list',
                'tlangs': 1,
                'asrs': 1,
            })
            list_url = caption_url + '&' + list_params
            list_page = self._download_webpage(list_url, video_id)
            caption_list = xml.etree.ElementTree.fromstring(list_page.encode('utf-8'))
            original_lang_node = caption_list.find('track')
            if original_lang_node.attrib.get('kind') != 'asr' :
                self._downloader.report_warning(u'Video doesn\'t have automatic captions')
                return {}
            original_lang = original_lang_node.attrib['lang_code']

            sub_lang_list = {}
            for lang_node in caption_list.findall('target'):
                sub_lang = lang_node.attrib['lang_code']
                params = compat_urllib_parse.urlencode({
                    'lang': original_lang,
                    'tlang': sub_lang,
                    'fmt': sub_format,
                    'ts': timestamp,
                    'kind': 'asr',
                })
                sub_lang_list[sub_lang] = caption_url + '&' + params
            return sub_lang_list
        # An extractor error can be raise by the download process if there are
        # no automatic captions but there are subtitles
        except (KeyError, ExtractorError):
            self._downloader.report_warning(err_msg)
            return {}

    def _print_formats(self, formats):
        print('Available formats:')
        for x in formats:
            print('%s\t:\t%s\t[%s]%s' %(x, self._video_extensions.get(x, 'flv'),
                                        self._video_dimensions.get(x, '???'),
                                        ' ('+self._special_itags[x]+')' if x in self._special_itags else ''))

    def _extract_id(self, url):
        mobj = re.match(self._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _get_video_url_list(self, url_map):
        """
        Transform a dictionary in the format {itag:url} to a list of (itag, url)
        with the requested formats.
        """
        req_format = self._downloader.params.get('format', None)
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
            # Format can be specified as itag or 'mp4' or 'flv' etc. We pick the highest quality
            # available in the specified format. For example,
            # if '1/2/3/4' is requested and '2' and '4' are available, we pick '2'.
            # if '1/mp4/3/4' is requested and '1' and '5' (is a mp4) are available, we pick '1'.
            # if '1/mp4/3/4' is requested and '4' and '5' (is a mp4) are available, we pick '5'.
            req_formats = req_format.split('/')
            video_url_list = None
            for rf in req_formats:
                if rf in url_map:
                    video_url_list = [(rf, url_map[rf])]
                    break
                if rf in self._video_formats_map:
                    for srf in self._video_formats_map[rf]:
                        if srf in url_map:
                            video_url_list = [(srf, url_map[srf])]
                            break
                    else:
                        continue
                    break
            if video_url_list is None:
                raise ExtractorError(u'requested format not available')
        return video_url_list

    def _extract_from_m3u8(self, manifest_url, video_id):
        url_map = {}
        def _get_urls(_manifest):
            lines = _manifest.split('\n')
            urls = filter(lambda l: l and not l.startswith('#'),
                            lines)
            return urls
        manifest = self._download_webpage(manifest_url, video_id, u'Downloading formats manifest')
        formats_urls = _get_urls(manifest)
        for format_url in formats_urls:
            itag = self._search_regex(r'itag/(\d+?)/', format_url, 'itag')
            url_map[itag] = format_url
        return url_map

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
        if re.search(r'player-age-gate-content">', video_webpage) is not None:
            self.report_age_confirmation()
            age_gate = True
            # We simulate the access to the video from www.youtube.com/v/{video_id}
            # this can be viewed without login into Youtube
            data = compat_urllib_parse.urlencode({'video_id': video_id,
                                                  'el': 'embedded',
                                                  'gl': 'US',
                                                  'hl': 'en',
                                                  'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                                                  'asv': 3,
                                                  'sts':'1588',
                                                  })
            video_info_url = 'https://www.youtube.com/get_video_info?' + data
            video_info_webpage = self._download_webpage(video_info_url, video_id,
                                    note=False,
                                    errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
        else:
            age_gate = False
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
        # We try first to get a high quality image:
        m_thumb = re.search(r'<span itemprop="thumbnail".*?href="(.*?)">',
                            video_webpage, re.DOTALL)
        if m_thumb is not None:
            video_thumbnail = m_thumb.group(1)
        elif 'thumbnail_url' not in video_info:
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
        video_subtitles = self.extract_subtitles(video_id, video_webpage)

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, video_webpage)
            return

        if 'length_seconds' not in video_info:
            self._downloader.report_warning(u'unable to extract video duration')
            video_duration = ''
        else:
            video_duration = compat_urllib_parse.unquote_plus(video_info['length_seconds'][0])

        # Decide which formats to download

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
            m_s = re.search(r'[&,]s=', args.get('adaptive_fmts', u''))
            if m_s is not None:
                if 'url_encoded_fmt_stream_map' in video_info:
                    video_info['url_encoded_fmt_stream_map'][0] += ',' + args['adaptive_fmts']
                else:
                    video_info['url_encoded_fmt_stream_map'] = [args['adaptive_fmts']]
            elif 'adaptive_fmts' in video_info:
                if 'url_encoded_fmt_stream_map' in video_info:
                    video_info['url_encoded_fmt_stream_map'][0] += ',' + video_info['adaptive_fmts'][0]
                else:
                    video_info['url_encoded_fmt_stream_map'] = video_info['adaptive_fmts']
        except ValueError:
            pass

        if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
            self.report_rtmp_download()
            video_url_list = [(None, video_info['conn'][0])]
        elif 'url_encoded_fmt_stream_map' in video_info and len(video_info['url_encoded_fmt_stream_map']) >= 1:
            if 'rtmpe%3Dyes' in video_info['url_encoded_fmt_stream_map'][0]:
                raise ExtractorError('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.', expected=True)
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
                            if age_gate:
                                player_version = self._search_regex(r'ad3-(.+?)\.swf',
                                    video_info['ad3_module'][0] if 'ad3_module' in video_info else 'NOT FOUND',
                                    'flash player', fatal=False)
                                player = 'flash player %s' % player_version
                            else:
                                player = u'html5 player %s' % self._search_regex(r'html5player-(.+?)\.js', video_webpage,
                                    'html5 player', fatal=False)
                            parts_sizes = u'.'.join(compat_str(len(part)) for part in s.split('.'))
                            self.to_screen(u'encrypted signature length %d (%s), itag %s, %s' %
                                (len(s), parts_sizes, url_data['itag'][0], player))
                        encrypted_sig = url_data['s'][0]
                        if age_gate:
                            signature = self._decrypt_signature_age_gate(encrypted_sig)
                        else:
                            signature = self._decrypt_signature(encrypted_sig)
                        url += '&signature=' + signature
                    if 'ratebypass' not in url:
                        url += '&ratebypass=yes'
                    url_map[url_data['itag'][0]] = url
            video_url_list = self._get_video_url_list(url_map)
            if not video_url_list:
                return
        elif video_info.get('hlsvp'):
            manifest_url = video_info['hlsvp'][0]
            url_map = self._extract_from_m3u8(manifest_url, video_id)
            video_url_list = self._get_video_url_list(url_map)
            if not video_url_list:
                return

        else:
            raise ExtractorError(u'no conn or url_encoded_fmt_stream_map information found in video info')

        results = []
        for format_param, video_real_url in video_url_list:
            # Extension
            video_extension = self._video_extensions.get(format_param, 'flv')

            video_format = '{0} - {1}{2}'.format(format_param if format_param else video_extension,
                                              self._video_dimensions.get(format_param, '???'),
                                              ' ('+self._special_itags[format_param]+')' if format_param in self._special_itags else '')

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
                        ((?:PL|EC|UU|FL)?[0-9A-Za-z-_]{10,})
                        .*
                     |
                        ((?:PL|EC|UU|FL)[0-9A-Za-z-_]{10,})
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
        videos = []

        for page_num in itertools.count(1):
            start_index = self._MAX_RESULTS * (page_num - 1) + 1
            if start_index >= 1000:
                self._downloader.report_warning(u'Max number of results reached')
                break
            url = self._TEMPLATE_URL % (playlist_id, self._MAX_RESULTS, start_index)
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
                if 'media$group' in entry and 'yt$videoid' in entry['media$group']:
                    videos.append((
                        index,
                        'https://www.youtube.com/watch?v=' + entry['media$group']['yt$videoid']['$t']
                    ))

        videos = [v[1] for v in sorted(videos)]

        url_results = [self.url_result(vurl, 'Youtube') for vurl in videos]
        return [self.playlist_result(url_results, playlist_id, playlist_title)]


class YoutubeChannelIE(InfoExtractor):
    IE_DESC = u'YouTube.com channels'
    _VALID_URL = r"^(?:https?://)?(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/([0-9A-Za-z_-]+)"
    _TEMPLATE_URL = 'http://www.youtube.com/channel/%s/videos?sort=da&flow=list&view=0&page=%s&gl=US&hl=en'
    _MORE_PAGES_INDICATOR = 'yt-uix-load-more'
    _MORE_PAGES_URL = 'http://www.youtube.com/c4_browse_ajax?action_load_more_videos=1&flow=list&paging=%s&view=0&sort=da&channel_id=%s'
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
            for pagenum in itertools.count(1):
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
        url_entries = [self.url_result(eurl, 'Youtube') for eurl in urls]
        return [self.playlist_result(url_entries, channel_id)]


class YoutubeUserIE(InfoExtractor):
    IE_DESC = u'YouTube.com user videos (URL or "ytuser" keyword)'
    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/(?:user/)?)|ytuser:)(?!feed/)([A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'http://gdata.youtube.com/feeds/api/users/%s'
    _GDATA_PAGE_SIZE = 50
    _GDATA_URL = 'http://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d&alt=json'
    IE_NAME = u'youtube:user'

    @classmethod
    def suitable(cls, url):
        # Don't return True if the url can be extracted with other youtube
        # extractor, the regex would is too permissive and it would match.
        other_ies = iter(klass for (name, klass) in globals().items() if name.endswith('IE') and klass is not cls)
        if any(ie.suitable(url) for ie in other_ies): return False
        else: return super(YoutubeUserIE, cls).suitable(url)

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

        for pagenum in itertools.count(0):
            start_index = pagenum * self._GDATA_PAGE_SIZE + 1

            gdata_url = self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index)
            page = self._download_webpage(gdata_url, username,
                                          u'Downloading video ids from %d to %d' % (start_index, start_index + self._GDATA_PAGE_SIZE))

            try:
                response = json.loads(page)
            except ValueError as err:
                raise ExtractorError(u'Invalid JSON in API response: ' + compat_str(err))

            # Extract video identifiers
            ids_in_page = []
            for entry in response['feed']['entry']:
                ids_in_page.append(entry['id']['$t'].split('/')[-1])
            video_ids.extend(ids_in_page)

            # A little optimization - if current page is not
            # "full", ie. does not contain PAGE_SIZE video ids then
            # we can assume that this page is the last one - there
            # are no more ids on further pages - no need to query
            # again.

            if len(ids_in_page) < self._GDATA_PAGE_SIZE:
                break

        urls = ['http://www.youtube.com/watch?v=%s' % video_id for video_id in video_ids]
        url_results = [self.url_result(rurl, 'Youtube') for rurl in urls]
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


class YoutubeFeedsInfoExtractor(YoutubeBaseInfoExtractor):
    """
    Base class for extractors that fetch info from
    http://www.youtube.com/feed_ajax
    Subclasses must define the _FEED_NAME and _PLAYLIST_TITLE properties.
    """
    _LOGIN_REQUIRED = True
    _PAGING_STEP = 30
    # use action_load_personal_feed instead of action_load_system_feed
    _PERSONAL_FEED = False

    @property
    def _FEED_TEMPLATE(self):
        action = 'action_load_system_feed'
        if self._PERSONAL_FEED:
            action = 'action_load_personal_feed'
        return 'http://www.youtube.com/feed_ajax?%s=1&feed_name=%s&paging=%%s' % (action, self._FEED_NAME)

    @property
    def IE_NAME(self):
        return u'youtube:%s' % self._FEED_NAME

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        feed_entries = []
        # The step argument is available only in 2.7 or higher
        for i in itertools.count(0):
            paging = i*self._PAGING_STEP
            info = self._download_webpage(self._FEED_TEMPLATE % paging,
                                          u'%s feed' % self._FEED_NAME,
                                          u'Downloading page %s' % i)
            info = json.loads(info)
            feed_html = info['feed_html']
            m_ids = re.finditer(r'"/watch\?v=(.*?)["&]', feed_html)
            ids = orderedSet(m.group(1) for m in m_ids)
            feed_entries.extend(self.url_result(id, 'Youtube') for id in ids)
            if info['paging'] is None:
                break
        return self.playlist_result(feed_entries, playlist_title=self._PLAYLIST_TITLE)

class YoutubeSubscriptionsIE(YoutubeFeedsInfoExtractor):
    IE_DESC = u'YouTube.com subscriptions feed, "ytsubs" keyword(requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/subscriptions|:ytsubs(?:criptions)?'
    _FEED_NAME = 'subscriptions'
    _PLAYLIST_TITLE = u'Youtube Subscriptions'

class YoutubeRecommendedIE(YoutubeFeedsInfoExtractor):
    IE_DESC = u'YouTube.com recommended videos, "ytrec" keyword (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/recommended|:ytrec(?:ommended)?'
    _FEED_NAME = 'recommended'
    _PLAYLIST_TITLE = u'Youtube Recommended videos'

class YoutubeWatchLaterIE(YoutubeFeedsInfoExtractor):
    IE_DESC = u'Youtube watch later list, "ytwatchlater" keyword (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/watch_later|:ytwatchlater'
    _FEED_NAME = 'watch_later'
    _PLAYLIST_TITLE = u'Youtube Watch Later'
    _PAGING_STEP = 100
    _PERSONAL_FEED = True

class YoutubeFavouritesIE(YoutubeBaseInfoExtractor):
    IE_NAME = u'youtube:favorites'
    IE_DESC = u'YouTube.com favourite videos, "ytfav" keyword (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/my_favorites|:ytfav(?:ou?rites)?'
    _LOGIN_REQUIRED = True

    def _real_extract(self, url):
        webpage = self._download_webpage('https://www.youtube.com/my_favorites', 'Youtube Favourites videos')
        playlist_id = self._search_regex(r'list=(.+?)["&]', webpage, u'favourites playlist id')
        return self.url_result(playlist_id, 'YoutubePlaylist')
