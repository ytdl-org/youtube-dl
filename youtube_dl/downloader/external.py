from __future__ import unicode_literals

import os.path
import subprocess

from .common import FileDownloader
from ..utils import (
    cli_option,
    cli_valueless_option,
    cli_bool_option,
    cli_configuration_args,
    encodeFilename,
    encodeArgument,
)


class ExternalFD(FileDownloader):
    def real_download(self, filename, info_dict):
        self.report_destination(filename)
        tmpfilename = self.temp_name(filename)

        retval = self._call_downloader(tmpfilename, info_dict)
        if retval == 0:
            fsize = os.path.getsize(encodeFilename(tmpfilename))
            self.to_screen('\r[%s] Downloaded %s bytes' % (self.get_basename(), fsize))
            self.try_rename(tmpfilename, filename)
            self._hook_progress({
                'downloaded_bytes': fsize,
                'total_bytes': fsize,
                'filename': filename,
                'status': 'finished',
            })
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
    def supports(cls, info_dict):
        return info_dict['protocol'] in ('http', 'https', 'ftp', 'ftps')

    def _option(self, command_option, param):
        return cli_option(self.params, command_option, param)

    def _bool_option(self, command_option, param, true_value='true', false_value='false', separator=None):
        return cli_bool_option(self.params, command_option, param, true_value, false_value, separator)

    def _valueless_option(self, command_option, param, expected_value=True):
        return cli_valueless_option(self.params, command_option, param, expected_value)

    def _configuration_args(self, default=[]):
        return cli_configuration_args(self.params, 'external_downloader_args', default)

    def _call_downloader(self, tmpfilename, info_dict):
        """ Either overwrite this or implement _make_cmd """
        cmd = [encodeArgument(a) for a in self._make_cmd(tmpfilename, info_dict)]

        self._debug_cmd(cmd)

        p = subprocess.Popen(
            cmd, stderr=subprocess.PIPE)
        _, stderr = p.communicate()
        if p.returncode != 0:
            self.to_stderr(stderr)
        return p.returncode


class CurlFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '--location', '-o', tmpfilename]
        for key, val in info_dict['http_headers'].items():
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._option('--interface', 'source_address')
        cmd += self._option('--proxy', 'proxy')
        cmd += self._valueless_option('--insecure', 'nocheckcertificate')
        cmd += self._configuration_args()
        cmd += ['--', info_dict['url']]
        return cmd


class AxelFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-o', tmpfilename]
        for key, val in info_dict['http_headers'].items():
            cmd += ['-H', '%s: %s' % (key, val)]
        cmd += self._configuration_args()
        cmd += ['--', info_dict['url']]
        return cmd


class WgetFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-O', tmpfilename, '-nv', '--no-cookies']
        for key, val in info_dict['http_headers'].items():
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._option('--bind-address', 'source_address')
        cmd += self._option('--proxy', 'proxy')
        cmd += self._valueless_option('--no-check-certificate', 'nocheckcertificate')
        cmd += self._configuration_args()
        cmd += ['--', info_dict['url']]
        return cmd


class Aria2cFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-c']
        cmd += self._configuration_args([
            '--min-split-size', '1M', '--max-connection-per-server', '4'])
        dn = os.path.dirname(tmpfilename)
        if dn:
            cmd += ['--dir', dn]
        cmd += ['--out', os.path.basename(tmpfilename)]
        for key, val in info_dict['http_headers'].items():
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._option('--interface', 'source_address')
        cmd += self._option('--all-proxy', 'proxy')
        cmd += self._bool_option('--check-certificate', 'nocheckcertificate', 'false', 'true', '=')
        cmd += ['--', info_dict['url']]
        return cmd


class HttpieFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = ['http', '--download', '--output', tmpfilename, info_dict['url']]
        for key, val in info_dict['http_headers'].items():
            cmd += ['%s:%s' % (key, val)]
        return cmd

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
