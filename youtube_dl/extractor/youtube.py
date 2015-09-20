# coding: utf-8

from __future__ import unicode_literals


import itertools
import json
import os.path
import re
import time
import traceback

from .common import InfoExtractor, SearchInfoExtractor
from ..jsinterp import JSInterpreter
from ..swfinterp import SWFInterpreter
from ..compat import (
    compat_chr,
    compat_parse_qs,
    compat_urllib_parse,
    compat_urllib_parse_unquote,
    compat_urllib_parse_unquote_plus,
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urlparse,
    compat_str,
)
from ..utils import (
    clean_html,
    encode_dict,
    ExtractorError,
    float_or_none,
    get_element_by_attribute,
    get_element_by_id,
    int_or_none,
    orderedSet,
    parse_duration,
    remove_start,
    smuggle_url,
    str_to_int,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    uppercase_escape,
    ISO3166Utils,
)


class YoutubeBaseInfoExtractor(InfoExtractor):
    """Provide base functions for Youtube extractors"""
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _TWOFACTOR_URL = 'https://accounts.google.com/signin/challenge'
    _NETRC_MACHINE = 'youtube'
    # If True it will raise an error if no login info is provided
    _LOGIN_REQUIRED = False

    def _set_language(self):
        self._set_cookie(
            '.youtube.com', 'PREF', 'f1=50000000&hl=en',
            # YouTube sets the expire time to about two months
            expire_time=time.time() + 2 * 30 * 24 * 3600)

    def _ids_to_results(self, ids):
        return [
            self.url_result(vid_id, 'Youtube', video_id=vid_id)
            for vid_id in ids]

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

        login_data = compat_urllib_parse.urlencode(encode_dict(login_form_strs)).encode('ascii')

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

        if re.search(r'(?i)<form[^>]* id="challenge"', login_results) is not None:
            tfa_code = self._get_tfa_info('2-step verification code')

            if not tfa_code:
                self._downloader.report_warning(
                    'Two-factor authentication required. Provide it either interactively or with --twofactor <code>'
                    '(Note that only TOTP (Google Authenticator App) codes work at this time.)')
                return False

            tfa_code = remove_start(tfa_code, 'G-')

            tfa_form_strs = self._form_hidden_inputs('challenge', login_results)

            tfa_form_strs.update({
                'Pin': tfa_code,
                'TrustDevice': 'on',
            })

            tfa_data = compat_urllib_parse.urlencode(encode_dict(tfa_form_strs)).encode('ascii')

            tfa_req = compat_urllib_request.Request(self._TWOFACTOR_URL, tfa_data)
            tfa_results = self._download_webpage(
                tfa_req, None,
                note='Submitting TFA code', errnote='unable to submit tfa', fatal=False)

            if tfa_results is False:
                return False

            if re.search(r'(?i)<form[^>]* id="challenge"', tfa_results) is not None:
                self._downloader.report_warning('Two-factor code expired or invalid. Please try again, or use a one-use backup code instead.')
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


