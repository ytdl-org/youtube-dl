from __future__ import unicode_literals

import logging
import os
import re
import subprocess
import sys
import tempfile
import time

from .common import FileDownloader
from ..compat import (
    compat_setenv,
    compat_str,
    compat_subprocess_Popen,
)

try:
    from ..postprocessor.ffmpeg import FFmpegPostProcessor, EXT_TO_OUT_FORMATS
except ImportError:
    FFmpegPostProcessor = None

from ..utils import (
    cli_option,
    cli_valueless_option,
    cli_bool_option,
    cli_configuration_args,
    encodeFilename,
    encodeArgument,
    handle_youtubedl_headers,
    check_executable,
    is_outdated_version,
    process_communicate_or_kill,
    T,
    traverse_obj,
)


class ExternalFD(FileDownloader):
    def real_download(self, filename, info_dict):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)
        self._cookies_tempfile = None

        try:
            started = time.time()
            retval = self._call_downloader(tmpfilename, info_dict)
        except KeyboardInterrupt:
            if not info_dict.get('is_live'):
                raise
            # Live stream downloading cancellation should be considered as
            # correct and expected termination thus all postprocessing
            # should take place
            retval = 0
            self.to_screen('[%s] Interrupted by user' % self.get_basename())
        finally:
            if self._cookies_tempfile and os.path.isfile(self._cookies_tempfile):
                try:
                    os.remove(self._cookies_tempfile)
                except OSError:
                    self.report_warning(
                        'Unable to delete temporary cookies file "{0}"'.format(self._cookies_tempfile))

        if retval == 0:
            status = {
                'filename': filename,
                'status': 'finished',
                'elapsed': time.time() - started,
            }
            if filename != '-':
                fsize = os.path.getsize(encodeFilename(tmpfilename))
                self.to_screen('\r[%s] Downloaded %s bytes' % (self.get_basename(), fsize))
                self.try_rename(tmpfilename, filename)
                status.update({
                    'downloaded_bytes': fsize,
                    'total_bytes': fsize,
                })
            self._hook_progress(status)
            return True
        else:
            self.to_stderr('\n')
            self.report_error('%s exited with code %d' % (
                self.get_basename(), retval))
            return False

    @classmethod
    def get_basename(cls):
        return cls.__name__[:-2].lower()

    @property
    def exe(self):
        return self.params.get('external_downloader')

    @classmethod
    def available(cls):
        return check_executable(cls.get_basename(), [cls.AVAILABLE_OPT])

    @classmethod
    def supports(cls, info_dict):
        return info_dict['protocol'] in ('http', 'https', 'ftp', 'ftps')

    @classmethod
    def can_download(cls, info_dict):
        return cls.available() and cls.supports(info_dict)

    def _option(self, command_option, param):
        return cli_option(self.params, command_option, param)

    def _bool_option(self, command_option, param, true_value='true', false_value='false', separator=None):
        return cli_bool_option(self.params, command_option, param, true_value, false_value, separator)

    def _valueless_option(self, command_option, param, expected_value=True):
        return cli_valueless_option(self.params, command_option, param, expected_value)

    def _configuration_args(self, default=[]):
        return cli_configuration_args(self.params, 'external_downloader_args', default)

    def _write_cookies(self):
        if not self.ydl.cookiejar.filename:
            tmp_cookies = tempfile.NamedTemporaryFile(suffix='.cookies', delete=False)
            tmp_cookies.close()
            self._cookies_tempfile = tmp_cookies.name
            self.to_screen('[download] Writing temporary cookies file to "{0}"'.format(self._cookies_tempfile))
        # real_download resets _cookies_tempfile; if it's None, save() will write to cookiejar.filename
        self.ydl.cookiejar.save(self._cookies_tempfile, ignore_discard=True, ignore_expires=True)
        return self.ydl.cookiejar.filename or self._cookies_tempfile

    def _call_downloader(self, tmpfilename, info_dict):
        """ Either overwrite this or implement _make_cmd """
        cmd = [encodeArgument(a) for a in self._make_cmd(tmpfilename, info_dict)]

        self._debug_cmd(cmd)

        p = subprocess.Popen(
            cmd, stderr=subprocess.PIPE)
        _, stderr = process_communicate_or_kill(p)
        if p.returncode != 0:
            self.to_stderr(stderr.decode('utf-8', 'replace'))
        return p.returncode

    @staticmethod
    def _header_items(info_dict):
        return traverse_obj(
            info_dict, ('http_headers', T(dict.items), Ellipsis))


