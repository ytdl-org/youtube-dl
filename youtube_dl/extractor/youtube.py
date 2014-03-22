# coding: utf-8

import collections
import errno
import io
import itertools
import json
import os.path
import re
import string
import struct
import traceback
import zlib

from .common import InfoExtractor, SearchInfoExtractor
from .subtitles import SubtitlesInfoExtractor
from ..utils import (
    compat_chr,
    compat_parse_qs,
    compat_urllib_parse,
    compat_urllib_request,
    compat_urlparse,
    compat_str,

    clean_html,
    get_cachedir,
    get_element_by_id,
    get_element_by_attribute,
    ExtractorError,
    int_or_none,
    PagedList,
    unescapeHTML,
    unified_strdate,
    orderedSet,
    write_json_file,
    uppercase_escape,
)

class YoutubeBaseInfoExtractor(InfoExtractor):
    """Provide base functions for Youtube extractors"""
    _LOGIN_URL = 'https://accounts.google.com/ServiceLogin'
    _LANG_URL = r'https://www.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
    _AGE_URL = 'https://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'
    _NETRC_MACHINE = 'youtube'
    # If True it will raise an error if no login info is provided
    _LOGIN_REQUIRED = False

    def _set_language(self):
        return bool(self._download_webpage(
            self._LANG_URL, None,
            note=u'Setting language', errnote='unable to set language',
            fatal=False))

    def _login(self):
        (username, password) = self._get_login_info()
        # No authentication to be performed
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError(u'No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return False

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note=u'Downloading login page',
            errnote=u'unable to fetch login page', fatal=False)
        if login_page is False:
            return

        galx = self._search_regex(r'(?s)<input.+?name="GALX".+?value="(.+?)"',
                                  login_page, u'Login GALX parameter')

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

        req = compat_urllib_request.Request(self._LOGIN_URL, login_data)
        login_results = self._download_webpage(
            req, None,
            note=u'Logging in', errnote=u'unable to log in', fatal=False)
        if login_results is False:
            return False
        if re.search(r'(?i)<form[^>]* id="gaia_loginform"', login_results) is not None:
            self._downloader.report_warning(u'unable to log in: bad username or password')
            return False
        return True

    def _confirm_age(self):
        age_form = {
            'next_url': '/',
            'action_confirm': 'Confirm',
        }
        req = compat_urllib_request.Request(self._AGE_URL,
            compat_urllib_parse.urlencode(age_form).encode('ascii'))

        self._download_webpage(
            req, None,
            note=u'Confirming age', errnote=u'Unable to confirm age')
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
    _VALID_URL = r"""(?x)^
                     (
                         (?:https?://|//)?                                    # http(s):// or protocol-independent URL (optional)
                         (?:(?:(?:(?:\w+\.)?[yY][oO][uU][tT][uU][bB][eE](?:-nocookie)?\.com/|
                            (?:www\.)?deturl\.com/www\.youtube\.com/|
                            (?:www\.)?pwnyoutube\.com/|
                            (?:www\.)?yourepeat\.com/|
                            tube\.majestyc\.net/|
                            youtube\.googleapis\.com/)                        # the various hostnames, with wildcard subdomains
                         (?:.*?\#/)?                                          # handle anchor (#/) redirect urls
                         (?:                                                  # the various things that can precede the ID:
                             (?:(?:v|embed|e)/)                               # v/ or embed/ or e/
                             |(?:                                             # or the v= param in all its forms
                                 (?:(?:watch|movie)(?:_popup)?(?:\.php)?/?)?  # preceding watch(_popup|.php) or nothing (like /?v=xxxx)
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

        # Dash mp4 audio
        '139': {'ext': 'm4a', 'format_note': 'DASH audio', 'vcodec': 'none', 'abr': 48, 'preference': -50},
        '140': {'ext': 'm4a', 'format_note': 'DASH audio', 'vcodec': 'none', 'abr': 128, 'preference': -50},
        '141': {'ext': 'm4a', 'format_note': 'DASH audio', 'vcodec': 'none', 'abr': 256, 'preference': -50},

        # Dash webm
        '167': {'ext': 'webm', 'height': 360, 'width': 640, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'acodec': 'none', 'preference': -40},
        '168': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'acodec': 'none', 'preference': -40},
        '169': {'ext': 'webm', 'height': 720, 'width': 1280, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'acodec': 'none', 'preference': -40},
        '170': {'ext': 'webm', 'height': 1080, 'width': 1920, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'acodec': 'none', 'preference': -40},
        '218': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'acodec': 'none', 'preference': -40},
        '219': {'ext': 'webm', 'height': 480, 'width': 854, 'format_note': 'DASH video', 'acodec': 'none', 'container': 'webm', 'vcodec': 'VP8', 'acodec': 'none', 'preference': -40},
        '242': {'ext': 'webm', 'height': 240, 'format_note': 'DASH webm', 'preference': -40},
        '243': {'ext': 'webm', 'height': 360, 'format_note': 'DASH webm', 'preference': -40},
        '244': {'ext': 'webm', 'height': 480, 'format_note': 'DASH webm', 'preference': -40},
        '245': {'ext': 'webm', 'height': 480, 'format_note': 'DASH webm', 'preference': -40},
        '246': {'ext': 'webm', 'height': 480, 'format_note': 'DASH webm', 'preference': -40},
        '247': {'ext': 'webm', 'height': 720, 'format_note': 'DASH webm', 'preference': -40},
        '248': {'ext': 'webm', 'height': 1080, 'format_note': 'DASH webm', 'preference': -40},

        # Dash webm audio
        '171': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH webm audio', 'abr': 48, 'preference': -50},
        '172': {'ext': 'webm', 'vcodec': 'none', 'format_note': 'DASH webm audio', 'abr': 256, 'preference': -50},

        # RTMP (unnamed)
        '_rtmp': {'protocol': 'rtmp'},
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
                u"description": u"test chars:  \"'/\\ä↭𝕐\ntest URL: https://github.com/rg3/youtube-dl/issues/1892\n\nThis is a test video for youtube-dl.\n\nFor more information, contact phihag@phihag.de ."
            }
        },
        {
            u"url":  u"http://www.youtube.com/watch?v=UxxajLWwzqY",
            u"file":  u"UxxajLWwzqY.mp4",
            u"note": u"Test generic use_cipher_signature video (#897)",
            u"info_dict": {
                u"upload_date": u"20120506",
                u"title": u"Icona Pop - I Love It (feat. Charli XCX) [OFFICIAL VIDEO]",
                u"description": u"md5:5b292926389560516e384ac437c0ec07",
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
            u"url":  u"//www.YouTube.com/watch?v=yZIXLfi8CZQ",
            u"file":  u"yZIXLfi8CZQ.mp4",
            u"note": u"Embed-only video (#1746)",
            u"info_dict": {
                u"upload_date": u"20120608",
                u"title": u"Principal Sexually Assaults A Teacher - Episode 117 - 8th June 2012",
                u"description": u"md5:09b78bd971f1e3e289601dfba15ca4f7",
                u"uploader": u"SET India",
                u"uploader_id": u"setindia"
            }
        },
        {
            u"url": u"http://www.youtube.com/watch?v=a9LDPn-MO4I",
            u"file": u"a9LDPn-MO4I.m4a",
            u"note": u"256k DASH audio (format 141) via DASH manifest",
            u"info_dict": {
                u"upload_date": "20121002",
                u"uploader_id": "8KVIDEO",
                u"description": "No description available.",
                u"uploader": "8KVIDEO",
                u"title": "UHDTV TEST 8K VIDEO.mp4"
            },
            u"params": {
                u"youtube_include_dash_manifest": True,
                u"format": "141",
            },
        },
        # DASH manifest with encrypted signature
        {
            u'url': u'https://www.youtube.com/watch?v=IB3lcPjvWLA',
            u'info_dict': {
                u'id': u'IB3lcPjvWLA',
                u'ext': u'm4a',
                u'title': u'Afrojack - The Spark ft. Spree Wilson',
                u'description': u'md5:3199ed45ee8836572865580804d7ac0f',
                u'uploader': u'AfrojackVEVO',
                u'uploader_id': u'AfrojackVEVO',
                u'upload_date': u'20131011',
            },
            u"params": {
                u'youtube_include_dash_manifest': True,
                u'format': '141',
            },
        },
    ]


    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""
        if YoutubePlaylistIE.suitable(url): return False
        return re.match(cls._VALID_URL, url) is not None

    def __init__(self, *args, **kwargs):
        super(YoutubeIE, self).__init__(*args, **kwargs)
        self._player_cache = {}

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

    def _extract_signature_function(self, video_id, player_url, slen):
        id_m = re.match(r'.*-(?P<id>[a-zA-Z0-9_-]+)\.(?P<ext>[a-z]+)$',
                        player_url)
        player_type = id_m.group('ext')
        player_id = id_m.group('id')

        # Read from filesystem cache
        func_id = '%s_%s_%d' % (player_type, player_id, slen)
        assert os.path.basename(func_id) == func_id
        cache_dir = get_cachedir(self._downloader.params)

        cache_enabled = cache_dir is not None
        if cache_enabled:
            cache_fn = os.path.join(os.path.expanduser(cache_dir),
                                    u'youtube-sigfuncs',
                                    func_id + '.json')
            try:
                with io.open(cache_fn, 'r', encoding='utf-8') as cachef:
                    cache_spec = json.load(cachef)
                return lambda s: u''.join(s[i] for i in cache_spec)
            except IOError:
                pass  # No cache available

        if player_type == 'js':
            code = self._download_webpage(
                player_url, video_id,
                note=u'Downloading %s player %s' % (player_type, player_id),
                errnote=u'Download of %s failed' % player_url)
            res = self._parse_sig_js(code)
        elif player_type == 'swf':
            urlh = self._request_webpage(
                player_url, video_id,
                note=u'Downloading %s player %s' % (player_type, player_id),
                errnote=u'Download of %s failed' % player_url)
            code = urlh.read()
            res = self._parse_sig_swf(code)
        else:
            assert False, 'Invalid player type %r' % player_type

        if cache_enabled:
            try:
                test_string = u''.join(map(compat_chr, range(slen)))
                cache_res = res(test_string)
                cache_spec = [ord(c) for c in cache_res]
                try:
                    os.makedirs(os.path.dirname(cache_fn))
                except OSError as ose:
                    if ose.errno != errno.EEXIST:
                        raise
                write_json_file(cache_spec, cache_fn)
            except Exception:
                tb = traceback.format_exc()
                self._downloader.report_warning(
                    u'Writing cache to %r failed: %s' % (cache_fn, tb))

        return res

    def _print_sig_code(self, func, slen):
        def gen_sig_code(idxs):
            def _genslice(start, end, step):
                starts = u'' if start == 0 else str(start)
                ends = (u':%d' % (end+step)) if end + step >= 0 else u':'
                steps = u'' if step == 1 else (u':%d' % step)
                return u's[%s%s%s]' % (starts, ends, steps)

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
                    yield u's[%d]' % prev
            if step is None:
                yield u's[%d]' % i
            else:
                yield _genslice(start, i, step)

        test_string = u''.join(map(compat_chr, range(slen)))
        cache_res = func(test_string)
        cache_spec = [ord(c) for c in cache_res]
        expr_code = u' + '.join(gen_sig_code(cache_spec))
        code = u'if len(s) == %d:\n    return %s\n' % (slen, expr_code)
        self.to_screen(u'Extracted signature function:\n' + code)

    def _parse_sig_js(self, jscode):
        funcname = self._search_regex(
            r'signature=([a-zA-Z]+)', jscode,
            u'Initial JS player signature function name')

        functions = {}

        def argidx(varname):
            return string.lowercase.index(varname)

        def interpret_statement(stmt, local_vars, allow_recursion=20):
            if allow_recursion < 0:
                raise ExtractorError(u'Recursion limit reached')

            if stmt.startswith(u'var '):
                stmt = stmt[len(u'var '):]
            ass_m = re.match(r'^(?P<out>[a-z]+)(?:\[(?P<index>[^\]]+)\])?' +
                             r'=(?P<expr>.*)$', stmt)
            if ass_m:
                if ass_m.groupdict().get('index'):
                    def assign(val):
                        lvar = local_vars[ass_m.group('out')]
                        idx = interpret_expression(ass_m.group('index'),
                                                   local_vars, allow_recursion)
                        assert isinstance(idx, int)
                        lvar[idx] = val
                        return val
                    expr = ass_m.group('expr')
                else:
                    def assign(val):
                        local_vars[ass_m.group('out')] = val
                        return val
                    expr = ass_m.group('expr')
            elif stmt.startswith(u'return '):
                assign = lambda v: v
                expr = stmt[len(u'return '):]
            else:
                raise ExtractorError(
                    u'Cannot determine left side of statement in %r' % stmt)

            v = interpret_expression(expr, local_vars, allow_recursion)
            return assign(v)

        def interpret_expression(expr, local_vars, allow_recursion):
            if expr.isdigit():
                return int(expr)

            if expr.isalpha():
                return local_vars[expr]

            m = re.match(r'^(?P<in>[a-z]+)\.(?P<member>.*)$', expr)
            if m:
                member = m.group('member')
                val = local_vars[m.group('in')]
                if member == 'split("")':
                    return list(val)
                if member == 'join("")':
                    return u''.join(val)
                if member == 'length':
                    return len(val)
                if member == 'reverse()':
                    return val[::-1]
                slice_m = re.match(r'slice\((?P<idx>.*)\)', member)
                if slice_m:
                    idx = interpret_expression(
                        slice_m.group('idx'), local_vars, allow_recursion-1)
                    return val[idx:]

            m = re.match(
                r'^(?P<in>[a-z]+)\[(?P<idx>.+)\]$', expr)
            if m:
                val = local_vars[m.group('in')]
                idx = interpret_expression(m.group('idx'), local_vars,
                                           allow_recursion-1)
                return val[idx]

            m = re.match(r'^(?P<a>.+?)(?P<op>[%])(?P<b>.+?)$', expr)
            if m:
                a = interpret_expression(m.group('a'),
                                         local_vars, allow_recursion)
                b = interpret_expression(m.group('b'),
                                         local_vars, allow_recursion)
                return a % b

            m = re.match(
                r'^(?P<func>[a-zA-Z$]+)\((?P<args>[a-z0-9,]+)\)$', expr)
            if m:
                fname = m.group('func')
                if fname not in functions:
                    functions[fname] = extract_function(fname)
                argvals = [int(v) if v.isdigit() else local_vars[v]
                           for v in m.group('args').split(',')]
                return functions[fname](argvals)
            raise ExtractorError(u'Unsupported JS expression %r' % expr)

        def extract_function(funcname):
            func_m = re.search(
                r'function ' + re.escape(funcname) +
                r'\((?P<args>[a-z,]+)\){(?P<code>[^}]+)}',
                jscode)
            argnames = func_m.group('args').split(',')

            def resf(args):
                local_vars = dict(zip(argnames, args))
                for stmt in func_m.group('code').split(';'):
                    res = interpret_statement(stmt, local_vars)
                return res
            return resf

        initial_function = extract_function(funcname)
        return lambda s: initial_function([s])

    def _parse_sig_swf(self, file_contents):
        if file_contents[1:3] != b'WS':
            raise ExtractorError(
                u'Not an SWF file; header is %r' % file_contents[:3])
        if file_contents[:1] == b'C':
            content = zlib.decompress(file_contents[8:])
        else:
            raise NotImplementedError(u'Unsupported compression format %r' %
                                      file_contents[:1])

        def extract_tags(content):
            pos = 0
            while pos < len(content):
                header16 = struct.unpack('<H', content[pos:pos+2])[0]
                pos += 2
                tag_code = header16 >> 6
                tag_len = header16 & 0x3f
                if tag_len == 0x3f:
                    tag_len = struct.unpack('<I', content[pos:pos+4])[0]
                    pos += 4
                assert pos+tag_len <= len(content)
                yield (tag_code, content[pos:pos+tag_len])
                pos += tag_len

        code_tag = next(tag
                        for tag_code, tag in extract_tags(content)
                        if tag_code == 82)
        p = code_tag.index(b'\0', 4) + 1
        code_reader = io.BytesIO(code_tag[p:])

        # Parse ABC (AVM2 ByteCode)
        def read_int(reader=None):
            if reader is None:
                reader = code_reader
            res = 0
            shift = 0
            for _ in range(5):
                buf = reader.read(1)
                assert len(buf) == 1
                b = struct.unpack('<B', buf)[0]
                res = res | ((b & 0x7f) << shift)
                if b & 0x80 == 0:
                    break
                shift += 7
            return res

        def u30(reader=None):
            res = read_int(reader)
            assert res & 0xf0000000 == 0
            return res
        u32 = read_int

        def s32(reader=None):
            v = read_int(reader)
            if v & 0x80000000 != 0:
                v = - ((v ^ 0xffffffff) + 1)
            return v

        def read_string(reader=None):
            if reader is None:
                reader = code_reader
            slen = u30(reader)
            resb = reader.read(slen)
            assert len(resb) == slen
            return resb.decode('utf-8')

        def read_bytes(count, reader=None):
            if reader is None:
                reader = code_reader
            resb = reader.read(count)
            assert len(resb) == count
            return resb

        def read_byte(reader=None):
            resb = read_bytes(1, reader=reader)
            res = struct.unpack('<B', resb)[0]
            return res

        # minor_version + major_version
        read_bytes(2 + 2)

        # Constant pool
        int_count = u30()
        for _c in range(1, int_count):
            s32()
        uint_count = u30()
        for _c in range(1, uint_count):
            u32()
        double_count = u30()
        read_bytes((double_count-1) * 8)
        string_count = u30()
        constant_strings = [u'']
        for _c in range(1, string_count):
            s = read_string()
            constant_strings.append(s)
        namespace_count = u30()
        for _c in range(1, namespace_count):
            read_bytes(1)  # kind
            u30()  # name
        ns_set_count = u30()
        for _c in range(1, ns_set_count):
            count = u30()
            for _c2 in range(count):
                u30()
        multiname_count = u30()
        MULTINAME_SIZES = {
            0x07: 2,  # QName
            0x0d: 2,  # QNameA
            0x0f: 1,  # RTQName
            0x10: 1,  # RTQNameA
            0x11: 0,  # RTQNameL
            0x12: 0,  # RTQNameLA
            0x09: 2,  # Multiname
            0x0e: 2,  # MultinameA
            0x1b: 1,  # MultinameL
            0x1c: 1,  # MultinameLA
        }
        multinames = [u'']
        for _c in range(1, multiname_count):
            kind = u30()
            assert kind in MULTINAME_SIZES, u'Invalid multiname kind %r' % kind
            if kind == 0x07:
                u30()  # namespace_idx
                name_idx = u30()
                multinames.append(constant_strings[name_idx])
            else:
                multinames.append('[MULTINAME kind: %d]' % kind)
                for _c2 in range(MULTINAME_SIZES[kind]):
                    u30()

        # Methods
        method_count = u30()
        MethodInfo = collections.namedtuple(
            'MethodInfo',
            ['NEED_ARGUMENTS', 'NEED_REST'])
        method_infos = []
        for method_id in range(method_count):
            param_count = u30()
            u30()  # return type
            for _ in range(param_count):
                u30()  # param type
            u30()  # name index (always 0 for youtube)
            flags = read_byte()
            if flags & 0x08 != 0:
                # Options present
                option_count = u30()
                for c in range(option_count):
                    u30()  # val
                    read_bytes(1)  # kind
            if flags & 0x80 != 0:
                # Param names present
                for _ in range(param_count):
                    u30()  # param name
            mi = MethodInfo(flags & 0x01 != 0, flags & 0x04 != 0)
            method_infos.append(mi)

        # Metadata
        metadata_count = u30()
        for _c in range(metadata_count):
            u30()  # name
            item_count = u30()
            for _c2 in range(item_count):
                u30()  # key
                u30()  # value

        def parse_traits_info():
            trait_name_idx = u30()
            kind_full = read_byte()
            kind = kind_full & 0x0f
            attrs = kind_full >> 4
            methods = {}
            if kind in [0x00, 0x06]:  # Slot or Const
                u30()  # Slot id
                u30()  # type_name_idx
                vindex = u30()
                if vindex != 0:
                    read_byte()  # vkind
            elif kind in [0x01, 0x02, 0x03]:  # Method / Getter / Setter
                u30()  # disp_id
                method_idx = u30()
                methods[multinames[trait_name_idx]] = method_idx
            elif kind == 0x04:  # Class
                u30()  # slot_id
                u30()  # classi
            elif kind == 0x05:  # Function
                u30()  # slot_id
                function_idx = u30()
                methods[function_idx] = multinames[trait_name_idx]
            else:
                raise ExtractorError(u'Unsupported trait kind %d' % kind)

            if attrs & 0x4 != 0:  # Metadata present
                metadata_count = u30()
                for _c3 in range(metadata_count):
                    u30()  # metadata index

            return methods

        # Classes
        TARGET_CLASSNAME = u'SignatureDecipher'
        searched_idx = multinames.index(TARGET_CLASSNAME)
        searched_class_id = None
        class_count = u30()
        for class_id in range(class_count):
            name_idx = u30()
            if name_idx == searched_idx:
                # We found the class we're looking for!
                searched_class_id = class_id
            u30()  # super_name idx
            flags = read_byte()
            if flags & 0x08 != 0:  # Protected namespace is present
                u30()  # protected_ns_idx
            intrf_count = u30()
            for _c2 in range(intrf_count):
                u30()
            u30()  # iinit
            trait_count = u30()
            for _c2 in range(trait_count):
                parse_traits_info()

        if searched_class_id is None:
            raise ExtractorError(u'Target class %r not found' %
                                 TARGET_CLASSNAME)

        method_names = {}
        method_idxs = {}
        for class_id in range(class_count):
            u30()  # cinit
            trait_count = u30()
            for _c2 in range(trait_count):
                trait_methods = parse_traits_info()
                if class_id == searched_class_id:
                    method_names.update(trait_methods.items())
                    method_idxs.update(dict(
                        (idx, name)
                        for name, idx in trait_methods.items()))

        # Scripts
        script_count = u30()
        for _c in range(script_count):
            u30()  # init
            trait_count = u30()
            for _c2 in range(trait_count):
                parse_traits_info()

        # Method bodies
        method_body_count = u30()
        Method = collections.namedtuple('Method', ['code', 'local_count'])
        methods = {}
        for _c in range(method_body_count):
            method_idx = u30()
            u30()  # max_stack
            local_count = u30()
            u30()  # init_scope_depth
            u30()  # max_scope_depth
            code_length = u30()
            code = read_bytes(code_length)
            if method_idx in method_idxs:
                m = Method(code, local_count)
                methods[method_idxs[method_idx]] = m
            exception_count = u30()
            for _c2 in range(exception_count):
                u30()  # from
                u30()  # to
                u30()  # target
                u30()  # exc_type
                u30()  # var_name
            trait_count = u30()
            for _c2 in range(trait_count):
                parse_traits_info()

        assert p + code_reader.tell() == len(code_tag)
        assert len(methods) == len(method_idxs)

        method_pyfunctions = {}

        def extract_function(func_name):
            if func_name in method_pyfunctions:
                return method_pyfunctions[func_name]
            if func_name not in methods:
                raise ExtractorError(u'Cannot find function %r' % func_name)
            m = methods[func_name]

            def resfunc(args):
                registers = ['(this)'] + list(args) + [None] * m.local_count
                stack = []
                coder = io.BytesIO(m.code)
                while True:
                    opcode = struct.unpack('!B', coder.read(1))[0]
                    if opcode == 36:  # pushbyte
                        v = struct.unpack('!B', coder.read(1))[0]
                        stack.append(v)
                    elif opcode == 44:  # pushstring
                        idx = u30(coder)
                        stack.append(constant_strings[idx])
                    elif opcode == 48:  # pushscope
                        # We don't implement the scope register, so we'll just
                        # ignore the popped value
                        stack.pop()
                    elif opcode == 70:  # callproperty
                        index = u30(coder)
                        mname = multinames[index]
                        arg_count = u30(coder)
                        args = list(reversed(
                            [stack.pop() for _ in range(arg_count)]))
                        obj = stack.pop()
                        if mname == u'split':
                            assert len(args) == 1
                            assert isinstance(args[0], compat_str)
                            assert isinstance(obj, compat_str)
                            if args[0] == u'':
                                res = list(obj)
                            else:
                                res = obj.split(args[0])
                            stack.append(res)
                        elif mname == u'slice':
                            assert len(args) == 1
                            assert isinstance(args[0], int)
                            assert isinstance(obj, list)
                            res = obj[args[0]:]
                            stack.append(res)
                        elif mname == u'join':
                            assert len(args) == 1
                            assert isinstance(args[0], compat_str)
                            assert isinstance(obj, list)
                            res = args[0].join(obj)
                            stack.append(res)
                        elif mname in method_pyfunctions:
                            stack.append(method_pyfunctions[mname](args))
                        else:
                            raise NotImplementedError(
                                u'Unsupported property %r on %r'
                                % (mname, obj))
                    elif opcode == 72:  # returnvalue
                        res = stack.pop()
                        return res
                    elif opcode == 79:  # callpropvoid
                        index = u30(coder)
                        mname = multinames[index]
                        arg_count = u30(coder)
                        args = list(reversed(
                            [stack.pop() for _ in range(arg_count)]))
                        obj = stack.pop()
                        if mname == u'reverse':
                            assert isinstance(obj, list)
                            obj.reverse()
                        else:
                            raise NotImplementedError(
                                u'Unsupported (void) property %r on %r'
                                % (mname, obj))
                    elif opcode == 93:  # findpropstrict
                        index = u30(coder)
                        mname = multinames[index]
                        res = extract_function(mname)
                        stack.append(res)
                    elif opcode == 97:  # setproperty
                        index = u30(coder)
                        value = stack.pop()
                        idx = stack.pop()
                        obj = stack.pop()
                        assert isinstance(obj, list)
                        assert isinstance(idx, int)
                        obj[idx] = value
                    elif opcode == 98:  # getlocal
                        index = u30(coder)
                        stack.append(registers[index])
                    elif opcode == 99:  # setlocal
                        index = u30(coder)
                        value = stack.pop()
                        registers[index] = value
                    elif opcode == 102:  # getproperty
                        index = u30(coder)
                        pname = multinames[index]
                        if pname == u'length':
                            obj = stack.pop()
                            assert isinstance(obj, list)
                            stack.append(len(obj))
                        else:  # Assume attribute access
                            idx = stack.pop()
                            assert isinstance(idx, int)
                            obj = stack.pop()
                            assert isinstance(obj, list)
                            stack.append(obj[idx])
                    elif opcode == 128:  # coerce
                        u30(coder)
                    elif opcode == 133:  # coerce_s
                        assert isinstance(stack[-1], (type(None), compat_str))
                    elif opcode == 164:  # modulo
                        value2 = stack.pop()
                        value1 = stack.pop()
                        res = value1 % value2
                        stack.append(res)
                    elif opcode == 208:  # getlocal_0
                        stack.append(registers[0])
                    elif opcode == 209:  # getlocal_1
                        stack.append(registers[1])
                    elif opcode == 210:  # getlocal_2
                        stack.append(registers[2])
                    elif opcode == 211:  # getlocal_3
                        stack.append(registers[3])
                    elif opcode == 214:  # setlocal_2
                        registers[2] = stack.pop()
                    elif opcode == 215:  # setlocal_3
                        registers[3] = stack.pop()
                    else:
                        raise NotImplementedError(
                            u'Unsupported opcode %d' % opcode)

            method_pyfunctions[func_name] = resfunc
            return resfunc

        initial_function = extract_function(u'decipher')
        return lambda s: initial_function([s])

    def _decrypt_signature(self, s, video_id, player_url, age_gate=False):
        """Turn the encrypted s field into a working signature"""

        if player_url is not None:
            if player_url.startswith(u'//'):
                player_url = u'https:' + player_url
            try:
                player_id = (player_url, len(s))
                if player_id not in self._player_cache:
                    func = self._extract_signature_function(
                        video_id, player_url, len(s)
                    )
                    self._player_cache[player_id] = func
                func = self._player_cache[player_id]
                if self._downloader.params.get('youtube_print_sig_code'):
                    self._print_sig_code(func, len(s))
                return func(s)
            except Exception:
                tb = traceback.format_exc()
                self._downloader.report_warning(
                    u'Automatic signature extraction failed: ' + tb)

            self._downloader.report_warning(
                u'Warning: Falling back to static signature algorithm')

        return self._static_decrypt_signature(
            s, video_id, player_url, age_gate)

    def _static_decrypt_signature(self, s, video_id, player_url, age_gate):
        if age_gate:
            # The videos with age protection use another player, so the
            # algorithms can be different.
            if len(s) == 86:
                return s[2:63] + s[82] + s[64:82] + s[63]

        if len(s) == 93:
            return s[86:29:-1] + s[88] + s[28:5:-1]
        elif len(s) == 92:
            return s[25] + s[3:25] + s[0] + s[26:42] + s[79] + s[43:79] + s[91] + s[80:83]
        elif len(s) == 91:
            return s[84:27:-1] + s[86] + s[26:5:-1]
        elif len(s) == 90:
            return s[25] + s[3:25] + s[2] + s[26:40] + s[77] + s[41:77] + s[89] + s[78:81]
        elif len(s) == 89:
            return s[84:78:-1] + s[87] + s[77:60:-1] + s[0] + s[59:3:-1]
        elif len(s) == 88:
            return s[7:28] + s[87] + s[29:45] + s[55] + s[46:55] + s[2] + s[56:87] + s[28]
        elif len(s) == 87:
            return s[6:27] + s[4] + s[28:39] + s[27] + s[40:59] + s[2] + s[60:]
        elif len(s) == 86:
            return s[80:72:-1] + s[16] + s[71:39:-1] + s[72] + s[38:16:-1] + s[82] + s[15::-1]
        elif len(s) == 85:
            return s[3:11] + s[0] + s[12:55] + s[84] + s[56:84]
        elif len(s) == 84:
            return s[78:70:-1] + s[14] + s[69:37:-1] + s[70] + s[36:14:-1] + s[80] + s[:14][::-1]
        elif len(s) == 83:
            return s[80:63:-1] + s[0] + s[62:0:-1] + s[63]
        elif len(s) == 82:
            return s[80:37:-1] + s[7] + s[36:7:-1] + s[0] + s[6:0:-1] + s[37]
        elif len(s) == 81:
            return s[56] + s[79:56:-1] + s[41] + s[55:41:-1] + s[80] + s[40:34:-1] + s[0] + s[33:29:-1] + s[34] + s[28:9:-1] + s[29] + s[8:0:-1] + s[9]
        elif len(s) == 80:
            return s[1:19] + s[0] + s[20:68] + s[19] + s[69:80]
        elif len(s) == 79:
            return s[54] + s[77:54:-1] + s[39] + s[53:39:-1] + s[78] + s[38:34:-1] + s[0] + s[33:29:-1] + s[34] + s[28:9:-1] + s[29] + s[8:0:-1] + s[9]

        else:
            raise ExtractorError(u'Unable to decrypt signature, key length %d not supported; retrying might work' % (len(s)))

    def _get_available_subtitles(self, video_id, webpage):
        try:
            sub_list = self._download_webpage(
                'https://video.google.com/timedtext?hl=en&type=list&v=%s' % video_id,
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
                'fmt': self._downloader.params.get('subtitlesformat', 'srt'),
                'name': unescapeHTML(l[0]).encode('utf-8'),
            })
            url = u'https://www.youtube.com/api/timedtext?' + params
            sub_lang_list[lang] = url
        if not sub_lang_list:
            self._downloader.report_warning(u'video doesn\'t have subtitles')
            return {}
        return sub_lang_list

    def _get_available_automatic_caption(self, video_id, webpage):
        """We need the webpage for getting the captions url, pass it as an
           argument to speed up the process."""
        sub_format = self._downloader.params.get('subtitlesformat', 'srt')
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
            caption_list = self._download_xml(list_url, video_id)
            original_lang_node = caption_list.find('track')
            if original_lang_node is None or original_lang_node.attrib.get('kind') != 'asr' :
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

    @classmethod
    def extract_id(cls, url):
        mobj = re.match(cls._VALID_URL, url, re.VERBOSE)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group(2)
        return video_id

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

    def _extract_annotations(self, video_id):
        url = 'https://www.youtube.com/annotations_invideo?features=1&legacy=1&video_id=%s' % video_id
        return self._download_webpage(url, video_id, note=u'Searching for annotations.', errnote=u'Unable to download video annotations.')

    def _real_extract(self, url):
        proto = (
            u'http' if self._downloader.params.get('prefer_insecure', False)
            else u'https')

        # Extract original video URL from URL with redirection, like age verification, using next_url parameter
        mobj = re.search(self._NEXT_URL_RE, url)
        if mobj:
            url = proto + '://www.youtube.com/' + compat_urllib_parse.unquote(mobj.group(1)).lstrip('/')
        video_id = self.extract_id(url)

        # Get video webpage
        url = proto + '://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1' % video_id
        video_webpage = self._download_webpage(url, video_id)

        # Attempt to extract SWF player URL
        mobj = re.search(r'swfConfig.*?"(https?:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
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
                                                  'el': 'player_embedded',
                                                  'gl': 'US',
                                                  'hl': 'en',
                                                  'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                                                  'asv': 3,
                                                  'sts':'1588',
                                                  })
            video_info_url = proto + '://www.youtube.com/get_video_info?' + data
            video_info_webpage = self._download_webpage(video_info_url, video_id,
                                    note=False,
                                    errnote='unable to download video info webpage')
            video_info = compat_parse_qs(video_info_webpage)
        else:
            age_gate = False
            for el_type in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
                video_info_url = (proto + '://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en'
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

        if 'view_count' in video_info:
            view_count = int(video_info['view_count'][0])
        else:
            view_count = None

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
        if 'title' in video_info:
            video_title = compat_urllib_parse.unquote_plus(video_info['title'][0])
        else:
            self._downloader.report_warning(u'Unable to extract video title')
            video_title = u'_'

        # thumbnail image
        # We try first to get a high quality image:
        m_thumb = re.search(r'<span itemprop="thumbnail".*?href="(.*?)">',
                            video_webpage, re.DOTALL)
        if m_thumb is not None:
            video_thumbnail = m_thumb.group(1)
        elif 'thumbnail_url' not in video_info:
            self._downloader.report_warning(u'unable to extract video thumbnail')
            video_thumbnail = None
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
                video_description = u''

        def _extract_count(klass):
            count = self._search_regex(
                r'class="%s">([\d,]+)</span>' % re.escape(klass),
                video_webpage, klass, default=None)
            if count is not None:
                return int(count.replace(',', ''))
            return None
        like_count = _extract_count(u'likes-count')
        dislike_count = _extract_count(u'dislikes-count')

        # subtitles
        video_subtitles = self.extract_subtitles(video_id, video_webpage)

        if self._downloader.params.get('listsubtitles', False):
            self._list_available_subtitles(video_id, video_webpage)
            return

        if 'length_seconds' not in video_info:
            self._downloader.report_warning(u'unable to extract video duration')
            video_duration = None
        else:
            video_duration = int(compat_urllib_parse.unquote_plus(video_info['length_seconds'][0]))

        # annotations
        video_annotations = None
        if self._downloader.params.get('writeannotations', False):
                video_annotations = self._extract_annotations(video_id)

        # Decide which formats to download
        try:
            mobj = re.search(r';ytplayer\.config\s*=\s*({.*?});', video_webpage)
            if not mobj:
                raise ValueError('Could not find vevo ID')
            json_code = uppercase_escape(mobj.group(1))
            ytplayer_config = json.loads(json_code)
            args = ytplayer_config['args']
            # Easy way to know if the 's' value is in url_encoded_fmt_stream_map
            # this signatures are encrypted
            if 'url_encoded_fmt_stream_map' not in args:
                raise ValueError(u'No stream_map present')  # caught below
            re_signature = re.compile(r'[&,]s=')
            m_s = re_signature.search(args['url_encoded_fmt_stream_map'])
            if m_s is not None:
                self.to_screen(u'%s: Encrypted signatures detected.' % video_id)
                video_info['url_encoded_fmt_stream_map'] = [args['url_encoded_fmt_stream_map']]
            m_s = re_signature.search(args.get('adaptive_fmts', u''))
            if m_s is not None:
                if 'adaptive_fmts' in video_info:
                    video_info['adaptive_fmts'][0] += ',' + args['adaptive_fmts']
                else:
                    video_info['adaptive_fmts'] = [args['adaptive_fmts']]
        except ValueError:
            pass

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
            encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + video_info.get('adaptive_fmts',[''])[0]
            if 'rtmpe%3Dyes' in encoded_url_map:
                raise ExtractorError('rtmpe downloads are not supported, see https://github.com/rg3/youtube-dl/issues/343 for more information.', expected=True)
            url_map = {}
            for url_data_str in encoded_url_map.split(','):
                url_data = compat_parse_qs(url_data_str)
                if 'itag' in url_data and 'url' in url_data:
                    url = url_data['url'][0]
                    if 'sig' in url_data:
                        url += '&signature=' + url_data['sig'][0]
                    elif 's' in url_data:
                        encrypted_sig = url_data['s'][0]
                        if self._downloader.params.get('verbose'):
                            if age_gate:
                                if player_url is None:
                                    player_version = 'unknown'
                                else:
                                    player_version = self._search_regex(
                                        r'-(.+)\.swf$', player_url,
                                        u'flash player', fatal=False)
                                player_desc = 'flash player %s' % player_version
                            else:
                                player_version = self._search_regex(
                                    r'html5player-(.+?)\.js', video_webpage,
                                    'html5 player', fatal=False)
                                player_desc = u'html5 player %s' % player_version

                            parts_sizes = u'.'.join(compat_str(len(part)) for part in encrypted_sig.split('.'))
                            self.to_screen(u'encrypted signature length %d (%s), itag %s, %s' %
                                (len(encrypted_sig), parts_sizes, url_data['itag'][0], player_desc))

                        if not age_gate:
                            jsplayer_url_json = self._search_regex(
                                r'"assets":.+?"js":\s*("[^"]+")',
                                video_webpage, u'JS player URL')
                            player_url = json.loads(jsplayer_url_json)

                        signature = self._decrypt_signature(
                            encrypted_sig, video_id, player_url, age_gate)
                        url += '&signature=' + signature
                    if 'ratebypass' not in url:
                        url += '&ratebypass=yes'
                    url_map[url_data['itag'][0]] = url
            formats = _map_to_format_list(url_map)
        elif video_info.get('hlsvp'):
            manifest_url = video_info['hlsvp'][0]
            url_map = self._extract_from_m3u8(manifest_url, video_id)
            formats = _map_to_format_list(url_map)
        else:
            raise ExtractorError(u'no conn, hlsvp or url_encoded_fmt_stream_map information found in video info')

        # Look for the DASH manifest
        if (self._downloader.params.get('youtube_include_dash_manifest', False)):
            try:
                # The DASH manifest used needs to be the one from the original video_webpage.
                # The one found in get_video_info seems to be using different signatures.
                # However, in the case of an age restriction there won't be any embedded dashmpd in the video_webpage.
                # Luckily, it seems, this case uses some kind of default signature (len == 86), so the
                # combination of get_video_info and the _static_decrypt_signature() decryption fallback will work here.
                if age_gate:
                    dash_manifest_url = video_info.get('dashmpd')[0]
                else:
                    dash_manifest_url = ytplayer_config['args']['dashmpd']
                def decrypt_sig(mobj):
                    s = mobj.group(1)
                    dec_s = self._decrypt_signature(s, video_id, player_url, age_gate)
                    return '/signature/%s' % dec_s
                dash_manifest_url = re.sub(r'/s/([\w\.]+)', decrypt_sig, dash_manifest_url)
                dash_doc = self._download_xml(
                    dash_manifest_url, video_id,
                    note=u'Downloading DASH manifest',
                    errnote=u'Could not download DASH manifest')
                for r in dash_doc.findall(u'.//{urn:mpeg:DASH:schema:MPD:2011}Representation'):
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

            except (ExtractorError, KeyError) as e:
                self.report_warning(u'Skipping DASH manifest: %s' % e, video_id)

        self._sort_formats(formats)

        return {
            'id':           video_id,
            'uploader':     video_uploader,
            'uploader_id':  video_uploader_id,
            'upload_date':  upload_date,
            'title':        video_title,
            'thumbnail':    video_thumbnail,
            'description':  video_description,
            'subtitles':    video_subtitles,
            'duration':     video_duration,
            'age_limit':    18 if age_gate else 0,
            'annotations':  video_annotations,
            'webpage_url': proto + '://www.youtube.com/watch?v=%s' % video_id,
            'view_count':   view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'formats':      formats,
        }

class YoutubePlaylistIE(YoutubeBaseInfoExtractor):
    IE_DESC = u'YouTube.com playlists'
    _VALID_URL = r"""(?x)(?:
                        (?:https?://)?
                        (?:\w+\.)?
                        youtube\.com/
                        (?:
                           (?:course|view_play_list|my_playlists|artist|playlist|watch)
                           \? (?:.*?&)*? (?:p|a|list)=
                        |  p/
                        )
                        (
                            (?:PL|EC|UU|FL|RD)?[0-9A-Za-z-_]{10,}
                            # Top tracks, they can also include dots 
                            |(?:MC)[\w\.]*
                        )
                        .*
                     |
                        ((?:PL|EC|UU|FL|RD)[0-9A-Za-z-_]{10,})
                     )"""
    _TEMPLATE_URL = 'https://www.youtube.com/playlist?list=%s'
    _MORE_PAGES_INDICATOR = r'data-link-type="next"'
    _VIDEO_RE = r'href="\s*/watch\?v=(?P<id>[0-9A-Za-z_-]{11})&amp;[^"]*?index=(?P<index>\d+)'
    IE_NAME = u'youtube:playlist'

    def _real_initialize(self):
        self._login()

    def _ids_to_results(self, ids):
        return [self.url_result(vid_id, 'Youtube', video_id=vid_id)
                       for vid_id in ids]

    def _extract_mix(self, playlist_id):
        # The mixes are generated from a a single video
        # the id of the playlist is just 'RD' + video_id
        url = 'https://youtube.com/watch?v=%s&list=%s' % (playlist_id[-11:], playlist_id)
        webpage = self._download_webpage(url, playlist_id, u'Downloading Youtube mix')
        search_title = lambda class_name: get_element_by_attribute('class', class_name, webpage)
        title_span = (search_title('playlist-title') or
            search_title('title long-title') or search_title('title'))
        title = clean_html(title_span)
        video_re = r'''(?x)data-video-username="(.*?)".*?
                       href="/watch\?v=([0-9A-Za-z_-]{11})&amp;[^"]*?list=%s''' % re.escape(playlist_id)
        matches = orderedSet(re.findall(video_re, webpage, flags=re.DOTALL))
        # Some of the videos may have been deleted, their username field is empty
        ids = [video_id for (username, video_id) in matches if username]
        url_results = self._ids_to_results(ids)

        return self.playlist_result(url_results, playlist_id, title)

    def _real_extract(self, url):
        # Extract playlist id
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        playlist_id = mobj.group(1) or mobj.group(2)

        # Check if it's a video-specific URL
        query_dict = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        if 'v' in query_dict:
            video_id = query_dict['v'][0]
            if self._downloader.params.get('noplaylist'):
                self.to_screen(u'Downloading just video %s because of --no-playlist' % video_id)
                return self.url_result(video_id, 'Youtube', video_id=video_id)
            else:
                self.to_screen(u'Downloading playlist PL%s - add --no-playlist to just download video %s' % (playlist_id, video_id))

        if playlist_id.startswith('RD'):
            # Mixes require a custom extraction process
            return self._extract_mix(playlist_id)
        if playlist_id.startswith('TL'):
            raise ExtractorError(u'For downloading YouTube.com top lists, use '
                u'the "yttoplist" keyword, for example "youtube-dl \'yttoplist:music:Top Tracks\'"', expected=True)

        url = self._TEMPLATE_URL % playlist_id
        page = self._download_webpage(url, playlist_id)
        more_widget_html = content_html = page

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
                'https://youtube.com/%s' % mobj.group('more'), playlist_id, 'Downloading page #%s' % page_num)
            content_html = more['content_html']
            more_widget_html = more['load_more_widget_html']

        playlist_title = self._html_search_regex(
                r'<h1 class="pl-header-title">\s*(.*?)\s*</h1>', page, u'title')

        url_results = self._ids_to_results(ids)
        return self.playlist_result(url_results, playlist_id, playlist_title)


class YoutubeTopListIE(YoutubePlaylistIE):
    IE_NAME = u'youtube:toplist'
    IE_DESC = (u'YouTube.com top lists, "yttoplist:{channel}:{list title}"'
        u' (Example: "yttoplist:music:Top Tracks")')
    _VALID_URL = r'yttoplist:(?P<chann>.*?):(?P<title>.*?)$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel = mobj.group('chann')
        title = mobj.group('title')
        query = compat_urllib_parse.urlencode({'title': title})
        playlist_re = 'href="([^"]+?%s.*?)"' % re.escape(query)
        channel_page = self._download_webpage('https://www.youtube.com/%s' % channel, title)
        link = self._html_search_regex(playlist_re, channel_page, u'list')
        url = compat_urlparse.urljoin('https://www.youtube.com/', link)
        
        video_re = r'data-index="\d+".*?data-video-id="([0-9A-Za-z_-]{11})"'
        ids = []
        # sometimes the webpage doesn't contain the videos
        # retry until we get them
        for i in itertools.count(0):
            msg = u'Downloading Youtube mix'
            if i > 0:
                msg += ', retry #%d' % i
            webpage = self._download_webpage(url, title, msg)
            ids = orderedSet(re.findall(video_re, webpage))
            if ids:
                break
        url_results = self._ids_to_results(ids)
        return self.playlist_result(url_results, playlist_title=title)


class YoutubeChannelIE(InfoExtractor):
    IE_DESC = u'YouTube.com channels'
    _VALID_URL = r"^(?:https?://)?(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie)?\.com)/channel/([0-9A-Za-z_-]+)"
    _MORE_PAGES_INDICATOR = 'yt-uix-load-more'
    _MORE_PAGES_URL = 'https://www.youtube.com/c4_browse_ajax?action_load_more_videos=1&flow=list&paging=%s&view=0&sort=da&channel_id=%s'
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
        else:
            # Download all channel pages using the json-based channel_ajax query
            for pagenum in itertools.count(1):
                url = self._MORE_PAGES_URL % (pagenum, channel_id)
                page = self._download_json(
                    url, channel_id, note=u'Downloading page #%s' % pagenum,
                    transform_source=uppercase_escape)

                ids_in_page = self.extract_videos_from_page(page['content_html'])
                video_ids.extend(ids_in_page)
    
                if self._MORE_PAGES_INDICATOR not in page['load_more_widget_html']:
                    break

        self._downloader.to_screen(u'[youtube] Channel %s: Found %i videos' % (channel_id, len(video_ids)))

        url_entries = [self.url_result(video_id, 'Youtube', video_id=video_id)
                       for video_id in video_ids]
        return self.playlist_result(url_entries, channel_id)


class YoutubeUserIE(InfoExtractor):
    IE_DESC = u'YouTube.com user videos (URL or "ytuser" keyword)'
    _VALID_URL = r'(?:(?:(?:https?://)?(?:\w+\.)?youtube\.com/(?:user/)?(?!(?:attribution_link|watch|results)(?:$|[^a-z_A-Z0-9-])))|ytuser:)(?!feed/)([A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'https://gdata.youtube.com/feeds/api/users/%s'
    _GDATA_PAGE_SIZE = 50
    _GDATA_URL = 'https://gdata.youtube.com/feeds/api/users/%s/uploads?max-results=%d&start-index=%d&alt=json'
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

        def download_page(pagenum):
            start_index = pagenum * self._GDATA_PAGE_SIZE + 1

            gdata_url = self._GDATA_URL % (username, self._GDATA_PAGE_SIZE, start_index)
            page = self._download_webpage(
                gdata_url, username,
                u'Downloading video ids from %d to %d' % (
                    start_index, start_index + self._GDATA_PAGE_SIZE))

            try:
                response = json.loads(page)
            except ValueError as err:
                raise ExtractorError(u'Invalid JSON in API response: ' + compat_str(err))
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
        url_results = PagedList(download_page, self._GDATA_PAGE_SIZE)

        return self.playlist_result(url_results, playlist_title=username)


class YoutubeSearchIE(SearchInfoExtractor):
    IE_DESC = u'YouTube.com searches'
    _API_URL = 'https://gdata.youtube.com/feeds/api/videos?q=%s&start-index=%i&max-results=50&v=2&alt=jsonc'
    _MAX_RESULTS = 1000
    IE_NAME = u'youtube:search'
    _SEARCH_KEY = 'ytsearch'

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        video_ids = []
        pagenum = 0
        limit = n

        while (50 * pagenum) < limit:
            result_url = self._API_URL % (compat_urllib_parse.quote_plus(query), (50*pagenum)+1)
            data_json = self._download_webpage(
                result_url, video_id=u'query "%s"' % query,
                note=u'Downloading page %s' % (pagenum + 1),
                errnote=u'Unable to download API page')
            data = json.loads(data_json)
            api_response = data['data']

            if 'items' not in api_response:
                raise ExtractorError(
                    u'[youtube] No video results', expected=True)

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
    IE_DESC = u'YouTube.com searches, newest videos first'


class YoutubeSearchURLIE(InfoExtractor):
    IE_DESC = u'YouTube.com search URLs'
    IE_NAME = u'youtube:search_url'
    _VALID_URL = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?search_query=(?P<query>[^&]+)(?:[&]|$)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query = compat_urllib_parse.unquote_plus(mobj.group('query'))

        webpage = self._download_webpage(url, query)
        result_code = self._search_regex(
            r'(?s)<ol id="search-results"(.*?)</ol>', webpage, u'result HTML')

        part_codes = re.findall(
            r'(?s)<h3 class="yt-lockup-title">(.*?)</h3>', result_code)
        entries = []
        for part_code in part_codes:
            part_title = self._html_search_regex(
                r'(?s)title="([^"]+)"', part_code, 'item title', fatal=False)
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
        return u'youtube:%s' % self._FEED_NAME

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        feed_entries = []
        paging = 0
        for i in itertools.count(1):
            info = self._download_webpage(self._FEED_TEMPLATE % paging,
                                          u'%s feed' % self._FEED_NAME,
                                          u'Downloading page %s' % i)
            info = json.loads(info)
            feed_html = info['feed_html']
            m_ids = re.finditer(r'"/watch\?v=(.*?)["&]', feed_html)
            ids = orderedSet(m.group(1) for m in m_ids)
            feed_entries.extend(
                self.url_result(video_id, 'Youtube', video_id=video_id)
                for video_id in ids)
            if info['paging'] is None:
                break
            paging = info['paging']
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
    _PERSONAL_FEED = True

class YoutubeHistoryIE(YoutubeFeedsInfoExtractor):
    IE_DESC = u'Youtube watch history, "ythistory" keyword (requires authentication)'
    _VALID_URL = u'https?://www\.youtube\.com/feed/history|:ythistory'
    _FEED_NAME = 'history'
    _PERSONAL_FEED = True
    _PLAYLIST_TITLE = u'Youtube Watch History'

class YoutubeFavouritesIE(YoutubeBaseInfoExtractor):
    IE_NAME = u'youtube:favorites'
    IE_DESC = u'YouTube.com favourite videos, "ytfav" keyword (requires authentication)'
    _VALID_URL = r'https?://www\.youtube\.com/my_favorites|:ytfav(?:ou?rites)?'
    _LOGIN_REQUIRED = True

    def _real_extract(self, url):
        webpage = self._download_webpage('https://www.youtube.com/my_favorites', 'Youtube Favourites videos')
        playlist_id = self._search_regex(r'list=(.+?)["&]', webpage, u'favourites playlist id')
        return self.url_result(playlist_id, 'YoutubePlaylist')


class YoutubeTruncatedURLIE(InfoExtractor):
    IE_NAME = 'youtube:truncated_url'
    IE_DESC = False  # Do not list
    _VALID_URL = r'''(?x)
        (?:https?://)?[^/]+/watch\?(?:feature=[a-z_]+)?$|
        (?:https?://)?(?:www\.)?youtube\.com/attribution_link\?a=[^&]+$
    '''

    def _real_extract(self, url):
        raise ExtractorError(
            u'Did you forget to quote the URL? Remember that & is a meta '
            u'character in most shells, so you want to put the URL in quotes, '
            u'like  youtube-dl '
            u'"http://www.youtube.com/watch?feature=foo&v=BaW_jenozKc" '
            u' or simply  youtube-dl BaW_jenozKc  .',
            expected=True)