class YoutubeIE(YoutubeBaseInfoExtractor):
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
                                 (?:.*?&)??                                   # any other preceding param (like /?s=tuff&v=xxxx)
                                 v=
                             )
                         ))
                         |(?:
                            youtu\.be|                                        # just youtu.be/xxxx
                            vid\.plus                                         # or vid.plus/xxxx
                         )/
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
        '59': {'ext': 'mp4', 'width': 854, 'height': 480},
        '78': {'ext': 'mp4', 'width': 854, 'height': 480},


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
        '138': {'ext': 'mp4', 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},  # Height can vary (https://github.com/rg3/youtube-dl/issues/4559)
        '160': {'ext': 'mp4', 'height': 144, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '264': {'ext': 'mp4', 'height': 1440, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '298': {'ext': 'mp4', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'h264'},
        '299': {'ext': 'mp4', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'h264'},
        '266': {'ext': 'mp4', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'vcodec': 'h264'},

        # Dash mp4 audio
        '139': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'vcodec': 'none', 'abr': 48, 'preference': -50, 'container': 'm4a_dash'},
        '140': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'vcodec': 'none', 'abr': 128, 'preference': -50, 'container': 'm4a_dash'},
        '141': {'ext': 'm4a', 'format_note': 'DASH audio', 'acodec': 'aac', 'vcodec': 'none', 'abr': 256, 'preference': -50, 'container': 'm4a_dash'},

        # Dash webm
        '167': {'ext': 'webm', 'height': 360, 'width': 640, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'vp8', 'preference': -40},
        '168': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'vp8', 'preference': -40},
        '169': {'ext': 'webm', 'height': 720, 'width': 1280, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'vp8', 'preference': -40},
        '170': {'ext': 'webm', 'height': 1080, 'width': 1920, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'vp8', 'preference': -40},
        '218': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'vp8', 'preference': -40},
        '219': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'vp8', 'preference': -40},
        '278': {'ext': 'webm', 'height': 144, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'container': 'webm', 'vcodec': 'vp9'},
        '242': {'ext': 'webm', 'height': 240, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '243': {'ext': 'webm', 'height': 360, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '244': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '245': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '246': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '247': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '248': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '271': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '272': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40},
        '302': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'vp9'},
        '303': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'vp9'},
        '308': {'ext': 'webm', 'height': 1440, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'vp9'},
        '313': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'vcodec': 'vp9'},
        '315': {'ext': 'webm', 'height': 2160, 'format_note': 'DASH video', 'acodec': 'none', 'preference': -40, 'fps': 60, 'vcodec': 'vp9'},

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
            'url': 'http://www.youtube.com/watch?v=BaW_jenozKcj&t=1s&end=9',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'phihag',
                'upload_date': '20121002',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'tags': ['youtube-dl'],
                'like_count': int,
                'dislike_count': int,
                'start_time': 1,
                'end_time': 9,
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
                'description': 'md5:782e8651347686cba06e58f71ab51773',
                'tags': ['Icona Pop i love it', 'sweden', 'pop music', 'big beat records', 'big beat', 'charli',
                         'xcx', 'charli xcx', 'girls', 'hbo', 'i love it', "i don't care", 'icona', 'pop',
                         'iconic ep', 'iconic', 'love', 'it'],
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
                'age_limit': 18,
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
            'url': 'http://www.youtube.com/watch?v=BaW_jenozKcj&v=UxxajLWwzqY',
            'note': 'Use the first video ID in the URL',
            'info_dict': {
                'id': 'BaW_jenozKc',
                'ext': 'mp4',
                'title': 'youtube-dl test video "\'/\\ä↭𝕐',
                'uploader': 'Philipp Hagemeister',
                'uploader_id': 'phihag',
                'upload_date': '20121002',
                'description': 'test chars:  "\'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de .',
                'categories': ['Science & Technology'],
                'tags': ['youtube-dl'],
                'like_count': int,
                'dislike_count': int,
            },
            'params': {
                'skip_download': True,
            },
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
        # JS player signature function name containing $
        {
            'url': 'https://www.youtube.com/watch?v=nfWlot6h_JM',
            'info_dict': {
                'id': 'nfWlot6h_JM',
                'ext': 'm4a',
                'title': 'Taylor Swift - Shake It Off',
                'description': 'md5:95f66187cd7c8b2c13eb78e1223b63c3',
                'uploader': 'TaylorSwiftVEVO',
                'uploader_id': 'TaylorSwiftVEVO',
                'upload_date': '20140818',
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
                'description': 're:(?s).{100,}About the Game\n.*?The Witcher 3: Wild Hunt.{100,}',
                'uploader': 'The Witcher',
                'uploader_id': 'WitcherGame',
                'upload_date': '20140605',
                'age_limit': 18,
            },
        },
        # Age-gate video with encrypted signature
        {
            'url': 'http://www.youtube.com/watch?v=6kLq3WMV1nU',
            'info_dict': {
                'id': '6kLq3WMV1nU',
                'ext': 'mp4',
                'title': 'Dedication To My Ex (Miss That) (Lyric Video)',
                'description': 'md5:33765bb339e1b47e7e72b5490139bb41',
                'uploader': 'LloydVEVO',
                'uploader_id': 'LloydVEVO',
                'upload_date': '20110629',
                'age_limit': 18,
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
        },
        # Olympics (https://github.com/rg3/youtube-dl/issues/4431)
        {
            'url': 'lqQg6PlCWgI',
            'info_dict': {
                'id': 'lqQg6PlCWgI',
                'ext': 'mp4',
                'upload_date': '20120724',
                'uploader_id': 'olympic',
                'description': 'HO09  - Women -  GER-AUS - Hockey - 31 July 2012 - London 2012 Olympic Games',
                'uploader': 'Olympics',
                'title': 'Hockey - Women -  GER-AUS - London 2012 Olympic Games',
            },
            'params': {
                'skip_download': 'requires avconv',
            }
        },
        # Non-square pixels
        {
            'url': 'https://www.youtube.com/watch?v=_b-2C3KPAM0',
            'info_dict': {
                'id': '_b-2C3KPAM0',
                'ext': 'mp4',
                'stretched_ratio': 16 / 9.,
                'upload_date': '20110310',
                'uploader_id': 'AllenMeow',
                'description': 'made by Wacom from Korea | 字幕&加油添醋 by TY\'s Allen | 感謝heylisa00cavey1001同學熱情提供梗及翻譯',
                'uploader': '孫艾倫',
                'title': '[A-made] 變態妍字幕版 太妍 我就是這樣的人',
            },
        },
        # url_encoded_fmt_stream_map is empty string
        {
            'url': 'qEJwOuvDf7I',
            'info_dict': {
                'id': 'qEJwOuvDf7I',
                'ext': 'webm',
                'title': 'Обсуждение судебной практики по выборам 14 сентября 2014 года в Санкт-Петербурге',
                'description': '',
                'upload_date': '20150404',
                'uploader_id': 'spbelect',
                'uploader': 'Наблюдатели Петербурга',
            },
            'params': {
                'skip_download': 'requires avconv',
            }
        },
        # Extraction from multiple DASH manifests (https://github.com/rg3/youtube-dl/pull/6097)
        {
            'url': 'https://www.youtube.com/watch?v=FIl7x6_3R5Y',
            'info_dict': {
                'id': 'FIl7x6_3R5Y',
                'ext': 'mp4',
                'title': 'md5:7b81415841e02ecd4313668cde88737a',
                'description': 'md5:116377fd2963b81ec4ce64b542173306',
                'upload_date': '20150625',
                'uploader_id': 'dorappi2000',
                'uploader': 'dorappi2000',
                'formats': 'mincount:33',
            },
        },
        # DASH manifest with segment_list
        {
            'url': 'https://www.youtube.com/embed/CsmdDsKjzN8',
            'md5': '8ce563a1d667b599d21064e982ab9e31',
            'info_dict': {
                'id': 'CsmdDsKjzN8',
                'ext': 'mp4',
                'upload_date': '20150501',  # According to '<meta itemprop="datePublished"', but in other places it's 20150510
                'uploader': 'Airtek',
                'description': 'Retransmisión en directo de la XVIII media maratón de Zaragoza.',
                'uploader_id': 'UCzTzUmjXxxacNnL8I3m4LnQ',
                'title': 'Retransmisión XVIII Media maratón Zaragoza 2015',
            },
            'params': {
                'youtube_include_dash_manifest': True,
                'format': '135',  # bestvideo
            }
        },
        {
            # Multifeed videos (multiple cameras), URL is for Main Camera
            'url': 'https://www.youtube.com/watch?v=jqWvoWXjCVs',
            'info_dict': {
                'id': 'jqWvoWXjCVs',
                'title': 'teamPGP: Rocket League Noob Stream',
                'description': 'md5:dc7872fb300e143831327f1bae3af010',
            },
            'playlist': [{
                'info_dict': {
                    'id': 'jqWvoWXjCVs',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (Main Camera)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                },
            }, {
                'info_dict': {
                    'id': '6h8e8xoXJzg',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (kreestuh)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                },
            }, {
                'info_dict': {
                    'id': 'PUOgX5z9xZw',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (grizzle)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                },
            }, {
                'info_dict': {
                    'id': 'teuwxikvS5k',
                    'ext': 'mp4',
                    'title': 'teamPGP: Rocket League Noob Stream (zim)',
                    'description': 'md5:dc7872fb300e143831327f1bae3af010',
                    'upload_date': '20150721',
                    'uploader': 'Beer Games Beer',
                    'uploader_id': 'beergamesbeer',
                },
            }],
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'http://vid.plus/FlRa-iH7PGw',
            'only_matching': True,
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
            r'.*?-(?P<id>[a-zA-Z0-9_-]+)(?:/watch_as3|/html5player(?:-new)?)?\.(?P<ext>[a-z]+)$',
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

        download_note = (
            'Downloading player %s' % player_url
            if self._downloader.params.get('verbose') else
            'Downloading %s player %s' % (player_type, player_id)
        )
        if player_type == 'js':
            code = self._download_webpage(
                player_url, video_id,
                note=download_note,
                errnote='Download of %s failed' % player_url)
            res = self._parse_sig_js(code)
        elif player_type == 'swf':
            urlh = self._request_webpage(
                player_url, video_id,
                note=download_note,
                errnote='Download of %s failed' % player_url)
            code = urlh.read()
            res = self._parse_sig_swf(code)
        else:
            assert False, 'Invalid player type %r' % player_type

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
            # Quelch pyflakes warnings - start will be set when step is set
            start = '(Never used)'
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
            r'\.sig\|\|([a-zA-Z0-9$]+)\(', jscode,
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

    def _get_subtitles(self, video_id, webpage):
        try:
            subs_doc = self._download_xml(
                'https://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id,
                video_id, note=False)
        except ExtractorError as err:
            self._downloader.report_warning('unable to download video subtitles: %s' % compat_str(err))
            return {}

        sub_lang_list = {}
        for track in subs_doc.findall('track'):
            lang = track.attrib['lang_code']
            if lang in sub_lang_list:
                continue
            sub_formats = []
            for ext in ['sbv', 'vtt', 'srt']:
                params = compat_urllib_parse.urlencode({
                    'lang': lang,
                    'v': video_id,
                    'fmt': ext,
                    'name': track.attrib['name'].encode('utf-8'),
                })
                sub_formats.append({
                    'url': 'https://www.youtube.com/api/timedtext?' + params,
                    'ext': ext,
                })
            sub_lang_list[lang] = sub_formats
        if not sub_lang_list:
            self._downloader.report_warning('video doesn\'t have subtitles')
            return {}
        return sub_lang_list

    def _get_automatic_captions(self, video_id, webpage):
        """We need the webpage for getting the captions url, pass it as an
           argument to speed up the process."""
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
            if original_lang_node is None:
                self._downloader.report_warning('Video doesn\'t have automatic captions')
                return {}
            original_lang = original_lang_node.attrib['lang_code']
            caption_kind = original_lang_node.attrib.get('kind', '')

            sub_lang_list = {}
            for lang_node in caption_list.findall('target'):
                sub_lang = lang_node.attrib['lang_code']
                sub_formats = []
                for ext in ['sbv', 'vtt', 'srt']:
                    params = compat_urllib_parse.urlencode({
                        'lang': original_lang,
                        'tlang': sub_lang,
                        'fmt': ext,
                        'ts': timestamp,
                        'kind': caption_kind,
                    })
                    sub_formats.append({
                        'url': caption_url + '&' + params,
                        'ext': ext,
                    })
                sub_lang_list[sub_lang] = sub_formats
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
            self, video_id, dash_manifest_url, player_url, age_gate, fatal=True):
        def decrypt_sig(mobj):
            s = mobj.group(1)
            dec_s = self._decrypt_signature(s, video_id, player_url, age_gate)
            return '/signature/%s' % dec_s
        dash_manifest_url = re.sub(r'/s/([a-fA-F0-9\.]+)', decrypt_sig, dash_manifest_url)
        dash_doc = self._download_xml(
            dash_manifest_url, video_id,
            note='Downloading DASH manifest',
            errnote='Could not download DASH manifest',
            fatal=fatal)

        if dash_doc is False:
            return []

        formats = []
        for a in dash_doc.findall('.//{urn:mpeg:DASH:schema:MPD:2011}AdaptationSet'):
            mime_type = a.attrib.get('mimeType')
            for r in a.findall('{urn:mpeg:DASH:schema:MPD:2011}Representation'):
                url_el = r.find('{urn:mpeg:DASH:schema:MPD:2011}BaseURL')
                if url_el is None:
                    continue
                if mime_type == 'text/vtt':
                    # TODO implement WebVTT downloading
                    pass
                elif mime_type.startswith('audio/') or mime_type.startswith('video/'):
                    segment_list = r.find('{urn:mpeg:DASH:schema:MPD:2011}SegmentList')
                    format_id = r.attrib['id']
                    video_url = url_el.text
                    filesize = int_or_none(url_el.attrib.get('{http://youtube.com/yt/2012/10/10}contentLength'))
                    f = {
                        'format_id': format_id,
                        'url': video_url,
                        'width': int_or_none(r.attrib.get('width')),
                        'height': int_or_none(r.attrib.get('height')),
                        'tbr': int_or_none(r.attrib.get('bandwidth'), 1000),
                        'asr': int_or_none(r.attrib.get('audioSamplingRate')),
                        'filesize': filesize,
                        'fps': int_or_none(r.attrib.get('frameRate')),
                    }
                    if segment_list is not None:
                        f.update({
                            'initialization_url': segment_list.find('{urn:mpeg:DASH:schema:MPD:2011}Initialization').attrib['sourceURL'],
                            'segment_urls': [segment.attrib.get('media') for segment in segment_list.findall('{urn:mpeg:DASH:schema:MPD:2011}SegmentURL')],
                            'protocol': 'http_dash_segments',
                        })
                    try:
                        existing_format = next(
                            fo for fo in formats
                            if fo['format_id'] == format_id)
                    except StopIteration:
                        full_info = self._formats.get(format_id, {}).copy()
                        full_info.update(f)
                        codecs = r.attrib.get('codecs')
                        if codecs:
                            if full_info.get('acodec') == 'none' and 'vcodec' not in full_info:
                                full_info['vcodec'] = codecs
                            elif full_info.get('vcodec') == 'none' and 'acodec' not in full_info:
                                full_info['acodec'] = codecs
                        formats.append(full_info)
                    else:
                        existing_format.update(f)
                else:
                    self.report_warning('Unknown MIME type %s in DASH manifest' % mime_type)
        return formats

    def _real_extract(self, url):
        url, smuggled_data = unsmuggle_url(url, {})

        proto = (
            'http' if self._downloader.params.get('prefer_insecure', False)
            else 'https')

        start_time = None
        end_time = None
        parsed_url = compat_urllib_parse_urlparse(url)
        for component in [parsed_url.fragment, parsed_url.query]:
            query = compat_parse_qs(component)
            if start_time is None and 't' in query:
                start_time = parse_duration(query['t'][0])
            if start_time is None and 'start' in query:
                start_time = parse_duration(query['start'][0])
            if end_time is None and 'end' in query:
                end_time = parse_duration(query['end'][0])

        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = proto + '://www.youtube.com/' + compat_urllib_parse_unquote(mobj.group(1)).lstrip('/')
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

        dash_mpds = []

        def add_dash_mpd(video_info):
            dash_mpd = video_info.get('dashmpd')
            if dash_mpd and dash_mpd[0] not in dash_mpds:
                dash_mpds.append(dash_mpd[0])

        # Get video info
        embed_webpage = None
        is_live = None
        if re.search(r'player-age-gate-content">', video_webpage) is not None:
            age_gate = True
            # We simulate the access to the video from www.youtube.com/v/{video_id}
            # this can be viewed without login into Youtube
            url = proto + '://www.youtube.com/embed/%s' % video_id
            embed_webpage = self._download_webpage(url, video_id, 'Downloading embed webpage')
            data = compat_urllib_parse.urlencode({
                'video_id': video_id,
                'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                'sts': self._search_regex(
                    r'"sts"\s*:\s*(\d+)', embed_webpage, 'sts', default=''),
            })
            video_info_url = proto + '://www.youtube.com/get_video_info?' + data
            video_info_webpage = self._download_webpage(
                video_info_url, video_id,
                note='Refetching age-gated info webpage',
                errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
            add_dash_mpd(video_info)
        else:
            age_gate = False
            video_info = None
            # Try looking directly into the video webpage
            mobj = re.search(r';ytplayer\.config\s*=\s*({.*?});', video_webpage)
            if mobj:
                json_code = uppercase_escape(mobj.group(1))
                ytplayer_config = json.loads(json_code)
                args = ytplayer_config['args']
                if args.get('url_encoded_fmt_stream_map'):
                    # Convert to the same format returned by compat_parse_qs
                    video_info = dict((k, [v]) for k, v in args.items())
                    add_dash_mpd(video_info)
                if args.get('livestream') == '1' or args.get('live_playback') == 1:
                    is_live = True
            if not video_info or self._downloader.params.get('youtube_include_dash_manifest', True):
                # We also try looking in get_video_info since it may contain different dashmpd
                # URL that points to a DASH manifest with possibly different itag set (some itags
                # are missing from DASH manifest pointed by webpage's dashmpd, some - from DASH
                # manifest pointed by get_video_info's dashmpd).
                # The general idea is to take a union of itags of both DASH manifests (for example
                # video with such 'manifest behavior' see https://github.com/rg3/youtube-dl/issues/6093)
                self.report_video_info_webpage_download(video_id)
                for el_type in ['&el=info', '&el=embedded', '&el=detailpage', '&el=vevo', '']:
                    video_info_url = (
                        '%s://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
                        % (proto, video_id, el_type))
                    video_info_webpage = self._download_webpage(
                        video_info_url,
                        video_id, note=False,
                        errnote='unable to download video info webpage')
                    get_video_info = compat_parse_qs(video_info_webpage)
                    if get_video_info.get('use_cipher_signature') != ['True']:
                        add_dash_mpd(get_video_info)
                    if not video_info:
                        video_info = get_video_info
                    if 'token' in get_video_info:
                        break
        if 'token' not in video_info:
            if 'reason' in video_info:
                if 'The uploader has not made this video available in your country.' in video_info['reason']:
                    regions_allowed = self._html_search_meta('regionsAllowed', video_webpage, default=None)
                    if regions_allowed:
                        raise ExtractorError('YouTube said: This video is available in %s only' % (
                            ', '.join(map(ISO3166Utils.short2full, regions_allowed.split(',')))),
                            expected=True)
                raise ExtractorError(
                    'YouTube said: %s' % video_info['reason'][0],
                    expected=True, video_id=video_id)
            else:
                raise ExtractorError(
                    '"token" parameter not in video info for unknown reason',
                    video_id=video_id)

        # title
        if 'title' in video_info:
            video_title = video_info['title'][0]
        else:
            self._downloader.report_warning('Unable to extract video title')
            video_title = '_'

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

        if 'multifeed_metadata_list' in video_info and not smuggled_data.get('force_singlefeed', False):
            if not self._downloader.params.get('noplaylist'):
                entries = []
                feed_ids = []
                multifeed_metadata_list = compat_urllib_parse_unquote_plus(video_info['multifeed_metadata_list'][0])
                for feed in multifeed_metadata_list.split(','):
                    feed_data = compat_parse_qs(feed)
                    entries.append({
                        '_type': 'url_transparent',
                        'ie_key': 'Youtube',
                        'url': smuggle_url(
                            '%s://www.youtube.com/watch?v=%s' % (proto, feed_data['id'][0]),
                            {'force_singlefeed': True}),
                        'title': '%s (%s)' % (video_title, feed_data['title'][0]),
                    })
                    feed_ids.append(feed_data['id'][0])
                self.to_screen(
                    'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
                    % (', '.join(feed_ids), video_id))
                return self.playlist_result(entries, video_id, video_title, video_description)
            self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

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
        video_uploader = compat_urllib_parse_unquote_plus(video_info['author'][0])

        # uploader_id
        video_uploader_id = None
        mobj = re.search(r'<link itemprop="url" href="http://www.youtube.com/(?:user|channel)/([^"]+)">', video_webpage)
        if mobj is not None:
            video_uploader_id = mobj.group(1)
        else:
            self._downloader.report_warning('unable to extract uploader nickname')

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
            video_thumbnail = compat_urllib_parse_unquote_plus(video_info['thumbnail_url'][0])

        # upload date
        upload_date = self._html_search_meta(
            'datePublished', video_webpage, 'upload date', default=None)
        if not upload_date:
            upload_date = self._search_regex(
                [r'(?s)id="eow-date.*?>(.*?)</span>',
                 r'id="watch-uploader-info".*?>.*?(?:Published|Uploaded|Streamed live|Started) on (.+?)</strong>'],
                video_webpage, 'upload date', default=None)
            if upload_date:
                upload_date = ' '.join(re.sub(r'[/,-]', r' ', mobj.group(1)).split())
        upload_date = unified_strdate(upload_date)

        m_cat_container = self._search_regex(
            r'(?s)<h4[^>]*>\s*Category\s*</h4>\s*<ul[^>]*>(.*?)</ul>',
            video_webpage, 'categories', default=None)
        if m_cat_container:
            category = self._html_search_regex(
                r'(?s)<a[^<]+>(.*?)</a>', m_cat_container, 'category',
                default=None)
            video_categories = None if category is None else [category]
        else:
            video_categories = None

        video_tags = [
            unescapeHTML(m.group('content'))
            for m in re.finditer(self._meta_regex('og:video:tag'), video_webpage)]

        def _extract_count(count_name):
            return str_to_int(self._search_regex(
                r'-%s-button[^>]+><span[^>]+class="yt-uix-button-content"[^>]*>([\d,]+)</span>'
                % re.escape(count_name),
                video_webpage, count_name, default=None))

        like_count = _extract_count('like')
        dislike_count = _extract_count('dislike')

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, video_webpage)
        automatic_captions = self.extract_automatic_captions(video_id, video_webpage)

        if 'length_seconds' not in video_info:
            self._downloader.report_warning('unable to extract video duration')
            video_duration = None
        else:
            video_duration = int(compat_urllib_parse_unquote_plus(video_info['length_seconds'][0]))

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
        elif len(video_info.get('url_encoded_fmt_stream_map', [''])[0]) >= 1 or len(video_info.get('adaptive_fmts', [''])[0]) >= 1:
            encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + video_info.get('adaptive_fmts', [''])[0]
            if 'rtmpe%3Dyes' in encoded_url_map:
                raise ExtractorError('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.', expected=True)
            formats = []
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
                    ASSETS_RE = r'"assets":.+?"js":\s*("[^"]+")'

                    jsplayer_url_json = self._search_regex(
                        ASSETS_RE,
                        embed_webpage if age_gate else video_webpage,
                        'JS player URL (1)', default=None)
                    if not jsplayer_url_json and not age_gate:
                        # We need the embed website after all
                        if embed_webpage is None:
                            embed_url = proto + '://www.youtube.com/embed/%s' % video_id
                            embed_webpage = self._download_webpage(
                                embed_url, video_id, 'Downloading embed webpage')
                        jsplayer_url_json = self._search_regex(
                            ASSETS_RE, embed_webpage, 'JS player URL')

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
                                    r'html5player-([^/]+?)(?:/html5player(?:-new)?)?\.js',
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

                # Some itags are not included in DASH manifest thus corresponding formats will
                # lack metadata (see https://github.com/rg3/youtube-dl/pull/5993).
                # Trying to extract metadata from url_encoded_fmt_stream_map entry.
                mobj = re.search(r'^(?P<width>\d+)[xX](?P<height>\d+)$', url_data.get('size', [''])[0])
                width, height = (int(mobj.group('width')), int(mobj.group('height'))) if mobj else (None, None)
                dct = {
                    'format_id': format_id,
                    'url': url,
                    'player_url': player_url,
                    'filesize': int_or_none(url_data.get('clen', [None])[0]),
                    'tbr': float_or_none(url_data.get('bitrate', [None])[0], 1000),
                    'width': width,
                    'height': height,
                    'fps': int_or_none(url_data.get('fps', [None])[0]),
                    'format_note': url_data.get('quality_label', [None])[0] or url_data.get('quality', [None])[0],
                }
                type_ = url_data.get('type', [None])[0]
                if type_:
                    type_split = type_.split(';')
                    kind_ext = type_split[0].split('/')
                    if len(kind_ext) == 2:
                        kind, ext = kind_ext
                        dct['ext'] = ext
                        if kind in ('audio', 'video'):
                            codecs = None
                            for mobj in re.finditer(
                                    r'(?P<key>[a-zA-Z_-]+)=(?P<quote>["\']?)(?P<val>.+?)(?P=quote)(?:;|$)', type_):
                                if mobj.group('key') == 'codecs':
                                    codecs = mobj.group('val')
                                    break
                            if codecs:
                                codecs = codecs.split(',')
                                if len(codecs) == 2:
                                    acodec, vcodec = codecs[0], codecs[1]
                                else:
                                    acodec, vcodec = (codecs[0], 'none') if kind == 'audio' else ('none', codecs[0])
                                dct.update({
                                    'acodec': acodec,
                                    'vcodec': vcodec,
                                })
                if format_id in self._formats:
                    dct.update(self._formats[format_id])
                formats.append(dct)
        elif video_info.get('hlsvp'):
            manifest_url = video_info['hlsvp'][0]
            url_map = self._extract_from_m3u8(manifest_url, video_id)
            formats = _map_to_format_list(url_map)
        else:
            raise ExtractorError('no conn, hlsvp or url_encoded_fmt_stream_map information found in video info')

        # Look for the DASH manifest
        if self._downloader.params.get('youtube_include_dash_manifest', True):
            dash_mpd_fatal = True
            for dash_manifest_url in dash_mpds:
                dash_formats = {}
                try:
                    for df in self._parse_dash_manifest(
                            video_id, dash_manifest_url, player_url, age_gate, dash_mpd_fatal):
                        # Do not overwrite DASH format found in some previous DASH manifest
                        if df['format_id'] not in dash_formats:
                            dash_formats[df['format_id']] = df
                        # Additional DASH manifests may end up in HTTP Error 403 therefore
                        # allow them to fail without bug report message if we already have
                        # some DASH manifest succeeded. This is temporary workaround to reduce
                        # burst of bug reports until we figure out the reason and whether it
                        # can be fixed at all.
                        dash_mpd_fatal = False
                except (ExtractorError, KeyError) as e:
                    self.report_warning(
                        'Skipping DASH manifest: %r' % e, video_id)
                if dash_formats:
                    # Remove the formats we found through non-DASH, they
                    # contain less info and it can be wrong, because we use
                    # fixed values (for example the resolution). See
                    # https://github.com/rg3/youtube-dl/issues/5774 for an
                    # example.
                    formats = [f for f in formats if f['format_id'] not in dash_formats.keys()]
                    formats.extend(dash_formats.values())

        # Check for malformed aspect ratio
        stretched_m = re.search(
            r'<meta\s+property="og:video:tag".*?content="yt:stretch=(?P<w>[0-9]+):(?P<h>[0-9]+)">',
            video_webpage)
        if stretched_m:
            ratio = float(stretched_m.group('w')) / float(stretched_m.group('h'))
            for f in formats:
                if f.get('vcodec') != 'none':
                    f['stretched_ratio'] = ratio

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
            'tags': video_tags,
            'subtitles': video_subtitles,
            'automatic_captions': automatic_captions,
            'duration': video_duration,
            'age_limit': 18 if age_gate else 0,
            'annotations': video_annotations,
            'webpage_url': proto + '://www.youtube.com/watch?v=%s' % video_id,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'average_rating': float_or_none(video_info.get('avg_rating', [None])[0]),
            'formats': formats,
            'is_live': is_live,
            'start_time': start_time,
            'end_time': end_time,
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
                            (?:PL|LL|EC|UU|FL|RD|UL)?[0-9A-Za-z-_]{10,}
                            # Top tracks, they can also include dots
                            |(?:MC)[\w\.]*
                        )
                        .*
                     |
                        ((?:PL|LL|EC|UU|FL|RD|UL)[0-9A-Za-z-_]{10,})
                     )"""
    _TEMPLATE_URL = 'https://www.youtube.com/playlist?list=%s'
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
            'id': 'PLtPgu7CB4gbZDA7i_euNxn75ISqxwZPYx',
            'title': 'YDL_Empty_List',
        },
        'playlist_count': 0,
    }, {
        'note': 'Playlist with deleted videos (#651). As a bonus, the video #51 is also twice in this list.',
        'url': 'https://www.youtube.com/playlist?list=PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC',
        'info_dict': {
            'title': '29C3: Not my department',
            'id': 'PLwP_SiAcdui0KVebT0mU9Apz359a4ubsC',
        },
        'playlist_count': 95,
    }, {
        'note': 'issue #673',
        'url': 'PLBB231211A4F62143',
        'info_dict': {
            'title': '[OLD]Team Fortress 2 (Class-based LP)',
            'id': 'PLBB231211A4F62143',
        },
        'playlist_mincount': 26,
    }, {
        'note': 'Large playlist',
        'url': 'https://www.youtube.com/playlist?list=UUBABnxM4Ar9ten8Mdjj1j0Q',
        'info_dict': {
            'title': 'Uploads from Cauchemar',
            'id': 'UUBABnxM4Ar9ten8Mdjj1j0Q',
        },
        'playlist_mincount': 799,
    }, {
        'url': 'PLtPgu7CB4gbY9oDN3drwC3cMbJggS7dKl',
        'info_dict': {
            'title': 'YDL_safe_search',
            'id': 'PLtPgu7CB4gbY9oDN3drwC3cMbJggS7dKl',
        },
        'playlist_count': 2,
    }, {
        'note': 'embedded',
        'url': 'http://www.youtube.com/embed/videoseries?list=PL6IaIsEjSbf96XFRuNccS_RuEXwNdsoEu',
        'playlist_count': 4,
        'info_dict': {
            'title': 'JODA15',
            'id': 'PL6IaIsEjSbf96XFRuNccS_RuEXwNdsoEu',
        }
    }, {
        'note': 'Embedded SWF player',
        'url': 'http://www.youtube.com/p/YN5VISEtHet5D4NEvfTd0zcgFk84NqFZ?hl=en_US&fs=1&rel=0',
        'playlist_count': 4,
        'info_dict': {
            'title': 'JODA7',
            'id': 'YN5VISEtHet5D4NEvfTd0zcgFk84NqFZ',
        }
    }, {
        'note': 'Buggy playlist: the webpage has a "Load more" button but it doesn\'t have more videos',
        'url': 'https://www.youtube.com/playlist?list=UUXw-G3eDE9trcvY2sBMM_aA',
        'info_dict': {
            'title': 'Uploads from Interstellar Movie',
            'id': 'UUXw-G3eDE9trcvY2sBMM_aA',
        },
        'playlist_mincout': 21,
    }]

    def _real_initialize(self):
        self._login()

    def _extract_mix(self, playlist_id):
        # The mixes are generated from a single video
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

    def _extract_playlist(self, playlist_id):
        url = self._TEMPLATE_URL % playlist_id
        page = self._download_webpage(url, playlist_id)

        for match in re.findall(r'<div class="yt-alert-message">([^<]+)</div>', page):
            match = match.strip()
            # Check if the playlist exists or is private
            if re.match(r'[^<]*(The|This) playlist (does not exist|is private)[^<]*', match):
                raise ExtractorError(
                    'The playlist doesn\'t exist or is private, use --username or '
                    '--netrc to access it.',
                    expected=True)
            elif re.match(r'[^<]*Invalid parameters[^<]*', match):
                raise ExtractorError(
                    'Invalid parameters. Maybe URL is incorrect.',
                    expected=True)
            elif re.match(r'[^<]*Choose your language[^<]*', match):
                continue
            else:
                self.report_warning('Youtube gives an alert message: ' + match)

        # Extract the video ids from the playlist pages
        def _entries():
            more_widget_html = content_html = page
            for page_num in itertools.count(1):
                matches = re.finditer(self._VIDEO_RE, content_html)
                # We remove the duplicates and the link with index 0
                # (it's not the first video of the playlist)
                new_ids = orderedSet(m.group('id') for m in matches if m.group('index') != '0')
                for vid_id in new_ids:
                    yield self.url_result(vid_id, 'Youtube', video_id=vid_id)

                mobj = re.search(r'data-uix-load-more-href="/?(?P<more>[^"]+)"', more_widget_html)
                if not mobj:
                    break

                more = self._download_json(
                    'https://youtube.com/%s' % mobj.group('more'), playlist_id,
                    'Downloading page #%s' % page_num,
                    transform_source=uppercase_escape)
                content_html = more['content_html']
                if not content_html.strip():
                    # Some webpages show a "Load more" button but they don't
                    # have more videos
                    break
                more_widget_html = more['load_more_widget_html']

        playlist_title = self._html_search_regex(
            r'(?s)<h1 class="pl-header-title[^"]*">\s*(.*?)\s*</h1>',
            page, 'title')

        return self.playlist_result(_entries(), playlist_id, playlist_title)

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

        if playlist_id.startswith('RD') or playlist_id.startswith('UL'):
            # Mixes require a custom extraction process
            return self._extract_mix(playlist_id)

        return self._extract_playlist(playlist_id)


class YoutubeChannelIE(InfoExtractor):
    IE_DESC = 'YouTube.com channels'
    _VALID_URL = r'https?://(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/(?P<id>[0-9A-Za-z_-]+)'
    _TEMPLATE_URL = 'https://www.youtube.com/channel/%s/videos'
    IE_NAME = 'youtube:channel'
    _TESTS = [{
        'note': 'paginated channel',
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w',
        'playlist_mincount': 91,
        'info_dict': {
            'id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
        }
    }]

    @staticmethod
    def extract_videos_from_page(page):
        ids_in_page = []
        titles_in_page = []
        for mobj in re.finditer(r'(?:title="(?P<title>[^"]+)"[^>]+)?href="/watch\?v=(?P<id>[0-9A-Za-z_-]+)&?', page):
            video_id = mobj.group('id')
            video_title = unescapeHTML(mobj.group('title'))
            try:
                idx = ids_in_page.index(video_id)
                if video_title and not titles_in_page[idx]:
                    titles_in_page[idx] = video_title
            except ValueError:
                ids_in_page.append(video_id)
                titles_in_page.append(video_title)
        return zip(ids_in_page, titles_in_page)

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        url = self._TEMPLATE_URL % channel_id

        # Channel by page listing is restricted to 35 pages of 30 items, i.e. 1050 videos total (see #5778)
        # Workaround by extracting as a playlist if managed to obtain channel playlist URL
        # otherwise fallback on channel by page extraction
        channel_page = self._download_webpage(
            url + '?view=57', channel_id,
            'Downloading channel page', fatal=False)
        if channel_page is False:
            channel_playlist_id = False
        else:
            channel_playlist_id = self._html_search_meta(
                'channelId', channel_page, 'channel id', default=None)
            if not channel_playlist_id:
                channel_playlist_id = self._search_regex(
                    r'data-channel-external-id="([^"]+)"',
                    channel_page, 'channel id', default=None)
        if channel_playlist_id and channel_playlist_id.startswith('UC'):
            playlist_id = 'UU' + channel_playlist_id[2:]
            return self.url_result(
                compat_urlparse.urljoin(url, '/playlist?list=%s' % playlist_id), 'YoutubePlaylist')

        channel_page = self._download_webpage(url, channel_id, 'Downloading page #1')
        autogenerated = re.search(r'''(?x)
                class="[^"]*?(?:
                    channel-header-autogenerated-label|
                    yt-channel-title-autogenerated
                )[^"]*"''', channel_page) is not None

        if autogenerated:
            # The videos are contained in a single page
            # the ajax pages can't be used, they are empty
            entries = [
                self.url_result(
                    video_id, 'Youtube', video_id=video_id,
                    video_title=video_title)
                for video_id, video_title in self.extract_videos_from_page(channel_page)]
            return self.playlist_result(entries, channel_id)

        def _entries():
            more_widget_html = content_html = channel_page
            for pagenum in itertools.count(1):

                for video_id, video_title in self.extract_videos_from_page(content_html):
                    yield self.url_result(
                        video_id, 'Youtube', video_id=video_id,
                        video_title=video_title)

                mobj = re.search(
                    r'data-uix-load-more-href="/?(?P<more>[^"]+)"',
                    more_widget_html)
                if not mobj:
                    break

                more = self._download_json(
                    'https://youtube.com/%s' % mobj.group('more'), channel_id,
                    'Downloading page #%s' % (pagenum + 1),
                    transform_source=uppercase_escape)
                content_html = more['content_html']
                more_widget_html = more['load_more_widget_html']

        return self.playlist_result(_entries(), channel_id)


class YoutubeUserIE(YoutubeChannelIE):
    IE_DESC = 'YouTube.com user videos (URL or "ytuser" keyword)'
    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/(?:user/)?(?!(?:attribution_link|watch|results)(?:$|[^a-z_A-Z0-9-])))|ytuser:)(?!feed/)(?P<id>[A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'https://www.youtube.com/user/%s/videos'
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


class YoutubeSearchIE(SearchInfoExtractor, YoutubePlaylistIE):
    IE_DESC = 'YouTube.com searches'
    # there doesn't appear to be a real limit, for example if you search for
    # 'python' you get more than 8.000.000 results
    _MAX_RESULTS = float('inf')
    IE_NAME = 'youtube:search'
    _SEARCH_KEY = 'ytsearch'
    _EXTRA_QUERY_ARGS = {}
    _TESTS = []

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        videos = []
        limit = n

        for pagenum in itertools.count(1):
            url_query = {
                'search_query': query.encode('utf-8'),
                'page': pagenum,
                'spf': 'navigate',
            }
            url_query.update(self._EXTRA_QUERY_ARGS)
            result_url = 'https://www.youtube.com/results?' + compat_urllib_parse.urlencode(url_query)
            data = self._download_json(
                result_url, video_id='query "%s"' % query,
                note='Downloading page %s' % pagenum,
                errnote='Unable to download API page')
            html_content = data[1]['body']['content']

            if 'class="search-message' in html_content:
                raise ExtractorError(
                    '[youtube] No video results', expected=True)

            new_videos = self._ids_to_results(orderedSet(re.findall(
                r'href="/watch\?v=(.{11})', html_content)))
            videos += new_videos
            if not new_videos or len(videos) > limit:
                break

        if len(videos) > n:
            videos = videos[:n]
        return self.playlist_result(videos, query)


class YoutubeSearchDateIE(YoutubeSearchIE):
    IE_NAME = YoutubeSearchIE.IE_NAME + ':date'
    _SEARCH_KEY = 'ytsearchdate'
    IE_DESC = 'YouTube.com searches, newest videos first'
    _EXTRA_QUERY_ARGS = {'search_sort': 'video_date_uploaded'}


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
        query = compat_urllib_parse_unquote_plus(mobj.group('query'))

        webpage = self._download_webpage(url, query)
        result_code = self._search_regex(
            r'(?s)<ol[^>]+class="item-section"(.*?)</ol>', webpage, 'result HTML')

        part_codes = re.findall(
            r'(?s)<h3[^>]+class="[^"]*yt-lockup-title[^"]*"[^>]*>(.*?)</h3>', result_code)
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
        'url': 'https://www.youtube.com/show/airdisasters',
        'playlist_mincount': 5,
        'info_dict': {
            'id': 'airdisasters',
            'title': 'Air Disasters',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')
        webpage = self._download_webpage(
            'https://www.youtube.com/show/%s/playlists' % playlist_id, playlist_id, 'Downloading show webpage')
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
    Base class for feed extractors
    Subclasses must define the _FEED_NAME and _PLAYLIST_TITLE properties.
    """
    _LOGIN_REQUIRED = True

    @property
    def IE_NAME(self):
        return 'youtube:%s' % self._FEED_NAME

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        page = self._download_webpage(
            'https://www.youtube.com/feed/%s' % self._FEED_NAME, self._PLAYLIST_TITLE)

        # The extraction process is the same as for playlists, but the regex
        # for the video ids doesn't contain an index
        ids = []
        more_widget_html = content_html = page
        for page_num in itertools.count(1):
            matches = re.findall(r'href="\s*/watch\?v=([0-9A-Za-z_-]{11})', content_html)

            # 'recommended' feed has infinite 'load more' and each new portion spins
            # the same videos in (sometimes) slightly different order, so we'll check
            # for unicity and break when portion has no new videos
            new_ids = filter(lambda video_id: video_id not in ids, orderedSet(matches))
            if not new_ids:
                break

            ids.extend(new_ids)

            mobj = re.search(r'data-uix-load-more-href="/?(?P<more>[^"]+)"', more_widget_html)
            if not mobj:
                break

            more = self._download_json(
                'https://youtube.com/%s' % mobj.group('more'), self._PLAYLIST_TITLE,
                'Downloading page #%s' % page_num,
                transform_source=uppercase_escape)
            content_html = more['content_html']
            more_widget_html = more['load_more_widget_html']

        return self.playlist_result(
            self._ids_to_results(ids), playlist_title=self._PLAYLIST_TITLE)