class CurlFD(ExternalFD):
    AVAILABLE_OPT = '-V'

    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '--location', '-o', tmpfilename, '--compressed']
        cookie_header = self.ydl.cookiejar.get_cookie_header(info_dict['url'])
        if cookie_header:
            cmd += ['--cookie', cookie_header]
        for key, val in self._header_items(info_dict):
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._bool_option('--continue-at', 'continuedl', '-', '0')
        cmd += self._valueless_option('--silent', 'noprogress')
        cmd += self._valueless_option('--verbose', 'verbose')
        cmd += self._option('--limit-rate', 'ratelimit')
        retry = self._option('--retry', 'retries')
        if len(retry) == 2:
            if retry[1] in ('inf', 'infinite'):
                retry[1] = '2147483647'
            cmd += retry
        cmd += self._option('--max-filesize', 'max_filesize')
        cmd += self._option('--interface', 'source_address')
        cmd += self._option('--proxy', 'proxy')
        cmd += self._valueless_option('--insecure', 'nocheckcertificate')
        cmd += self._configuration_args()
        cmd += ['--', info_dict['url']]
        return cmd

    def _call_downloader(self, tmpfilename, info_dict):
        cmd = [encodeArgument(a) for a in self._make_cmd(tmpfilename, info_dict)]

        self._debug_cmd(cmd)

        # curl writes the progress to stderr so don't capture it.
        p = subprocess.Popen(cmd)
        process_communicate_or_kill(p)
        return p.returncode


class AxelFD(ExternalFD):
    AVAILABLE_OPT = '-V'

    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-o', tmpfilename]
        for key, val in self._header_items(info_dict):
            cmd += ['-H', '%s: %s' % (key, val)]
        cookie_header = self.ydl.cookiejar.get_cookie_header(info_dict['url'])
        if cookie_header:
            cmd += ['-H', 'Cookie: {0}'.format(cookie_header), '--max-redirect=0']
        cmd += self._configuration_args()
        cmd += ['--', info_dict['url']]
        return cmd


class WgetFD(ExternalFD):
    AVAILABLE_OPT = '--version'

    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-O', tmpfilename, '-nv', '--compression=auto']
        if self.ydl.cookiejar.get_cookie_header(info_dict['url']):
            cmd += ['--load-cookies', self._write_cookies()]
        for key, val in self._header_items(info_dict):
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._option('--limit-rate', 'ratelimit')
        retry = self._option('--tries', 'retries')
        if len(retry) == 2:
            if retry[1] in ('inf', 'infinite'):
                retry[1] = '0'
            cmd += retry
        cmd += self._option('--bind-address', 'source_address')
        proxy = self.params.get('proxy')
        if proxy:
            for var in ('http_proxy', 'https_proxy'):
                cmd += ['--execute', '%s=%s' % (var, proxy)]
        cmd += self._valueless_option('--no-check-certificate', 'nocheckcertificate')
        cmd += self._configuration_args()
        cmd += ['--', info_dict['url']]
        return cmd


