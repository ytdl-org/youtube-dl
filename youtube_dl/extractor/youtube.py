# coding: utf-8

from __future__ import unicode_literals


import itertools
import json
import os.path
import re
import time
import traceback

from .common import InfoExtractor, SearchInfoExtractor
from .subtitles import SubtitlesInfoExtractor
from ..jsinterp import JSInterpreter
from ..swfinterp import SWFInterpreter
from ..utils import (
    compat_chr,
    compat_parse_qs,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
    compat_str,

    clean_html,
    get_element_by_id,
    get_element_by_attribute,
    ExtractorError,
    int_or_none,
    OnDemandPagedList,
    unescapeHTML,
    unified_strdate,
    orderedSet,
    uppercase_escape,
)


class YoutubeBaseInfoExtractor(InfoExtractor):
    """Provide base functions for Youtube extractors"""
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _TWOFACTOR_URL = 'https://accounts.google.com/SecondFactor'
    _NETRC_MACHINE = 'youtube'
    # If True it will raise an error if no login info is provided
    _LOGIN_REQUIRED = False

    def _set_language(self):
        self._set_cookie(
            '.youtube.com', 'PREF', 'f1=50000000&hl=en',
            # YouTube sets the expire time to about two months
            expire_time=time.time() + 2 * 30 * 24 * 3600)

    def _login(self):
        """
        Attempt to log in to YouTube.
        True is returned if successful or skipped.
        False is returned if login failed.

        If _LOGIN_REQUIRED is set and no authentication was provided, an error is raised.
        """
        (username, password) = self._get_login_info()
        # No authentication to be performed
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return True

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note='Downloading login page',
            errnote='unable to fetch login page', fatal=False)
        if login_page is False:
            return

        galx = self._search_regex(r'(?s)<input.+?name="GALX".+?value="(.+?)"',
                                  login_page, 'Login GALX parameter')

        # Log in
        login_form_strs = {
            'continue': 'https://www.youtube.com/signin?action_handle_signin=true&feature=sign_in_button&hl=en_US&nomobiletemp=1',
            'Email': username,
            'GALX': galx,
            'Passwd': password,

            'PersistentCookie': 'yes',
            '_utf8': '霱',
            'bgresponse': 'js_disabled',
            'checkConnection': '',
            'checkedDomains': 'youtube',
            'dnConn': '',
            'pstMsg': '0',
            'rmShown': '1',
            'secTok': '',
            'signIn': 'Sign in',
            'timeStmp': '',
            'service': 'youtube',
            'uilel': '3',
            'hl': 'en_US',
        }

        # Convert to UTF-8 *before* urlencode because Python 2.x's urlencode
        # chokes on unicode
        login_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k, v in login_form_strs.items())
        login_data = compat_urllib_parse.urlencode(login_form).encode('ascii')

        req = compat_urllib_request.Request(self._LOGIN_URL, login_data)
        login_results = self._download_webpage(
            req, None,
            note='Logging in', errnote='unable to log in', fatal=False)
        if login_results is False:
            return False

        if re.search(r'id="errormsg_0_Passwd"', login_results) is not None:
            raise ExtractorError('Please use your account password and a two-factor code instead of an application-specific password.', expected=True)

        # Two-Factor
        # TODO add SMS and phone call support - these require making a request and then prompting the user

        if re.search(r'(?i)<form[^>]* id="gaia_secondfactorform"', login_results) is not None:
            tfa_code = self._get_tfa_info()

            if tfa_code is None:
                self._downloader.report_warning('Two-factor authentication required. Provide it with --twofactor <code>')
                self._downloader.report_warning('(Note that only TOTP (Google Authenticator App) codes work at this time.)')
                return False

            # Unlike the first login form, secTok and timeStmp are both required for the TFA form

            match = re.search(r'id="secTok"\n\s+value=\'(.+)\'/>', login_results, re.M | re.U)
            if match is None:
                self._downloader.report_warning('Failed to get secTok - did the page structure change?')
            secTok = match.group(1)
            match = re.search(r'id="timeStmp"\n\s+value=\'(.+)\'/>', login_results, re.M | re.U)
            if match is None:
                self._downloader.report_warning('Failed to get timeStmp - did the page structure change?')
            timeStmp = match.group(1)

            tfa_form_strs = {
                'continue': 'https://www.youtube.com/signin?action_handle_signin=true&feature=sign_in_button&hl=en_US&nomobiletemp=1',
                'smsToken': '',
                'smsUserPin': tfa_code,
                'smsVerifyPin': 'Verify',

                'PersistentCookie': 'yes',
                'checkConnection': '',
                'checkedDomains': 'youtube',
                'pstMsg': '1',
                'secTok': secTok,
                'timeStmp': timeStmp,
                'service': 'youtube',
                'hl': 'en_US',
            }
            tfa_form = dict((k.encode('utf-8'), v.encode('utf-8')) for k, v in tfa_form_strs.items())
            tfa_data = compat_urllib_parse.urlencode(tfa_form).encode('ascii')

            tfa_req = compat_urllib_request.Request(self._TWOFACTOR_URL, tfa_data)
            tfa_results = self._download_webpage(
                tfa_req, None,
                note='Submitting TFA code', errnote='unable to submit tfa', fatal=False)

            if tfa_results is False:
                return False

            if re.search(r'(?i)<form[^>]* id="gaia_secondfactorform"', tfa_results) is not None:
                self._downloader.report_warning('Two-factor code expired. Please try again, or use a one-use backup code instead.')
                return False
            if re.search(r'(?i)<form[^>]* id="gaia_loginform"', tfa_results) is not None:
                self._downloader.report_warning('unable to log in - did the page structure change?')
                return False
            if re.search(r'smsauth-interstitial-reviewsettings', tfa_results) is not None:
                self._downloader.report_warning('Your Google account has a security notice. Please log in on your web browser, resolve the notice, and try again.')
                return False

        if re.search(r'(?i)<form[^>]* id="gaia_loginform"', login_results) is not None:
            self._downloader.report_warning('unable to log in: bad username or password')
            return False
        return True

    def _real_initialize(self):
        if self._downloader is None:
            return
        self._set_language()
        if not self._login():
            return


