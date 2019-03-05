# coding: utf-8
from __future__ import unicode_literals

import json
import os
import re
import subprocess
import tempfile

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_kwargs,
)
from ..utils import (
    check_executable,
    determine_ext,
    encodeArgument,
    ExtractorError,
    get_element_by_id,
    get_exe_version,
    is_outdated_version,
    std_headers,
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
        if (cookie.has_nonstandard_attr('httpOnly') or
                cookie.has_nonstandard_attr('httponly') or
                cookie.has_nonstandard_attr('HttpOnly')):
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


class OpenloadIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?P<host>
                            (?:www\.)?
                            (?:
                                openload\.(?:co|io|link|pw)|
                                oload\.(?:tv|stream|site|xyz|win|download|cloud|cc|icu|fun|club|info|pw|live|space)
                            )
                        )/
                        (?:f|embed)/
                        (?P<id>[a-zA-Z0-9-_]+)
                    '''

    _TESTS = [{
        'url': 'https://openload.co/f/kUEfGclsU9o',
        'md5': 'bf1c059b004ebc7a256f89408e65c36e',
        'info_dict': {
            'id': 'kUEfGclsU9o',
            'ext': 'mp4',
            'title': 'skyrim_no-audio_1080.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'https://openload.co/embed/rjC09fkPLYs',
        'info_dict': {
            'id': 'rjC09fkPLYs',
            'ext': 'mp4',
            'title': 'movie.mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': {
                'en': [{
                    'ext': 'vtt',
                }],
            },
        },
        'params': {
            'skip_download': True,  # test subtitles only
        },
    }, {
        'url': 'https://openload.co/embed/kUEfGclsU9o/skyrim_no-audio_1080.mp4',
        'only_matching': True,
    }, {
        'url': 'https://openload.io/f/ZAn6oz-VZGE/',
        'only_matching': True,
    }, {
        'url': 'https://openload.co/f/_-ztPaZtMhM/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/f/Sxz5sADo82g/, different layout
        # for title and ext
        'url': 'https://openload.co/embed/Sxz5sADo82g/',
        'only_matching': True,
    }, {
        # unavailable via https://openload.co/embed/e-Ixz9ZR5L0/ but available
        # via https://openload.co/f/e-Ixz9ZR5L0/
        'url': 'https://openload.co/f/e-Ixz9ZR5L0/',
        'only_matching': True,
    }, {
        'url': 'https://oload.tv/embed/KnG-kKZdcfY/',
        'only_matching': True,
    }, {
        'url': 'http://www.openload.link/f/KnG-kKZdcfY',
        'only_matching': True,
    }, {
        'url': 'https://oload.stream/f/KnG-kKZdcfY',
        'only_matching': True,
    }, {
        'url': 'https://oload.xyz/f/WwRBpzW8Wtk',
        'only_matching': True,
    }, {
        'url': 'https://oload.win/f/kUEfGclsU9o',
        'only_matching': True,
    }, {
        'url': 'https://oload.download/f/kUEfGclsU9o',
        'only_matching': True,
    }, {
        'url': 'https://oload.cloud/f/4ZDnBXRWiB8',
        'only_matching': True,
    }, {
        # Its title has not got its extension but url has it
        'url': 'https://oload.download/f/N4Otkw39VCw/Tomb.Raider.2018.HDRip.XviD.AC3-EVO.avi.mp4',
        'only_matching': True,
    }, {
        'url': 'https://oload.cc/embed/5NEAbI2BDSk',
        'only_matching': True,
    }, {
        'url': 'https://oload.icu/f/-_i4y_F_Hs8',
        'only_matching': True,
    }, {
        'url': 'https://oload.fun/f/gb6G1H4sHXY',
        'only_matching': True,
    }, {
        'url': 'https://oload.club/f/Nr1L-aZ2dbQ',
        'only_matching': True,
    }, {
        'url': 'https://oload.info/f/5NEAbI2BDSk',
        'only_matching': True,
    }, {
        'url': 'https://openload.pw/f/WyKgK8s94N0',
        'only_matching': True,
    }, {
        'url': 'https://oload.pw/f/WyKgK8s94N0',
        'only_matching': True,
    }, {
        'url': 'https://oload.live/f/-Z58UZ-GR4M',
        'only_matching': True,
    }, {
        'url': 'https://oload.space/f/IY4eZSst3u8/',
        'only_matching': True,
    }]

    _USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+src=["\']((?:https?://)?(?:openload\.(?:co|io)|oload\.tv)/embed/[a-zA-Z0-9-_]+)',
            webpage)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        video_id = mobj.group('id')

        url_pattern = 'https://%s/%%s/%s/' % (host, video_id)
        headers = {
            'User-Agent': self._USER_AGENT,
        }

        for path in ('embed', 'f'):
            page_url = url_pattern % path
            last = path == 'f'
            webpage = self._download_webpage(
                page_url, video_id, 'Downloading %s webpage' % path,
                headers=headers, fatal=last)
            if not webpage:
                continue
            if 'File not found' in webpage or 'deleted by the owner' in webpage:
                if not last:
                    continue
                raise ExtractorError('File not found', expected=True, video_id=video_id)
            break

        phantom = PhantomJSwrapper(self, required_version='2.0')
        webpage, _ = phantom.get(page_url, html=webpage, video_id=video_id, headers=headers)

        decoded_id = (get_element_by_id('streamurl', webpage) or
                      get_element_by_id('streamuri', webpage) or
                      get_element_by_id('streamurj', webpage) or
                      self._search_regex(
                          (r'>\s*([\w-]+~\d{10,}~\d+\.\d+\.0\.0~[\w-]+)\s*<',
                           r'>\s*([\w~-]+~\d+\.\d+\.\d+\.\d+~[\w~-]+)',
                           r'>\s*([\w-]+~\d{10,}~(?:[a-f\d]+:){2}:~[\w-]+)\s*<',
                           r'>\s*([\w~-]+~[a-f0-9:]+~[\w~-]+)\s*<',
                           r'>\s*([\w~-]+~[a-f0-9:]+~[\w~-]+)'), webpage,
                          'stream URL'))

        video_url = 'https://%s/stream/%s?mime=true' % (host, decoded_id)

        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'<span[^>]+class=["\']title["\'][^>]*>([^<]+)', webpage,
            'title', default=None) or self._html_search_meta(
            'description', webpage, 'title', fatal=True)

        entries = self._parse_html5_media_entries(page_url, webpage, video_id)
        entry = entries[0] if entries else {}
        subtitles = entry.get('subtitles')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': entry.get('thumbnail') or self._og_search_thumbnail(webpage, default=None),
            'url': video_url,
            'ext': determine_ext(title, None) or determine_ext(url, 'mp4'),
            'subtitles': subtitles,
            'http_headers': headers,
        }