class Aria2cFD(ExternalFD):
    AVAILABLE_OPT = '-v'

    @staticmethod
    def _aria2c_filename(fn):
        return fn if os.path.isabs(fn) else os.path.join('.', fn)

    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-c',
               '--console-log-level=warn', '--summary-interval=0', '--download-result=hide',
               '--http-accept-gzip=true', '--file-allocation=none', '-x16', '-j16', '-s16']
        if 'fragments' in info_dict:
            cmd += ['--allow-overwrite=true', '--allow-piece-length-change=true']
        else:
            cmd += ['--min-split-size', '1M']

        if self.ydl.cookiejar.get_cookie_header(info_dict['url']):
            cmd += ['--load-cookies={0}'.format(self._write_cookies())]
        for key, val in self._header_items(info_dict):
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._configuration_args(['--max-connection-per-server', '4'])
        cmd += ['--out', os.path.basename(tmpfilename)]
        cmd += self._option('--max-overall-download-limit', 'ratelimit')
        cmd += self._option('--interface', 'source_address')
        cmd += self._option('--all-proxy', 'proxy')
        cmd += self._bool_option('--check-certificate', 'nocheckcertificate', 'false', 'true', '=')
        cmd += self._bool_option('--remote-time', 'updatetime', 'true', 'false', '=')
        cmd += self._bool_option('--show-console-readout', 'noprogress', 'false', 'true', '=')
        cmd += self._configuration_args()

        # aria2c strips out spaces from the beginning/end of filenames and paths.
        # We work around this issue by adding a "./" to the beginning of the
        # filename and relative path, and adding a "/" at the end of the path.
        # See: https://github.com/yt-dlp/yt-dlp/issues/276
        # https://github.com/ytdl-org/youtube-dl/issues/20312
        # https://github.com/aria2/aria2/issues/1373
        dn = os.path.dirname(tmpfilename)
        if dn:
            cmd += ['--dir', self._aria2c_filename(dn) + os.path.sep]
        if 'fragments' not in info_dict:
            cmd += ['--out', self._aria2c_filename(os.path.basename(tmpfilename))]
        cmd += ['--auto-file-renaming=false']
        if 'fragments' in info_dict:
            cmd += ['--file-allocation=none', '--uri-selector=inorder']
            url_list_file = '%s.frag.urls' % (tmpfilename, )
            url_list = []
            for frag_index, fragment in enumerate(info_dict['fragments']):
                fragment_filename = '%s-Frag%d' % (os.path.basename(tmpfilename), frag_index)
                url_list.append('%s\n\tout=%s' % (fragment['url'], self._aria2c_filename(fragment_filename)))
            stream, _ = self.sanitize_open(url_list_file, 'wb')
            stream.write('\n'.join(url_list).encode())
            stream.close()
            cmd += ['-i', self._aria2c_filename(url_list_file)]
        else:
            cmd += ['--', info_dict['url']]
        return cmd


class Aria2pFD(ExternalFD):
    ''' Aria2pFD class
    This class support to use aria2p as downloader.
    (Aria2p, a command-line tool and Python library to interact with an aria2c daemon process
    through JSON-RPC.)
    It can help you to get download progress more easily.
    To use aria2p as downloader, you need to install aria2c and aria2p, aria2p can download with pip.
    Then run aria2c in the background and enable with the --enable-rpc option.
    '''
    try:
        import aria2p
        __avail = True
    except ImportError:
        __avail = False

    @classmethod
    def available(cls):
        return cls.__avail

    def _call_downloader(self, tmpfilename, info_dict):
        aria2 = self.aria2p.API(
            self.aria2p.Client(
                host='http://localhost',
                port=6800,
                secret=''
            )
        )

        options = {
            'min-split-size': '1M',
            'max-connection-per-server': 4,
            'auto-file-renaming': 'false',
        }
        options['dir'] = os.path.dirname(tmpfilename) or os.path.abspath('.')
        options['out'] = os.path.basename(tmpfilename)
        if self.ydl.cookiejar.get_cookie_header(info_dict['url']):
            options['load-cookies'] = self._write_cookies()
        options['header'] = []
        for key, val in self._header_items(info_dict):
            options['header'].append('{0}: {1}'.format(key, val))
        download = aria2.add_uris([info_dict['url']], options)
        status = {
            'status': 'downloading',
            'tmpfilename': tmpfilename,
        }
        started = time.time()
        while download.status in ['active', 'waiting']:
            download = aria2.get_download(download.gid)
            status.update({
                'downloaded_bytes': download.completed_length,
                'total_bytes': download.total_length,
                'elapsed': time.time() - started,
                'eta': download.eta.total_seconds(),
                'speed': download.download_speed,
            })
            self._hook_progress(status)
            time.sleep(.5)
        return download.status != 'complete'