class YoutubeWatchLaterIE(YoutubePlaylistIE):
    IE_NAME = 'youtube:watchlater'
    IE_DESC = 'Youtube watch later list, ":ytwatchlater" for short (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/(?:feed/watch_later|playlist\?list=WL)|:ytwatchlater'

    _TESTS = []  # override PlaylistIE tests

    def _real_extract(self, url):
        return self._extract_playlist('WL')


class YoutubeFavouritesIE(YoutubeBaseInfoExtractor):
    IE_NAME = 'youtube:favorites'
    IE_DESC = 'YouTube.com favourite videos, ":ytfav" for short (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/my_favorites|:ytfav(?:ou?rites)?'
    _LOGIN_REQUIRED = True

    def _real_extract(self, url):
        webpage = self._download_webpage('https://www.youtube.com/my_favorites', 'Youtube Favourites videos')
        playlist_id = self._search_regex(r'list=(.+?)["&]', webpage, 'favourites playlist id')
        return self.url_result(playlist_id, 'YoutubePlaylist')


class YoutubeRecommendedIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'YouTube.com recommended videos, ":ytrec" for short (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/recommended|:ytrec(?:ommended)?'
    _FEED_NAME = 'recommended'
    _PLAYLIST_TITLE = 'Youtube Recommended videos'


class YoutubeSubscriptionsIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'YouTube.com subscriptions feed, "ytsubs" keyword (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/feed/subscriptions|:ytsubs(?:criptions)?'
    _FEED_NAME = 'subscriptions'
    _PLAYLIST_TITLE = 'Youtube Subscriptions'


class YoutubeHistoryIE(YoutubeFeedsInfoExtractor):
    IE_DESC = 'Youtube watch history, ":ythistory" for short (requires authentication)'
    _VALID_URL = 'https?://www\.youtube\.com/feed/history|:ythistory'
    _FEED_NAME = 'history'
    _PLAYLIST_TITLE = 'Youtube History'


class YoutubeTruncatedURLIE(InfoExtractor):
    IE_NAME = 'youtube:truncated_url'
    IE_DESC = False  # Do not list
    _VALID_URL = r'''(?x)
        (?:https?://)?
        (?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie)?\.com/
        (?:watch\?(?:
            feature=[a-z_]+|
            annotation_id=annotation_[^&]+|
            x-yt-cl=[0-9]+|
            hl=[^&]*|
            t=[0-9]+
        )?
        |
            attribution_link\?a=[^&]+
        )
        $
    '''

    _TESTS = [{
        'url': 'http://www.youtube.com/watch?annotation_id=annotation_3951667041',
        'only_matching': True,
    }, {
        'url': 'http://www.youtube.com/watch?',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?x-yt-cl=84503534',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?feature=foo',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?hl=en-GB',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/watch?t=2372',
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


class YoutubeTruncatedIDIE(InfoExtractor):
    IE_NAME = 'youtube:truncated_id'
    IE_DESC = False  # Do not list
    _VALID_URL = r'https?://(?:www\.)?youtube\.com/watch\?v=(?P<id>[0-9A-Za-z_-]{1,10})$'

    _TESTS = [{
        'url': 'https://www.youtube.com/watch?v=N_708QY7Ob',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        raise ExtractorError(
            'Incomplete YouTube ID %s. URL %s looks truncated.' % (video_id, url),
            expected=True)
