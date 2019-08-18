# coding: utf-8
from __future__ import unicode_literals

import base64
import binascii
import json
import os
import random
import subprocess
import tempfile
import re

from .common import InfoExtractor
from ..aes import aes_cbc_decrypt
from ..compat import (
    compat_b64decode,
    compat_ord,
    compat_kwargs,
    compat_urlparse,
)
from ..utils import (
    check_executable,
    get_exe_version,
    is_outdated_version,
    encodeArgument,
    std_headers,
    bytes_to_intlist,
    bytes_to_long,
    ExtractorError,
    float_or_none,
    intlist_to_bytes,
    long_to_bytes,
    pkcs1pad,
    strip_or_none,
    urljoin,
)


def cookie_to_dict(cookie):
    cookie_dict = {
        'name': cookie.name,
        'value': cookie.value,
    }
    if cookie.port_specified:
        cookie_dict['port'] = cookie.port
    if cookie.domain_specified:
        cookie_dict['domain'] = cookie.domain
    if cookie.path_specified:
        cookie_dict['path'] = cookie.path
    if cookie.expires is not None:
        cookie_dict['expires'] = cookie.expires
    if cookie.secure is not None:
        cookie_dict['secure'] = cookie.secure
    if cookie.discard is not None:
        cookie_dict['discard'] = cookie.discard
    try:
        if (cookie.has_nonstandard_attr('httpOnly')
                or cookie.has_nonstandard_attr('httponly')
                or cookie.has_nonstandard_attr('HttpOnly')):
            cookie_dict['httponly'] = True
    except TypeError:
        pass
    return cookie_dict


def cookie_jar_to_list(cookie_jar):
    return [cookie_to_dict(cookie) for cookie in cookie_jar]