class HttpieFD(ExternalFD):
    @classmethod
    def available(cls):
        return check_executable('http', ['--version'])

    def _make_cmd(self, tmpfilename, info_dict):
        cmd = ['http', '--download', '--output', tmpfilename, info_dict['url']]
        for key, val in self._header_items(info_dict):
            cmd += ['%s:%s' % (key, val)]

        # httpie 3.1.0+ removes the Cookie header on redirect, so this should be safe for now. [1]
        # If we ever need cookie handling for redirects, we can export the cookiejar into a session. [2]
        # 1: https://github.com/httpie/httpie/security/advisories/GHSA-9w4w-cpc8-h2fq
        # 2: https://httpie.io/docs/cli/sessions
        cookie_header = self.ydl.cookiejar.get_cookie_header(info_dict['url'])
        if cookie_header:
            cmd += ['Cookie:%s' % cookie_header]
        return cmd


class FFmpegFD(ExternalFD):
    @classmethod
    def supports(cls, info_dict):
        return info_dict['protocol'] in ('http', 'https', 'ftp', 'ftps', 'm3u8', 'rtsp', 'rtmp', 'mms', 'http_dash_segments')

    @classmethod
    def available(cls):
        # actual availability can only be confirmed for an instance
        return bool(FFmpegPostProcessor)

    def _call_downloader(self, tmpfilename, info_dict):
        # `downloader` means the parent `YoutubeDL`
        ffpp = FFmpegPostProcessor(downloader=self.ydl)
        if not ffpp.available:
            self.report_error('ffmpeg required for download but no ffmpeg (nor avconv) executable could be found. Please install one.')
            return False
        ffpp.check_version()

        args = [ffpp.executable, '-y']

        for log_level in ('quiet', 'verbose'):
            if self.params.get(log_level, False):
                args += ['-loglevel', log_level]
                break

        seekable = info_dict.get('_seekable')
        if seekable is not None:
            # setting -seekable prevents ffmpeg from guessing if the server
            # supports seeking(by adding the header `Range: bytes=0-`), which
            # can cause problems in some cases
            # https://github.com/ytdl-org/youtube-dl/issues/11800#issuecomment-275037127
            # http://trac.ffmpeg.org/ticket/6125#comment:10
            args += ['-seekable', '1' if seekable else '0']

        args += self._configuration_args()

        # start_time = info_dict.get('start_time') or 0
        # if start_time:
        #     args += ['-ss', compat_str(start_time)]
        # end_time = info_dict.get('end_time')
        # if end_time:
        #     args += ['-t', compat_str(end_time - start_time)]

        url = info_dict['url']
        cookies = self.ydl.cookiejar.get_cookies_for_url(url)
        if cookies:
            args.extend(['-cookies', ''.join(
                '{0}={1}; path={2}; domain={3};\r\n'.format(
                    cookie.name, cookie.value, cookie.path, cookie.domain)
                for cookie in cookies)])

        if info_dict.get('http_headers') and re.match(r'^https?://', url):
            # Trailing \r\n after each HTTP header is important to prevent warning from ffmpeg/avconv:
            # [http @ 00000000003d2fa0] No trailing CRLF found in HTTP header.
            headers = handle_youtubedl_headers(info_dict['http_headers'])
            args += [
                '-headers',
                ''.join('%s: %s\r\n' % (key, val) for key, val in headers.items())]

        env = None
        proxy = self.params.get('proxy')
        if proxy:
            if not re.match(r'^[\da-zA-Z]+://', proxy):
                proxy = 'http://%s' % proxy

            if proxy.startswith('socks'):
                self.report_warning(
                    '%s does not support SOCKS proxies. Downloading is likely to fail. '
                    'Consider adding --hls-prefer-native to your command.' % self.get_basename())

            # Since December 2015 ffmpeg supports -http_proxy option (see
            # http://git.videolan.org/?p=ffmpeg.git;a=commit;h=b4eb1f29ebddd60c41a2eb39f5af701e38e0d3fd)
            # We could switch to the following code if we are able to detect version properly
            # args += ['-http_proxy', proxy]
            env = os.environ.copy()
            compat_setenv('HTTP_PROXY', proxy, env=env)
            compat_setenv('http_proxy', proxy, env=env)

        protocol = info_dict.get('protocol')

        if protocol == 'rtmp':
            player_url = info_dict.get('player_url')
            page_url = info_dict.get('page_url')
            app = info_dict.get('app')
            play_path = info_dict.get('play_path')
            tc_url = info_dict.get('tc_url')
            flash_version = info_dict.get('flash_version')
            live = info_dict.get('rtmp_live', False)
            conn = info_dict.get('rtmp_conn')
            if player_url is not None:
                args += ['-rtmp_swfverify', player_url]
            if page_url is not None:
                args += ['-rtmp_pageurl', page_url]
            if app is not None:
                args += ['-rtmp_app', app]
            if play_path is not None:
                args += ['-rtmp_playpath', play_path]
            if tc_url is not None:
                args += ['-rtmp_tcurl', tc_url]
            if flash_version is not None:
                args += ['-rtmp_flashver', flash_version]
            if live:
                args += ['-rtmp_live', 'live']
            if isinstance(conn, list):
                for entry in conn:
                    args += ['-rtmp_conn', entry]
            elif isinstance(conn, compat_str):
                args += ['-rtmp_conn', conn]

        args += ['-i', url, '-c', 'copy']

        if self.params.get('test', False):
            args += ['-fs', compat_str(self._TEST_FILE_SIZE)]

        if protocol in ('m3u8', 'm3u8_native'):
            if self.params.get('hls_use_mpegts', False) or tmpfilename == '-':
                args += ['-f', 'mpegts']
            else:
                args += ['-f', 'mp4']
                if (ffpp.basename == 'ffmpeg' and is_outdated_version(ffpp._versions['ffmpeg'], '3.2', False)) and (not info_dict.get('acodec') or info_dict['acodec'].split('.')[0] in ('aac', 'mp4a')):
                    args += ['-bsf:a', 'aac_adtstoasc']
        elif protocol == 'rtmp':
            args += ['-f', 'flv']
        else:
            args += ['-f', EXT_TO_OUT_FORMATS.get(info_dict['ext'], info_dict['ext'])]

        args = [encodeArgument(opt) for opt in args]
        args.append(encodeFilename(ffpp._ffmpeg_filename_argument(tmpfilename), True))

        self._debug_cmd(args)

        # From [1], a PIPE opened in Popen() should be closed, unless
        # .communicate() is called. Avoid leaking any PIPEs by using Popen
        # as a context manager (newer Python 3.x and compat)
        # Fixes "Resource Warning" in test/test_downloader_external.py
        # [1] https://devpress.csdn.net/python/62fde12d7e66823466192e48.html
        _proc = compat_subprocess_Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            bufsize=1,
            env=env,
        )
        ffmpeg_logger = logging.getLogger('ffmpeg')
        with _proc as proc:
            try:
                for line in iter(proc.stdout.readline, ''):
                    ffmpeg_logger.debug(line.strip())

                proc.stdout.close()
                retval = proc.wait()
            except BaseException as e:
                if isinstance(e, KeyError) and (sys.platform != 'win32'):
                    process_communicate_or_kill(proc, 'q')
                else:
                    proc.kill()
                raise

        return retval


class AVconvFD(FFmpegFD):
    pass


_BY_NAME = dict(
    (klass.get_basename(), klass)
    for name, klass in globals().items()
    if name.endswith('FD') and name != 'ExternalFD'
)


def list_external_downloaders():
    return sorted(_BY_NAME.keys())


def get_external_downloader(external_downloader):
    """ Given the name of the executable, see whether we support the given
        downloader . """
    # Drop .exe extension on Windows
    bn = os.path.splitext(os.path.basename(external_downloader))[0]
    return _BY_NAME[bn]