class YoutubeIE(YoutubeBaseInfoExtractor, SubtitlesInfoExtractor):
    IE_DESC = 'YouTube.com'
    _VALID_URL = r"""(?x)^
                     (
                         (?:https?://|//)                                    # http(s):// or protocol-independent URL
                         (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie)?\.com/|
                            (?:www\.)?deturl\.com/www\.youtube\.com/|
                            (?:www\.)?pwnyoutube\.com/|
                            (?:www\.)?yourepeat\.com/|
                            tube\.majestyc\.net/|
                            youtube\.googleapis\.com/)                        # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/(?!videoseries))                # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
                                 (?:\?|\#!?)                                  # the params delimiter ? or # or #!
                                 (?:.*?&)?                                    # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         ))
                         |youtu\.be/                                          # just youtu.be/xxxx
                         |(?:www\.)?cleanvideosearch\.com/media/action/yt/watch\?videoId=
                         )
                     )?                                                       # all until now is optional -> you can pass the naked ID
                     ([0-9A-Za-z_-]{11})                                      # here is it! the YouTube video ID
                     (?!.*?&list=)                                            # combined list/video URLs are handled by the playlist IE
                     (?(1).+)?                                                # if we found the ID, everything can follow
                     $"""
    _NEXT_URL_RE = r'[\?&]next_url=([^&]+)'
    _formats = {
        '5': {'ext': 'flv', 'width': 400, 'height': 240},
        '6': {'ext': 'flv', 'width': 450, 'height': 270},
        '13': {'ext': '3gp'},
        '17': {'ext': '3gp', 'width': 176, 'height': 144},
        '18': {'ext': 'mp4', 'width': 640, 'height': 360},
        '22': {'ext': 'mp4', 'width': 1280, 'height': 720},
        '34': {'ext': 'flv', 'width': 640, 'height': 360},
        '35': {'ext': 'flv', 'width': 854, 'height': 480},
        '36': {'ext': '3gp', 'width': 320, 'height': 240},
        '37': {'ext': 'mp4', 'width': 1920, 'height': 1080},
        '38': {'ext': 'mp4', 'width': 4096, 'height': 3072},
        '43': {'ext': 'webm', 'width': 640, 'height': 360},
        '44': {'ext': 'webm', 'width': 854, 'height': 480},
        '45': {'ext': 'webm', 'width': 1280, 'height': 720},
        '46': {'ext': 'webm', 'width': 1920, 'height': 1080},


        # 3d videos
        '82': {'ext': 'mp4', 'height': 360, 'format_note': '3D', 'preference': -20},
        '83': {'ext': 'mp4', 'height': 480, 'format_note': '3D', 'preference': -20},
        '84': {'ext': 'mp4', 'height': 720, 'format_note': '3D', 'preference': -20},
        '85': {'ext': 'mp4', 'height': 1080, 'format_note': '3D', 'preference': -20},
        '100': {'ext': 'webm', 'height': 360, 'format_note': '3D', 'preference': -20},
        '101': {'ext': 'webm', 'height': 480, 'format_note': '3D', 'preference': -20},
        '102': {'ext': 'webm', 'height': 720, 'format_note': '3D', 'preference': -20},

        # Apple HTTP Live Streaming
        '92': {'ext': 'mp4', 'height': 240, 'format_note': 'HLS', 'preference': -10},
        '93': {'ext': 'mp4', 'height': 360, 'format_note': 'HLS', 'preference': -10},
        '94': {'ext': 'mp4', 'height': 480, 'format_note': 'HLS', 'preference': -10},
        '95': {'ext': 'mp4', 'height': 720, 'format_note': 'HLS', 'preference': -10},
        '96': {'ext': 'mp4', 'height': 1080, 'format_note': 'HLS', 'preference': -10},
        '132': {'ext': 'mp4', 'height': 240, 'format_note': 'HLS', 'preference': -10},
        '151': {'ext': 'mp4', 'height': 72, 'format_note': 'HLS', 'preference': -10},

        # DASH mp4 video
        '133': {'ext': 'mp4', 'height': 240, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '134': {'ext': 'mp4', 'height': 360, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '135': {'ext': 'mp4', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '136': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '137': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '138': {'ext': 'mp4', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '160': {'ext': 'mp4', 'height': 144, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '264': {'ext': 'mp4', 'height': 1440, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '298': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'h264'},
        '299': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'h264'},
        '266': {'ext': 'mp4', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'vcodec': 'h264'},

        # Dash mp4 audio
        '139': {'ext': 'm4a', 'format_note': 'DASH audio', 'vcodec': 'none', 'abr': 48, 'preference': -50},
        '140': {'ext': 'm4a', 'format_note': 'DASH audio', 'vcodec': 'none', 'abr': 128, 'preference': -50},
        '141': {'ext': 'm4a', 'format_note': 'DASH audio', 'vcodec': 'none', 'abr': 256, 'preference': -50},

        # Dash webm
        '167': {'ext': 'webm', 'height': 360, 'width': 640, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'preference': -40},
        '168': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'preference': -40},
        '169': {'ext': 'webm', 'height': 720, 'width': 1280, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'preference': -40},
        '170': {'ext': 'webm', 'height': 1080, 'width': 1920, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'preference': -40},
        '218': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'preference': -40},
        '219': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'preference': -40},
        '278': {'ext': 'webm', 'height': 144, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'container': 'webm', 'vcodec': 'VP9'},
        '242': {'ext': 'webm', 'height': 240, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '243': {'ext': 'webm', 'height': 360, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '244': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '245': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '246': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '247': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '248': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '271': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '272': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '302': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'VP9'},
        '303': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'VP9'},
        '313': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'vcodec': 'VP9'},

        # Dash webm audio
        '171': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH audio', 'abr': 128, 'preference': -50},
        '172': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH audio', 'abr': 256, 'preference': -50},

        # Dash webm audio with opus inside
        '249': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 50, 'preference': -50},
        '250': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 70, 'preference': -50},
        '251': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 160, 'preference': -50},

        # RTMP (unnamed)
        '_rtmp': {'protocol': 'rtmp'},
    }

    IE_NAME = 'youtube'
    _TESTS = [
        {
            'url': 'http://www.youtube.com/watch?v=BaW_jenozKc',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'phihag',
                'upload_date': '20121002',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'like_count': int,
                'dislike_count': int,
            }
        },
        {
            'url': 'http://www.youtube.com/watch?v=UxxajLWwzqY',
            'note': 'Test generic use_cipher_signature video (#897)',
            'info_dict': {
                'id': 'UxxajLWwzqY',
                'ext': 'mp4',
                'upload_date': '20120506',
                'title': 'Icona Pop - I Love It (feat. Charli XCX) [OFFICIAL VIDEO]',
                'description': 'md5:fea86fda2d5a5784273df5c7cc994d9f',
                'uploader': 'Icona Pop',
                'uploader_id': 'IconaPop',
            }
        },
        {
            'url': 'https://www.youtube.com/watch?v=07FYdnEawAQ',
            'note': 'Test VEVO video with age protection (#956)',
            'info_dict': {
                'id': '07FYdnEawAQ',
                'ext': 'mp4',
                'upload_date': '20130703',
                'title': 'Justin Timberlake - Tunnel Vision (Explicit)',
                'description': 'md5:64249768eec3bc4276236606ea996373',
                'uploader': 'justintimberlakeVEVO',
                'uploader_id': 'justintimberlakeVEVO',
            }
        },
        {
            'url': '//www.YouTube.com/watch?v=yZIXLfi8CZQ',
            'note': 'Embed-only video (#1746)',
            'info_dict': {
                'id': 'yZIXLfi8CZQ',
                'ext': 'mp4',
                'upload_date': '20120608',
                'title': 'Principal Sexually Assaults A Teacher - Episode 117 - 8th June 2012',
                'description': 'md5:09b78bd971f1e3e289601dfba15ca4f7',
                'uploader': 'SET India',
                'uploader_id': 'setindia'
            }
        },
        {
            'url': 'http://www.youtube.com/watch?v=a9LDPn-MO4I',
            'note': '256k DASH audio (format 141) via DASH manifest',
            'info_dict': {
                'id': 'a9LDPn-MO4I',
                'ext': 'm4a',
                'upload_date': '20121002',
                'uploader_id': '8KVIDEO',
                'description': '',
                'uploader': '8KVIDEO',
                'title': 'UHDTV TEST 8K VIDEO.mp4'
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141',
            },
        },
        # DASH manifest with encrypted signature
        {
            'url': 'https://www.youtube.com/watch?v=IB3lcPjvWLA',
            'info_dict': {
                'id': 'IB3lcPjvWLA',
                'ext': 'm4a',
                'title': 'Afrojack, Spree Wilson - The Spark ft. Spree Wilson',
                'description': 'md5:12e7067fa6735a77bdcbb58cb1187d2d',
                'uploader': 'AfrojackVEVO',
                'uploader_id': 'AfrojackVEVO',
                'upload_date': '20131011',
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '141',
            },
        },
        # Controversy video
        {
            'url': 'https://www.youtube.com/watch?v=T4XJQO3qol8',
            'info_dict': {
                'id': 'T4XJQO3qol8',
                'ext': 'mp4',
                'upload_date': '20100909',
                'uploader': 'The Amazing Atheist',
                'uploader_id': 'TheAmazingAtheist',
                'title': 'Burning Everyone\'s Koran',
                'description': 'SUBSCRIBE: http://www.youtube.com/saturninefilms\n\nEven Obama has taken a stand against freedom on this issue: http://www.huffingtonpost.com/2010/09/09/obama-gma-interview-quran_n_710282.html',
            }
        },
        # Normal age-gate video (No vevo, embed allowed)
        {
            'url': 'http://youtube.com/watch?v=HtVdAasjOgU',
            'info_dict': {
                'id': 'HtVdAasjOgU',
                'ext': 'mp4',
                'title': 'The Witcher 3: Wild Hunt - The Sword Of Destiny Trailer',
                'description': 'md5:eca57043abae25130f58f655ad9a7771',
                'uploader': 'The Witcher',
                'uploader_id': 'WitcherGame',
                'upload_date': '20140605',
            },
        },
        # video_info is None (https://github.com/rg3/youtube-dl/issues/4421)
        {
            'url': '__2ABJjxzNo',
            'info_dict': {
                'id': '__2ABJjxzNo',
                'ext': 'mp4',
                'upload_date': '20100430',
                'uploader_id': 'deadmau5',
                'description': 'md5:12c56784b8032162bb936a5f76d55360',
                'uploader': 'deadmau5',
                'title': 'Deadmau5 - Some Chords (HD)',
            },
            'expected_warnings': [
                'DASH manifest missing',
            ]
        }
    ]

    def __init__(self, *args, **kwargs):
        super(YoutubeIE, self).__init__(*args, **kwargs)
        self._player_cache = {}

    def report_video_info_webpage_download(self, video_id):
        """Report attempt to download video info webpage."""
        self.to_screen('%s: Downloading video info webpage' % video_id)

    def report_information_extraction(self, video_id):
        """Report attempt to extract video information."""
        self.to_screen('%s: Extracting video information' % video_id)

    def report_unavailable_format(self, video_id, format):
        """Report extracted video URL."""
        self.to_screen('%s: Format %s not available' % (video_id, format))

    def report_rtmp_download(self):
        """Indicate the download will use the RTMP protocol."""
        self.to_screen('RTMP download detected')

    def _signature_cache_id(self, example_sig):
        """ Return a string representation of a signature """
        return '.'.join(compat_str(len(part)) for part in example_sig.split('.'))

    def _extract_signature_function(self, video_id, player_url, example_sig):
        id_m = re.match(
            r'.*-(?P<id>[a-zA-Z0-9_-]+)(?:/watch_as3|/html5player)?\.(?P<ext>[a-z]+)$',
            player_url)
        if not id_m:
            raise ExtractorError('Cannot identify player %r' % player_url)
        player_type = id_m.group('ext')
        player_id = id_m.group('id')

        # Read from filesystem cache
        func_id = '%s_%s_%s' % (
            player_type, player_id, self._signature_cache_id(example_sig))
        assert os.path.basename(func_id) == func_id

        cache_spec = self._downloader.cache.load('youtube-sigfuncs', func_id)
        if cache_spec is not None:
            return lambda s: ''.join(s[i] for i in cache_spec)

        if player_type == 'js':
            code = self._download_webpage(
                player_url, video_id,
                note='Downloading %s player %s' % (player_type, player_id),
                errnote='Download of %s failed' % player_url)
            res = self._parse_sig_js(code)
        elif player_type == 'swf':
            urlh = self._request_webpage(
                player_url, video_id,
                note='Downloading %s player %s' % (player_type, player_id),
                errnote='Download of %s failed' % player_url)
            code = urlh.read()
            res = self._parse_sig_swf(code)
        else:
            assert False, 'Invalid player type %r' % player_type

        if cache_spec is None:
            test_string = ''.join(map(compat_chr, range(len(example_sig))))
            cache_res = res(test_string)
            cache_spec = [ord(c) for c in cache_res]

        self._downloader.cache.store('youtube-sigfuncs', func_id, cache_spec)
        return res

    def _print_sig_code(self, func, example_sig):
        def gen_sig_code(idxs):
            def _genslice(start, end, step):
                starts = '' if start == 0 else str(start)
                ends = (':%d' % (end + step)) if end + step >= 0 else ':'
                steps = '' if step == 1 else (':%d' % step)
                return 's[%s%s%s]' % (starts, ends, steps)

            step = None
            start = '(Never used)'  # Quelch pyflakes warnings - start will be
                                    # set as soon as step is set
            for i, prev in zip(idxs[1:], idxs[:-1]):
                if step is not None:
                    if i - prev == step:
                        continue
                    yield _genslice(start, prev, step)
                    step = None
                    continue
                if i - prev in [-1, 1]:
                    step = i - prev
                    start = prev
                    continue
                else:
                    yield 's[%d]' % prev
            if step is None:
                yield 's[%d]' % i
            else:
                yield _genslice(start, i, step)

        test_string = ''.join(map(compat_chr, range(len(example_sig))))
        cache_res = func(test_string)
        cache_spec = [ord(c) for c in cache_res]
        expr_code = ' + '.join(gen_sig_code(cache_spec))
        signature_id_tuple = '(%s)' % (
            ', '.join(compat_str(len(p)) for p in example_sig.split('.')))
        code = ('if tuple(len(p) for p in s.split(\'.\')) == %s:\n'
                '    return %s\n') % (signature_id_tuple, expr_code)
        self.to_screen('Extracted signature function:\n' + code)

    def _parse_sig_js(self, jscode):
        funcname = self._search_regex(
            r'\.sig\|\|([a-zA-Z0-9]+)\(', jscode,
            'Initial JS player signature function name')

        jsi = JSInterpreter(jscode)
        initial_function = jsi.extract_function(funcname)
        return lambda s: initial_function([s])

    def _parse_sig_swf(self, file_contents):
        swfi = SWFInterpreter(file_contents)
        TARGET_CLASSNAME = 'SignatureDecipher'
        searched_class = swfi.extract_class(TARGET_CLASSNAME)
        initial_function = swfi.extract_function(searched_class, 'decipher')
        return lambda s: initial_function([s])

    def _decrypt_signature(self, s, video_id, player_url, age_gate=False):
        """Turn the encrypted s field into a working signature"""

        if player_url is None:
            raise ExtractorError('Cannot decrypt signature without player_url')

        if player_url.startswith('//'):
            player_url = 'https:' + player_url
        try:
            player_id = (player_url, self._signature_cache_id(s))
            if player_id not in self._player_cache:
                func = self._extract_signature_function(
                    video_id, player_url, s
                )
                self._player_cache[player_id] = func
            func = self._player_cache[player_id]
            if self._downloader.params.get('youtube_print_sig_code'):
                self._print_sig_code(func, s)
            return func(s)
        except Exception as e:
            tb = traceback.format_exc()
            raise ExtractorError(
                'Signature extraction failed: ' + tb, cause=e)

    def _get_available_subtitles(self, video_id, webpage):
        try:
            sub_list = self._download_webpage(
                'https://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id,
                video_id, note=False)
        except ExtractorError as err:
            self._downloader.report_warning('unable to download video subtitles: %s' % compat_str(err))
            return {}
        lang_list = re.findall(r'name="([^"]*)"[^>]+lang_code="([\w\-]+)"', sub_list)

        sub_lang_list = {}
        for l in lang_list:
            lang = l[1]
            if lang in sub_lang_list:
                continue
            params = compat_urllib_parse.urlencode({
                'lang': lang,
                'v': video_id,
                'fmt': self._downloader.params.get('subtitlesformat', 'srt'),
                'name': unescapeHTML(l[0]).encode('utf-8'),
            })
            url = 'https://www.youtube.com/api/timedtext?' + params
            sub_lang_list[lang] = url
        if not sub_lang_list:
            self._downloader.report_warning('video doesn\'t have subtitles')
            return {}
        return sub_lang_list

    def _get_available_automatic_caption(self, video_id, webpage):
        """We need the webpage for getting the captions url, pass it as an
           argument to speed up the process."""
        sub_format = self._downloader.params.get('subtitlesformat', 'srt')
        self.to_screen('%s: Looking for automatic captions' % video_id)
        mobj = re.search(r';ytplayer.config = ({.*?});', webpage)
        err_msg = 'Couldn\'t find automatic captions for %s' % video_id
        if mobj is None:
            self._downloader.report_warning(err_msg)
            return {}
        player_config = json.loads(mobj.group(1))
        try:
            args = player_config['args']
            caption_url = args['ttsurl']
            timestamp = args['timestamp']
            # We get the available subtitles
            list_params = compat_urllib_parse.urlencode({
                'type': 'list',
                'tlangs': 1,
                'asrs': 1,
            })
            list_url = caption_url + '&' + list_params
            caption_list = self._download_xml(list_url, video_id)
            original_lang_node = caption_list.find('track')
            if original_lang_node is None or original_lang_node.attrib.get('kind') != 'asr':
                self._downloader.report_warning('Video doesn\'t have automatic captions')
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

    @classmethod
    def extract_id(cls, url):
        mobj = re.match(cls._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

    def _extract_from_m3u8(self, manifest_url, video_id):
        url_map = {}

        def _get_urls(_manifest):
            lines = _manifest.split('\n')
            urls = filter(lambda l: l and not l.startswith('#'),
                          lines)
            return urls
        manifest = self._download_webpage(manifest_url, video_id, 'Downloading formats manifest')
        formats_urls = _get_urls(manifest)
        for format_url in formats_urls:
            itag = self._search_regex(r'itag/(\d+?)/', format_url, 'itag')
            url_map[itag] = format_url
        return url_map

    def _extract_annotations(self, video_id):
        url = 'https://www.youtube.com/annotations_invideo?features=1&legacy=1&video_id=%s' % video_id
        return self._download_webpage(url, video_id, note='Searching for annotations.', errnote='Unable to download video annotations.')

    def _parse_dash_manifest(
            self, video_id, dash_manifest_url, player_url, age_gate):
        def decrypt_sig(mobj):
            s = mobj.group(1)
            dec_s = self._decrypt_signature(s, video_id, player_url, age_gate)
            return '/signature/%s' % dec_s
        dash_manifest_url = re.sub(r'/s/([\w\.]+)', decrypt_sig, dash_manifest_url)
        dash_doc = self._download_xml(
            dash_manifest_url, video_id,
            note='Downloading DASH manifest',
            errnote='Could not download DASH manifest')

        formats = []
        for r in dash_doc.findall('.//{urn:mpeg:DASH:schema:MPD:2011}Representation'):
            url_el = r.find('{urn:mpeg:DASH:schema:MPD:2011}BaseURL')
            if url_el is None:
                continue
            format_id = r.attrib['id']
            video_url = url_el.text
            filesize = int_or_none(url_el.attrib.get('{http://youtube.com/yt/2012/10/10}contentLength'))
            f = {
                'format_id': format_id,
                'url': video_url,
                'width': int_or_none(r.attrib.get('width')),
                'tbr': int_or_none(r.attrib.get('bandwidth'), 1000),
                'asr': int_or_none(r.attrib.get('audioSamplingRate')),
                'filesize': filesize,
                'fps': int_or_none(r.attrib.get('frameRate')),
            }
            try:
                existing_format = next(
                    fo for fo in formats
                    if fo['format_id'] == format_id)
            except StopIteration:
                f.update(self._formats.get(format_id, {}))
                formats.append(f)
            else:
                existing_format.update(f)
        return formats

    def _real_extract(self, url):
        proto = (
            'http' if self._downloader.params.get('prefer_insecure', False)
            else 'https')

        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = proto + '://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self.extract_id(url)

        # Get video webpage
        url = proto + '://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1&bpctr=9999999999' % video_id
        video_webpage = self._download_webpage(url, video_id)

        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(https?:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
        if mobj is not None:
            player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
        else:
            player_url = None

        # Get video info
        if re.search(r'player-age-gate-content">', video_webpage) is not None:
            age_gate = True
            # We simulate the access to the video from www.youtube.com/v/{video_id}
            # this can be viewed without login into Youtube
            data = compat_urllib_parse.urlencode({
                'video_id': video_id,
                'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                'sts': self._search_regex(
                    r'"sts"\s*:\s*(\d+)', video_webpage, 'sts', default=''),
            })
            video_info_url = proto + '://www.youtube.com/get_video_info?' + data
            video_info_webpage = self._download_webpage(
                video_info_url, video_id,
                note='Refetching age-gated info webpage',
                errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
        else:
            age_gate = False
            try:
                # Try looking directly into the video webpage
                mobj = re.search(r';ytplayer\.config\s*=\s*({.*?});', video_webpage)
                if not mobj:
                    raise ValueError('Could not find ytplayer.config')  # caught below
                json_code = uppercase_escape(mobj.group(1))
                ytplayer_config = json.loads(json_code)
                args = ytplayer_config['args']
                # Convert to the same format returned by compat_parse_qs
                video_info = dict((k, [v]) for k, v in args.items())
                if 'url_encoded_fmt_stream_map' not in args:
                    raise ValueError('No stream_map present')  # caught below
            except ValueError:
                # We fallback to the get_video_info pages (used by the embed page)
                self.report_video_info_webpage_download(video_id)
                for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
                    video_info_url = (
                        '%s://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                        % (proto, video_id, el_type))
                    video_info_webpage = self._download_webpage(
                        video_info_url,
                        video_id, note=False,
                        errnote='unable to download video info webpage')
                    video_info = compat_parse_qs(video_info_webpage)
                    if 'token' in video_info:
                        break
        if 'token' not in video_info:
            if 'reason' in video_info:
                raise ExtractorError(
                    'YouTube said: %s' % video_info['reason'][0],
                    expected=True, video_id=video_id)
            else:
                raise ExtractorError(
                    '"token" parameter not in video info for unknown reason',
                    video_id=video_id)

        if 'view_count' in video_info:
            view_count = int(video_info['view_count'][0])
        else:
            view_count = None

        # Check for "rental" videos
        if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
            raise ExtractorError('"rental" videos not supported')

        # Start extracting information
        self.report_information_extraction(video_id)

        # uploader
        if 'author' not in video_info:
            raise ExtractorError('Unable to extract uploader name')
        video_uploader = compat_urllib_parse.unquote_plus(video_info['author'][0])

        # uploader_id
        video_uploader_id = None
        mobj = re.search(r'<link itemprop="url" href="http://www.youtube.com/(?:user|channel)/([^"]+)">', video_webpage)
        if mobj is not None:
            video_uploader_id = mobj.group(1)
        else:
            self._downloader.report_warning('unable to extract uploader nickname')

        # title
        if 'title' in video_info:
            video_title = video_info['title'][0]
        else:
            self._downloader.report_warning('Unable to extract video title')
            video_title = '_'

        # thumbnail image
        # We try first to get a high quality image:
        m_thumb = re.search(r'<span itemprop="thumbnail".*?href="(.*?)">',
                            video_webpage, re.DOTALL)
        if m_thumb is not None:
            video_thumbnail = m_thumb.group(1)
        elif 'thumbnail_url' not in video_info:
            self._downloader.report_warning('unable to extract video thumbnail')
            video_thumbnail = None
        else:   # don't panic if we can't find it
            video_thumbnail = compat_urllib_parse.unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = None
        mobj = re.search(r'(?s)id="eow-date.*?>(.*?)</span>', video_webpage)
        if mobj is None:
            mobj = re.search(
                r'(?s)id="watch-uploader-info".*?>.*?(?:Published|Uploaded|Streamed live) on (.*?)</strong>',
                video_webpage)
        if mobj is not None:
            upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
            upload_date = unified_strdate(upload_date)

        m_cat_container = self._search_regex(
            r'(?s)<h4[^>]*>\s*Category\s*</h4>\s*<ul[^>]*>(.*?)</ul>',
            video_webpage, 'categories', fatal=False)
        if m_cat_container:
            category = self._html_search_regex(
                r'(?s)<a[^<]+>(.*?)</a>', m_cat_container, 'category',
                default=None)
            video_categories = None if category is None else [category]
        else:
            video_categories = None

        # description
        video_description = get_element_by_id("eow-description", video_webpage)
        if video_description:
            video_description = re.sub(r'''(?x)
                <a\s+
                    (?:[a-zA-Z-]+="[^"]+"\s+)*?
                    title="([^"]+)"\s+
                    (?:[a-zA-Z-]+="[^"]+"\s+)*?
                    class="yt-uix-redirect-link"\s*>
                [^<]+
                </a>
            ''', r'\1', video_description)
            video_description = clean_html(video_description)
        else:
            fd_mobj = re.search(r'<meta name="description" content="([^"]+)"', video_webpage)
            if fd_mobj:
                video_description = unescapeHTML(fd_mobj.group(1))
            else:
                video_description = ''

        def _extract_count(count_name):
            count = self._search_regex(
                r'id="watch-%s"[^>]*>.*?([\d,]+)\s*</span>' % re.escape(count_name),
                video_webpage, count_name, default=None)
            if count is not None:
                return int(count.replace(',', ''))
            return None
        like_count = _extract_count('like')
        dislike_count = _extract_count('dislike')

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, video_webpage)

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, video_webpage)
            return

        if 'length_seconds' not in video_info:
            self._downloader.report_warning('unable to extract video duration')
            video_duration = None
        else:
            video_duration = int(compat_urllib_parse.unquote_plus(video_info['length_seconds'][0]))

        # annotations
        video_annotations = None
        if self._downloader.params.get('writeannotations', False):
            video_annotations = self._extract_annotations(video_id)

        def _map_to_format_list(urlmap):
            formats = []
            for itag, video_real_url in urlmap.items():
                dct = {
                    'format_id': itag,
                    'url': video_real_url,
                    'player_url': player_url,
                }
                if itag in self._formats:
                    dct.update(self._formats[itag])
                formats.append(dct)
            return formats

        if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
            self.report_rtmp_download()
            formats = [{
                'format_id': '_rtmp',
                'protocol': 'rtmp',
                'url': video_info['conn'][0],
                'player_url': player_url,
            }]
        elif len(video_info.get('url_encoded_fmt_stream_map', [])) >= 1 or len(video_info.get('adaptive_fmts', [])) >= 1:
            encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + video_info.get('adaptive_fmts', [''])[0]
            if 'rtmpe%3Dyes' in encoded_url_map:
                raise ExtractorError('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.', expected=True)
            url_map = {}
            for url_data_str in encoded_url_map.split(','):
                url_data = compat_parse_qs(url_data_str)
                if 'itag' not in url_data or 'url' not in url_data:
                    continue
                format_id = url_data['itag'][0]
                url = url_data['url'][0]

                if 'sig' in url_data:
                    url += '&signature=' + url_data['sig'][0]
                elif 's' in url_data:
                    encrypted_sig = url_data['s'][0]

                    if not age_gate:
                        jsplayer_url_json = self._search_regex(
                            r'"assets":.+?"js":\s*("[^"]+")',
                            video_webpage, 'JS player URL')
                        player_url = json.loads(jsplayer_url_json)
                    if player_url is None:
                        player_url_json = self._search_regex(
                            r'ytplayer\.config.*?"url"\s*:\s*("[^"]+")',
                            video_webpage, 'age gate player URL')
                        player_url = json.loads(player_url_json)

                    if self._downloader.params.get('verbose'):
                        if player_url is None:
                            player_version = 'unknown'
                            player_desc = 'unknown'
                        else:
                            if player_url.endswith('swf'):
                                player_version = self._search_regex(
                                    r'-(.+?)(?:/watch_as3)?\.swf$', player_url,
                                    'flash player', fatal=False)
                                player_desc = 'flash player %s' % player_version
                            else:
                                player_version = self._search_regex(
                                    r'html5player-([^/]+?)(?:/html5player)?\.js',
                                    player_url,
                                    'html5 player', fatal=False)
                                player_desc = 'html5 player %s' % player_version

                        parts_sizes = self._signature_cache_id(encrypted_sig)
                        self.to_screen('{%s} signature length %s, %s' %
                                       (format_id, parts_sizes, player_desc))

                    signature = self._decrypt_signature(
                        encrypted_sig, video_id, player_url, age_gate)
                    url += '&signature=' + signature
                if 'ratebypass' not in url:
                    url += '&ratebypass=yes'
                url_map[format_id] = url
            formats = _map_to_format_list(url_map)
        elif video_info.get('hlsvp'):
            manifest_url = video_info['hlsvp'][0]
            url_map = self._extract_from_m3u8(manifest_url, video_id)
            formats = _map_to_format_list(url_map)
        else:
            raise ExtractorError('no conn, hlsvp or url_encoded_fmt_stream_map information found in video info')

        # Look for the DASH manifest
        if self._downloader.params.get('youtube_include_dash_manifest', True):
            dash_mpd = video_info.get('dashmpd')
            if not dash_mpd:
                self.report_warning('%s: DASH manifest missing' % video_id)
            else:
                dash_manifest_url = dash_mpd[0]
                try:
                    dash_formats = self._parse_dash_manifest(
                        video_id, dash_manifest_url, player_url, age_gate)
                except (ExtractorError, KeyError) as e:
                    self.report_warning(
                        'Skipping DASH manifest: %r' % e, video_id)
                else:
                    formats.extend(dash_formats)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'uploader': video_uploader,
            'uploader_id': video_uploader_id,
            'upload_date': upload_date,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'description': video_description,
            'categories': video_categories,
            'subtitles': video_subtitles,
            'duration': video_duration,
            'age_limit': 18 if age_gate else 0,
            'annotations': video_annotations,
            'webpage_url': proto + '://www.youtube.com/watch?v=%s' % video_id,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats': formats,
        }