class PhantomJSwrapper(object):
    """PhantomJS wrapper class
    This class is experimental.
    """

    _TEMPLATE = r'''
        phantom.onError = function(msg, trace) {{
          var msgStack = ['PHANTOM ERROR: ' + msg];
          if(trace && trace.length) {{
            msgStack.push('TRACE:');
            trace.forEach(function(t) {{
              msgStack.push(' -> ' + (t.file || t.sourceURL) + ': ' + t.line
                + (t.function ? ' (in function ' + t.function +')' : ''));
            }});
          }}
          console.error(msgStack.join('\n'));
          phantom.exit(1);
        }};
        var page = require('webpage').create();
        var fs = require('fs');
        var read = {{ mode: 'r', charset: 'utf-8' }};
        var write = {{ mode: 'w', charset: 'utf-8' }};
        JSON.parse(fs.read("{cookies}", read)).forEach(function(x) {{
          phantom.addCookie(x);
        }});
        page.settings.resourceTimeout = {timeout};
        page.settings.userAgent = "{ua}";
        page.onLoadStarted = function() {{
          page.evaluate(function() {{
            delete window._phantom;
            delete window.callPhantom;
          }});
        }};
        var saveAndExit = function() {{
          fs.write("{html}", page.content, write);
          fs.write("{cookies}", JSON.stringify(phantom.cookies), write);
          phantom.exit();
        }};
        page.onLoadFinished = function(status) {{
          if(page.url === "") {{
            page.setContent(fs.read("{html}", read), "{url}");
          }}
          else {{
            {jscode}
          }}
        }};
        page.open("");
    '''

    _TMP_FILE_NAMES = ['script', 'html', 'cookies']

    @staticmethod
    def _version():
        return get_exe_version('phantomjs', version_re=r'([0-9.]+)')

    def __init__(self, extractor, required_version=None, timeout=10000):
        self._TMP_FILES = {}

        self.exe = check_executable('phantomjs', ['-v'])
        if not self.exe:
            raise ExtractorError('PhantomJS executable not found in PATH, '
                                 'download it from http://phantomjs.org',
                                 expected=True)

        self.extractor = extractor

        if required_version:
            version = self._version()
            if is_outdated_version(version, required_version):
                self.extractor._downloader.report_warning(
                    'Your copy of PhantomJS is outdated, update it to version '
                    '%s or newer if you encounter any errors.' % required_version)

        self.options = {
            'timeout': timeout,
        }
        for name in self._TMP_FILE_NAMES:
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            self._TMP_FILES[name] = tmp

    def __del__(self):
        for name in self._TMP_FILE_NAMES:
            try:
                os.remove(self._TMP_FILES[name].name)
            except (IOError, OSError, KeyError):
                pass

    def _save_cookies(self, url):
        cookies = cookie_jar_to_list(self.extractor._downloader.cookiejar)
        for cookie in cookies:
            if 'path' not in cookie:
                cookie['path'] = '/'
            if 'domain' not in cookie:
                cookie['domain'] = compat_urlparse.urlparse(url).netloc
        with open(self._TMP_FILES['cookies'].name, 'wb') as f:
            f.write(json.dumps(cookies).encode('utf-8'))

    def _load_cookies(self):
        with open(self._TMP_FILES['cookies'].name, 'rb') as f:
            cookies = json.loads(f.read().decode('utf-8'))
        for cookie in cookies:
            if cookie['httponly'] is True:
                cookie['rest'] = {'httpOnly': None}
            if 'expiry' in cookie:
                cookie['expire_time'] = cookie['expiry']
            self.extractor._set_cookie(**compat_kwargs(cookie))

    def get(self, url, html=None, video_id=None, note=None, note2='Executing JS on webpage', headers={}, jscode='saveAndExit();'):
        """
        Downloads webpage (if needed) and executes JS
        Params:
            url: website url
            html: optional, html code of website
            video_id: video id
            note: optional, displayed when downloading webpage
            note2: optional, displayed when executing JS
            headers: custom http headers
            jscode: code to be executed when page is loaded
        Returns tuple with:
            * downloaded website (after JS execution)
            * anything you print with `console.log` (but not inside `page.execute`!)
        In most cases you don't need to add any `jscode`.
        It is executed in `page.onLoadFinished`.
        `saveAndExit();` is mandatory, use it instead of `phantom.exit()`
        It is possible to wait for some element on the webpage, for example:
            var check = function() {
              var elementFound = page.evaluate(function() {
                return document.querySelector('#b.done') !== null;
              });
              if(elementFound)
                saveAndExit();
              else
                window.setTimeout(check, 500);
            }
            page.evaluate(function(){
              document.querySelector('#a').click();
            });
            check();
        """
        if 'saveAndExit();' not in jscode:
            raise ExtractorError('`saveAndExit();` not found in `jscode`')
        if not html:
            html = self.extractor._download_webpage(url, video_id, note=note, headers=headers)
        with open(self._TMP_FILES['html'].name, 'wb') as f:
            f.write(html.encode('utf-8'))

        self._save_cookies(url)

        replaces = self.options
        replaces['url'] = url
        user_agent = headers.get('User-Agent') or std_headers['User-Agent']
        replaces['ua'] = user_agent.replace('"', '\\"')
        replaces['jscode'] = jscode

        for x in self._TMP_FILE_NAMES:
            replaces[x] = self._TMP_FILES[x].name.replace('\\', '\\\\').replace('"', '\\"')

        with open(self._TMP_FILES['script'].name, 'wb') as f:
            f.write(self._TEMPLATE.format(**replaces).encode('utf-8'))

        if video_id is None:
            self.extractor.to_screen('%s' % (note2,))
        else:
            self.extractor.to_screen('%s: %s' % (video_id, note2))

        p = subprocess.Popen([
            self.exe, '--ssl-protocol=any',
            self._TMP_FILES['script'].name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise ExtractorError(
                'Executing JS failed\n:' + encodeArgument(err))
        with open(self._TMP_FILES['html'].name, 'rb') as f:
            html = f.read().decode('utf-8')

        self._load_cookies()

        return (html, encodeArgument(out))


class ADNIE(InfoExtractor):
    IE_DESC = 'Anime Digital Network'
    _VALID_URL = r'https?://(?:www\.)?animedigitalnetwork\.fr/video/[^/]+/(?P<id>\d+)'
    _TEST = {
        'url': 'http://animedigitalnetwork.fr/video/blue-exorcist-kyoto-saga/7778-episode-1-debut-des-hostilites',
        'md5': 'e497370d847fd79d9d4c74be55575c7a',
        'info_dict': {
            'id': '7778',
            'ext': 'mp4',
            'title': 'Blue Exorcist - Kyôto Saga - Épisode 1',
            'description': 'md5:2f7b5aa76edbc1a7a92cedcda8a528d5',
        }
    }
    _BASE_URL = 'http://animedigitalnetwork.fr'
    _RSA_KEY = (0xc35ae1e4356b65a73b551493da94b8cb443491c0aa092a357a5aee57ffc14dda85326f42d716e539a34542a0d3f363adf16c5ec222d713d5997194030ee2e4f0d1fb328c01a81cf6868c090d50de8e169c6b13d1675b9eeed1cbc51e1fffca9b38af07f37abd790924cd3bee59d0257cfda4fe5f3f0534877e21ce5821447d1b, 65537)
    _POS_ALIGN_MAP = {
        'start': 1,
        'end': 3,
    }
    _LINE_ALIGN_MAP = {
        'middle': 8,
        'end': 4,
    }

    @staticmethod
    def _ass_subtitles_timecode(seconds):
        return '%01d:%02d:%02d.%02d' % (seconds / 3600, (seconds % 3600) / 60, seconds % 60, (seconds % 1) * 100)

    def _get_subtitles(self, sub_path, video_id, url, webpage):
        if not sub_path:
            return None

        enc_subtitles = self._download_webpage(
            urljoin(self._BASE_URL, sub_path),
            video_id, 'Downloading subtitles location', fatal=False) or '{}'
        subtitle_location = (self._parse_json(enc_subtitles, video_id, fatal=False) or {}).get('location')
        if subtitle_location:
            enc_subtitles = self._download_webpage(
                urljoin(self._BASE_URL, subtitle_location),
                video_id, 'Downloading subtitles data', fatal=False,
                headers={'Origin': 'https://animedigitalnetwork.fr'})
        if not enc_subtitles:
            return None

        # Get the second half of the encryption key
        phantom = PhantomJSwrapper(self, required_version='2.0')
        _, logs = phantom.get(url, html=webpage, video_id=video_id, jscode="""
          function getKey() {
            var key = page.evaluate(function() {
              return window.videojs &&
                window.videojs.players["adn-video-js"] &&
                window.videojs.players["adn-video-js"].onChromecastCustomData().key;
            })
            if (key) {
              console.log('Key is : ' + key);
              saveAndExit();
            } else {
              setTimeout(getKey, 1 * 1000);
            }
          }
          getKey();
          window.setTimeout(function() {
            console.error('Timed out');
            saveAndExit();
          }, 60 * 1000);
        """)
        match = re.match(re.compile(r'Key is : (.+)\n', re.MULTILINE), logs)
        if 'Timed out' in logs or match is None:
            raise ExtractorError('Could not get the key')
        key = match.group(1).strip()

        dec_subtitles = intlist_to_bytes(aes_cbc_decrypt(
            bytes_to_intlist(compat_b64decode(enc_subtitles[24:])),
            bytes_to_intlist(binascii.unhexlify(self._K + key)),
            bytes_to_intlist(compat_b64decode(enc_subtitles[:24]))
        ))
        subtitles_json = self._parse_json(
            dec_subtitles[:-compat_ord(dec_subtitles[-1])].decode(),
            None, fatal=False)
        if not subtitles_json:
            return None

        subtitles = {}
        for sub_lang, sub in subtitles_json.items():
            ssa = '''[Script Info]
ScriptType:V4.00
[V4 Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,TertiaryColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,AlphaLevel,Encoding
Style: Default,Arial,18,16777215,16777215,16777215,0,-1,0,1,1,0,2,20,20,20,0,0
[Events]
Format: Marked,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text'''
            for current in sub:
                start, end, text, line_align, position_align = (
                    float_or_none(current.get('startTime')),
                    float_or_none(current.get('endTime')),
                    current.get('text'), current.get('lineAlign'),
                    current.get('positionAlign'))
                if start is None or end is None or text is None:
                    continue
                alignment = self._POS_ALIGN_MAP.get(position_align, 2) + self._LINE_ALIGN_MAP.get(line_align, 0)
                ssa += os.linesep + 'Dialogue: Marked=0,%s,%s,Default,,0,0,0,,%s%s' % (
                    self._ass_subtitles_timecode(start),
                    self._ass_subtitles_timecode(end),
                    '{\\a%d}' % alignment if alignment != 2 else '',
                    text.replace('\n', '\\N').replace('<i>', '{\\i1}').replace('</i>', '{\\i0}'))

            if sub_lang == 'vostf':
                sub_lang = 'fr'
            subtitles.setdefault(sub_lang, []).extend([{
                'ext': 'json',
                'data': json.dumps(sub),
            }, {
                'ext': 'ssa',
                'data': ssa,
            }])
        return subtitles

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player_config = self._parse_json(self._search_regex(
            r'playerConfig\s*=\s*({.+});', webpage,
            'player config', default='{}'), video_id, fatal=False)
        if not player_config:
            config_url = urljoin(self._BASE_URL, self._search_regex(
                r'(?:id="player"|class="[^"]*adn-player-container[^"]*")[^>]+data-url="([^"]+)"',
                webpage, 'config url'))
            player_config = self._download_json(
                config_url, video_id,
                'Downloading player config JSON metadata')['player']

        video_info = {}
        video_info_str = self._search_regex(
            r'videoInfo\s*=\s*({.+});', webpage,
            'video info', fatal=False)
        if video_info_str:
            video_info = self._parse_json(
                video_info_str, video_id, fatal=False) or {}

        options = player_config.get('options') or {}
        metas = options.get('metas') or {}
        links = player_config.get('links') or {}
        sub_path = player_config.get('subtitles')
        error = None
        if not links:
            links_url = player_config.get('linksurl') or options['videoUrl']
            token = options['token']
            self._K = ''.join([random.choice('0123456789abcdef') for _ in range(16)])
            message = bytes_to_intlist(json.dumps({
                'k': self._K,
                'e': 60,
                't': token,
            }))
            padded_message = intlist_to_bytes(pkcs1pad(message, 128))
            n, e = self._RSA_KEY
            encrypted_message = long_to_bytes(pow(bytes_to_long(padded_message), e, n))
            authorization = base64.b64encode(encrypted_message).decode()
            links_data = self._download_json(
                urljoin(self._BASE_URL, links_url), video_id,
                'Downloading links JSON metadata', headers={
                    'Authorization': 'Bearer ' + authorization,
                })
            links = links_data.get('links') or {}
            metas = metas or links_data.get('meta') or {}
            sub_path = sub_path or links_data.get('subtitles') or \
                'index.php?option=com_vodapi&task=subtitles.getJSON&format=json&id=' + video_id
            sub_path += '&token=' + token
            error = links_data.get('error')
        title = metas.get('title') or video_info['title']

        formats = []
        for format_id, qualities in links.items():
            if not isinstance(qualities, dict):
                continue
            for quality, load_balancer_url in qualities.items():
                load_balancer_data = self._download_json(
                    load_balancer_url, video_id,
                    'Downloading %s %s JSON metadata' % (format_id, quality),
                    fatal=False) or {}
                m3u8_url = load_balancer_data.get('location')
                if not m3u8_url:
                    continue
                m3u8_formats = self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False)
                if format_id == 'vf':
                    for f in m3u8_formats:
                        f['language'] = 'fr'
                formats.extend(m3u8_formats)
        if not error:
            error = options.get('error')
        if not formats and error:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error), expected=True)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': strip_or_none(metas.get('summary') or video_info.get('resume')),
            'thumbnail': video_info.get('image'),
            'formats': formats,
            'subtitles': self.extract_subtitles(sub_path, video_id, url, webpage),
            'episode': metas.get('subtitle') or video_info.get('videoTitle'),
            'series': video_info.get('playlistTitle'),
        }