class YoutubePlaylistIE(YoutubeBaseInfoExtractor):
    IE_DESC = 'YouTube.com playlists'
    _VALID_URL = r"""(?x)(?:
                        (?:https?://)?
                        (?:\w+\.)?
                        youtube\.com/
                        (?:
                           (?:course|view_play_list|my_playlists|artist|playlist|watch|embed/videoseries)
                           \? (?:.*?&)*? (?:p|a|list)=
                        |  p/
                        )
                        (
                            (?:PL|LL|EC|UU|FL|RD)?[0-9A-Za-z-_]{10,}
                            # Top tracks, they can also include dots
                            |(?:MC)[\w\.]*
                        )
                        .*
                     |
                        ((?:PL|LL|EC|UU|FL|RD)[0-9A-Za-z-_]{10,})
                     )"""
    _TEMPLATE_URL = 'https://www.youtube.com/playlist?list=%s'
    _MORE_PAGES_INDICATOR = r'data-link-type="next"'
    _VIDEO_RE = r'href="\s*/watch\?v=(?P<id>[0-9A-Za-z_-]{11})&amp;[^"]*?index=(?P<index>\d+)'
    IE_NAME = 'youtube:playlist'
    _TESTS = [{
        'url': 'https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re',
        'info_dict': {
            'title': 'ytdl test PL',
            'id': 'PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re',
        },
        'playlist_count': 3,
    }, {
        'url': 'https://www.youtube.com/playlist?list=PLtPgu7CB4gbZDA7i_euNxn75ISqxwZPYx',
        'info_dict': {
            'title': 'YDL_Empty_List',
        },
        'playlist_count': 0,
    }, {
        'note': 'Playlist with deleted videos (#651). As a bonus, the video #51 is also twice in this list.',
        'url': 'https://www.youtube.com/playlist?list=PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC',
        'info_dict': {
            'title': '29C3: Not my department',
        },
        'playlist_count': 95,
    }, {
        'note': 'issue #673',
        'url': 'PLBB231211A4F62143',
        'info_dict': {
            'title': '[OLD]Team Fortress 2 (Class-based LP)',
        },
        'playlist_mincount': 26,
    }, {
        'note': 'Large playlist',
        'url': 'https://www.youtube.com/playlist?list=UUBABnxM4Ar9ten8Mdjj1j0Q',
        'info_dict': {
            'title': 'Uploads from Cauchemar',
        },
        'playlist_mincount': 799,
    }, {
        'url': 'PLtPgu7CB4gbY9oDN3drwC3cMbJggS7dKl',
        'info_dict': {
            'title': 'YDL_safe_search',
        },
        'playlist_count': 2,
    }, {
        'note': 'embedded',
        'url': 'http://www.youtube.com/embed/videoseries?list=PL6IaIsEjSbf96XFRuNccS_RuEXwNdsoEu',
        'playlist_count': 4,
        'info_dict': {
            'title': 'JODA15',
        }
    }, {
        'note': 'Embedded SWF player',
        'url': 'http://www.youtube.com/p/YN5VISEtHet5D4NEvfTd0zcgFk84NqFZ?hl=en_US&fs=1&rel=0',
        'playlist_count': 4,
        'info_dict': {
            'title': 'JODA7',
        }
    }]

    def _real_initialize(self):
        self._login()

    def _ids_to_results(self, ids):
        return [
            self.url_result(vid_id, 'Youtube', video_id=vid_id)
            for vid_id in ids]

    def _extract_mix(self, playlist_id):
        # The mixes are generated from a a single video
        # the id of the playlist is just 'RD' + video_id
        url = 'https://youtube.com/watch?v=%s&list=%s' % (playlist_id[-11:], playlist_id)
        webpage = self._download_webpage(
            url, playlist_id, 'Downloading Youtube mix')
        search_title = lambda class_name: get_element_by_attribute('class', class_name, webpage)
        title_span = (
            search_title('playlist-title') or
            search_title('title long-title') or
            search_title('title'))
        title = clean_html(title_span)
        ids = orderedSet(re.findall(
            r'''(?xs)data-video-username=".*?".*?
                       href="/watch\?v=([0-9A-Za-z_-]{11})&amp;[^"]*?list=%s''' % re.escape(playlist_id),
            webpage))
        url_results = self._ids_to_results(ids)

        return self.playlist_result(url_results, playlist_id, title)

    def _real_extract(self, url):
        # Extract playlist id
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError('Invalid URL: %s' % url)
        playlist_id = mobj.group(1) or mobj.group(2)

        # Check if it's a video-specific URL
        query_dict = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        if 'v' in query_dict:
            video_id = query_dict['v'][0]
            if self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)
                return self.url_result(video_id, 'Youtube', video_id=video_id)
            else:
                self.to_screen('Downloading playlist %s - add --no-playlist to just download video %s' % (playlist_id, video_id))

        if playlist_id.startswith('RD'):
            # Mixes require a custom extraction process
            return self._extract_mix(playlist_id)
        if playlist_id.startswith('TL'):
            raise ExtractorError('For downloading YouTube.com top lists, use '
                                 'the "yttoplist" keyword, for example "youtube-dl \'yttoplist:music:Top Tracks\'"', expected=True)

        url = self._TEMPLATE_URL % playlist_id
        page = self._download_webpage(url, playlist_id)
        more_widget_html = content_html = page

        # Check if the playlist exists or is private
        if re.search(r'<div class="yt-alert-message">[^<]*?(The|This) playlist (does not exist|is private)[^<]*?</div>', page) is not None:
            raise ExtractorError(
                'The playlist doesn\'t exist or is private, use --username or '
                '--netrc to access it.',
                expected=True)

        # Extract the video ids from the playlist pages
        ids = []

        for page_num in itertools.count(1):
            matches = re.finditer(self._VIDEO_RE, content_html)
            # We remove the duplicates and the link with index 0
            # (it's not the first video of the playlist)
            new_ids = orderedSet(m.group('id') for m in matches if m.group('index') != '0')
            ids.extend(new_ids)

            mobj = re.search(r'data-uix-load-more-href="/?(?P<more>[^"]+)"', more_widget_html)
            if not mobj:
                break

            more = self._download_json(
                'https://youtube.com/%s' % mobj.group('more'), playlist_id,
                'Downloading page #%s' % page_num,
                transform_source=uppercase_escape)
            content_html = more['content_html']
            more_widget_html = more['load_more_widget_html']

        playlist_title = self._html_search_regex(
            r'(?s)<h1 class="pl-header-title[^"]*">\s*(.*?)\s*</h1>',
            page, 'title')

        url_results = self._ids_to_results(ids)
        return self.playlist_result(url_results, playlist_id, playlist_title)


class YoutubeTopListIE(YoutubePlaylistIE):
    IE_NAME = 'youtube:toplist'
    IE_DESC = ('YouTube.com top lists, "yttoplist:{channel}:{list title}"'
               ' (Example: "yttoplist:music:Top Tracks")')
    _VALID_URL = r'yttoplist:(?P<chann>.*?):(?P<title>.*?)$'
    _TESTS = [{
        'url': 'yttoplist:music:Trending',
        'playlist_mincount': 5,
        'skip': 'Only works for logged-in users',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel = mobj.group('chann')
        title = mobj.group('title')
        query = compat_urllib_parse.urlencode({'title': title})
        channel_page = self._download_webpage(
            'https://www.youtube.com/%s' % channel, title)
        link = self._html_search_regex(
            r'''(?x)
                <a\s+href="([^"]+)".*?>\s*
                <span\s+class="branded-page-module-title-text">\s*
                <span[^>]*>.*?%s.*?</span>''' % re.escape(query),
            channel_page, 'list')
        url = compat_urlparse.urljoin('https://www.youtube.com/', link)

        video_re = r'data-index="\d+".*?data-video-id="([0-9A-Za-z_-]{11})"'
        ids = []
        # sometimes the webpage doesn't contain the videos
        # retry until we get them
        for i in itertools.count(0):
            msg = 'Downloading Youtube mix'
            if i > 0:
                msg += ', retry #%d' % i

            webpage = self._download_webpage(url, title, msg)
            ids = orderedSet(re.findall(video_re, webpage))
            if ids:
                break
        url_results = self._ids_to_results(ids)
        return self.playlist_result(url_results, playlist_title=title)


class YoutubeChannelIE(InfoExtractor):
    IE_DESC = 'YouTube.com channels'
    _VALID_URL = r'https?://(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/(?P<id>[0-9A-Za-z_-]+)'
    _MORE_PAGES_INDICATOR = 'yt-uix-load-more'
    _MORE_PAGES_URL = 'https://www.youtube.com/c4_browse_ajax?action_load_more_videos=1&flow=list&paging=%s&view=0&sort=da&channel_id=%s'
    IE_NAME = 'youtube:channel'
    _TESTS = [{
        'note': 'paginated channel',
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w',
        'playlist_mincount': 91,
    }]

    def extract_videos_from_page(self, page):
        ids_in_page = []
        for mobj in re.finditer(r'href="/watch\?v=([0-9A-Za-z_-]+)&?', page):
            if mobj.group(1) not in ids_in_page:
                ids_in_page.append(mobj.group(1))
        return ids_in_page

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        video_ids = []
        url = 'https://www.youtube.com/channel/%s/videos' % channel_id
        channel_page = self._download_webpage(url, channel_id)
        autogenerated = re.search(r'''(?x)
                class="[^"]*?(?:
                    channel-header-autogenerated-label|
                    yt-channel-title-autogenerated
                )[^"]*"''', channel_page) is not None

        if autogenerated:
            # The videos are contained in a single page
            # the ajax pages can't be used, they are empty
            video_ids = self.extract_videos_from_page(channel_page)
            entries = [
                self.url_result(video_id, 'Youtube', video_id=video_id)
                for video_id in video_ids]
            return self.playlist_result(entries, channel_id)

        def _entries():
            for pagenum in itertools.count(1):
                url = self._MORE_PAGES_URL % (pagenum, channel_id)
                page = self._download_json(
                    url, channel_id, note='Downloading page #%s' % pagenum,
                    transform_source=uppercase_escape)

                ids_in_page = self.extract_videos_from_page(page['content_html'])
                for video_id in ids_in_page:
                    yield self.url_result(
                        video_id, 'Youtube', video_id=video_id)

                if self._MORE_PAGES_INDICATOR not in page['load_more_widget_html']:
                    break

        return self.playlist_result(_entries(), channel_id)


class YoutubeUserIE(InfoExtractor):
    IE_DESC = 'YouTube.com user videos (URL or "ytuser" keyword)'
    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/(?:user/)?(?!(?:attribution_link|watch|results)(?:$|[^a-z_A-Z0-9-])))|ytuser:)(?!feed/)(?P<id>[A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'https://gdata.youtube.com/feeds/api/users/%s'
    _GDATA_PAGE_SIZE = 50
    _GDATA_URL = 'https://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d&alt=json'
    IE_NAME = 'youtube:user'

    _TESTS = [{
        'url': 'https://www.youtube.com/user/TheLinuxFoundation',
        'playlist_mincount': 320,
        'info_dict': {
            'title': 'TheLinuxFoundation',
        }
    }, {
        'url': 'ytuser:phihag',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        # Don't return True if the url can be extracted with other youtube
        # extractor, the regex would is too permissive and it would match.
        other_ies = iter(klass for (name, klass) in globals().items() if name.endswith('IE') and klass is not cls)
        if any(ie.suitable(url) for ie in other_ies):
            return False
        else:
            return super(YoutubeUserIE, cls).suitable(url)

    def _real_extract(self, url):
        username = self._match_id(url)

        # Download video ids using YouTube Data API. Result size per
        # query is limited (currently to 50 videos) so we need to query
        # page by page until there are no video ids - it means we got
        # all of them.

        def download_page(pagenum):
            start_index = pagenum * self._GDATA_PAGE_SIZE + 1

            gdata_url = self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index)
            page = self._download_webpage(
                gdata_url, username,
                'Downloading video ids from %d to %d' % (
                    start_index, start_index + self._GDATA_PAGE_SIZE))

            try:
                response = json.loads(page)
            except ValueError as err:
                raise ExtractorError('Invalid JSON in API response: ' + compat_str(err))
            if 'entry' not in response['feed']:
                return

            # Extract video identifiers
            entries = response['feed']['entry']
            for entry in entries:
                title = entry['title']['$t']
                video_id = entry['id']['$t'].split('/')[-1]
                yield {
                    '_type': 'url',
                    'url': video_id,
                    'ie_key': 'Youtube',
                    'id': video_id,
                    'title': title,
                }
        url_results = OnDemandPagedList(download_page, self._GDATA_PAGE_SIZE)

        return self.playlist_result(url_results, playlist_title=username)


class YoutubeSearchIE(SearchInfoExtractor):
    IE_DESC = 'YouTube.com searches'
    _API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc'
    _MAX_RESULTS = 1000
    IE_NAME = 'youtube:search'
    _SEARCH_KEY = 'ytsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        video_ids = []
        pagenum = 0
        limit = n
        PAGE_SIZE = 50

        while (PAGE_SIZE * pagenum) < limit:
            result_url = self._API_URL % (
                compat_urllib_parse.quote_plus(query.encode('utf-8')),
                (PAGE_SIZE * pagenum) + 1)
            data_json = self._download_webpage(
                result_url, video_id='query "%s"' % query,
                note='Downloading page %s' % (pagenum + 1),
                errnote='Unable to download API page')
            data = json.loads(data_json)
            api_response = data['data']

            if 'items' not in api_response:
                raise ExtractorError(
                    '[youtube] No video results', expected=True)

            new_ids = list(video['id'] for video in api_response['items'])
            video_ids += new_ids

            limit = min(n, api_response['totalItems'])
            pagenum += 1

        if len(video_ids) > n:
            video_ids = video_ids[:n]
        videos = [self.url_result(video_id, 'Youtube', video_id=video_id)
                  for video_id in video_ids]
        return self.playlist_result(videos, query)


class YoutubeSearchDateIE(YoutubeSearchIE):
    IE_NAME = YoutubeSearchIE.IE_NAME + ':date'
    _API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc&orderby=published'
    _SEARCH_KEY = 'ytsearchdate'
    IE_DESC = 'YouTube.com searches, newest videos first'


class YoutubeSearchURLIE(InfoExtractor):
    IE_DESC = 'YouTube.com search URLs'
    IE_NAME = 'youtube:search_url'
    _VALID_URL = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?search_query=(?P<query>[^&]+)(?:[&]|$)'
    _TESTS = [{
        'url': 'https://www.youtube.com/results?baz=bar&search_query=youtube-dl+test+video&filters=video&lclk=video',
        'playlist_mincount': 5,
        'info_dict': {
            'title': 'youtube-dl test video',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query = compat_urllib_parse.unquote_plus(mobj.group('query'))

        webpage = self._download_webpage(url, query)
        result_code = self._search_regex(
            r'(?s)<ol class="item-section"(.*?)</ol>', webpage, 'result HTML')

        part_codes = re.findall(
            r'(?s)<h3 class="yt-lockup-title">(.*?)</h3>', result_code)
        entries = []
        for part_code in part_codes:
            part_title = self._html_search_regex(
                [r'(?s)title="([^"]+)"', r'>([^<]+)</a>'], part_code, 'item title', fatal=False)
            part_url_snippet = self._html_search_regex(
                r'(?s)href="([^"]+)"', part_code, 'item URL')
            part_url = compat_urlparse.urljoin(
                'https://www.youtube.com/', part_url_snippet)
            entries.append({
                '_type': 'url',
                'url': part_url,
                'title': part_title,
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'title': query,
        }


class YoutubeShowIE(InfoExtractor):
    IE_DESC = 'YouTube.com (multi-season) shows'
    _VALID_URL = r'https?://www\.youtube\.com/show/(?P<id>[^?#]*)'
    IE_NAME = 'youtube:show'
    _TESTS = [{
        'url': 'http://www.youtube.com/show/airdisasters',
        'playlist_mincount': 3,
        'info_dict': {
            'id': 'airdisasters',
            'title': 'Air Disasters',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        webpage = self._download_webpage(
            url, playlist_id, 'Downloading show webpage')
        # There's one playlist for each season of the show
        m_seasons = list(re.finditer(r'href="(/playlist\?list=.*?)"', webpage))
        self.to_screen('%s: Found %s seasons' % (playlist_id, len(m_seasons)))
        entries = [
            self.url_result(
                'https://www.youtube.com' + season.group(1), 'YoutubePlaylist')
            for season in m_seasons
        ]
        title = self._og_search_title(webpage, fatal=False)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': title,
            'entries': entries,
        }


class YoutubeFeedsInfoExtractor(YoutubeBaseInfoExtractor):
    """
    Base class for extractors that fetch info from
    http://www.youtube.com/feed_ajax
    Subclasses must define the _FEED_NAME and _PLAYLIST_TITLE properties.
    """
    _LOGIN_REQUIRED = True
    # use action_load_personal_feed instead of action_load_system_feed
    _PERSONAL_FEED = False

    @property
    def _FEED_TEMPLATE(self):
        action = 'action_load_system_feed'
        if self._PERSONAL_FEED:
            action = 'action_load_personal_feed'
        return 'https://www.youtube.com/feed_ajax?%s=1&feed_name=%s&paging=%%s' % (action, self._FEED_NAME)

    @property
    def IE_NAME(self):
        return 'youtube:%s' % self._FEED_NAME

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        feed_entries = []
        paging = 0
        for i in itertools.count(1):
            info = self._download_json(self._FEED_TEMPLATE % paging,
                                       '%s feed' % self._FEED_NAME,
                                       'Downloading page %s' % i)
            feed_html = info.get('feed_html') or info.get('content_html')
            load_more_widget_html = info.get('load_more_widget_html') or feed_html
            m_ids = re.finditer(r'"/watch\?v=(.*?)["&]', feed_html)
            ids = orderedSet(m.group(1) for m in m_ids)
            feed_entries.extend(
                self.url_result(video_id, 'Youtube', video_id=video_id)
                for video_id in ids)
            mobj = re.search(
                r'data-uix-load-more-href="/?[^"]+paging=(?P<paging>\d+)',
                load_more_widget_html)
            if mobj is None:
                break
            paging = mobj.group('paging')
        return self.playlist_result(feed_entries, playlist_title=self._PLAYLIST_TITLE)


class YoutubeRecommendedIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'YouTube.com recommended videos, ":ytrec" for short (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/recommended|:ytrec(?:ommended)?'
    _FEED_NAME = 'recommended'
    _PLAYLIST_TITLE = 'Youtube Recommended videos'


class YoutubeWatchLaterIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'Youtube watch later list, ":ytwatchlater" for short (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/watch_later|:ytwatchlater'
    _FEED_NAME = 'watch_later'
    _PLAYLIST_TITLE = 'Youtube Watch Later'
    _PERSONAL_FEED = True


class YoutubeHistoryIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'Youtube watch history, ":ythistory" for short (requires authentication)'
    _VALID_URL = 'https?://www\.youtube\.com/feed/history|:ythistory'
    _FEED_NAME = 'history'
    _PERSONAL_FEED = True
    _PLAYLIST_TITLE = 'Youtube Watch History'


class YoutubeFavouritesIE(YoutubeBaseInfoExtractor):
    IE_NAME = 'youtube:favorites'
    IE_DESC = 'YouTube.com favourite videos, ":ytfav" for short (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/my_favorites|:ytfav(?:ou?rites)?'
    _LOGIN_REQUIRED = True

    def _real_extract(self, url):
        webpage = self._download_webpage('https://www.youtube.com/my_favorites', 'Youtube Favourites videos')
        playlist_id = self._search_regex(r'list=(.+?)["&]', webpage, 'favourites playlist id')
        return self.url_result(playlist_id, 'YoutubePlaylist')


class YoutubeSubscriptionsIE(YoutubePlaylistIE):
    IE_NAME = 'youtube:subscriptions'
    IE_DESC = 'YouTube.com subscriptions feed, "ytsubs" keyword (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/subscriptions|:ytsubs(?:criptions)?'
    _TESTS = []

    def _real_extract(self, url):
        title = 'Youtube Subscriptions'
        page = self._download_webpage('https://www.youtube.com/feed/subscriptions', title)

        # The extraction process is the same as for playlists, but the regex
        # for the video ids doesn't contain an index
        ids = []
        more_widget_html = content_html = page

        for page_num in itertools.count(1):
            matches = re.findall(r'href="\s*/watch\?v=([0-9A-Za-z_-]{11})', content_html)
            new_ids = orderedSet(matches)
            ids.extend(new_ids)

            mobj = re.search(r'data-uix-load-more-href="/?(?P<more>[^"]+)"', more_widget_html)
            if not mobj:
                break

            more = self._download_json(
                'https://youtube.com/%s' % mobj.group('more'), title,
                'Downloading page #%s' % page_num,
                transform_source=uppercase_escape)
            content_html = more['content_html']
            more_widget_html = more['load_more_widget_html']

        return {
            '_type': 'playlist',
            'title': title,
            'entries': self._ids_to_results(ids),
        }


class YoutubeTruncatedURLIE(InfoExtractor):
    IE_NAME = 'youtube:truncated_url'
    IE_DESC = False  # Do not list
    _VALID_URL = r'''(?x)
        (?:https?://)?[^/]+/watch\?(?:
            feature=[a-z_]+|
            annotation_id=annotation_[^&]+
        )?$|
        (?:https?://)?(?:www\.)?youtube\.com/attribution_link\?a=[^&]+$
    '''

    _TESTS = [{
        'url': 'http://www.youtube.com/watch?annotation_id=annotation_3951667041',
        'only_matching': True,
    }, {
        'url': 'http://www.youtube.com/watch?',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        raise ExtractorError(
            'Did you forget to quote the URL? Remember that & is a meta '
            'character in most shells, so you want to put the URL in quotes, '
            'like  youtube-dl '
            '"http://www.youtube.com/watch?feature=foo&v=BaW_jenozKc" '
            ' or simply  youtube-dl BaW_jenozKc  .',
            expected=True)
