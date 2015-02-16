from __future__ import unicode_literals

import os.path
import subprocess
import sys

from .common import FileDownloader
from ..utils import (
    encodeFilename,
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

    def _source_address(self, command_option):
        source_address = self.params.get('source_address')
        if source_address is None:
            return []
        return [command_option, source_address]

    def _call_downloader(self, tmpfilename, info_dict):
        """ Either overwrite this or implement _make_cmd """
        cmd = self._make_cmd(tmpfilename, info_dict)

        if sys.platform == 'win32' and sys.version_info < (3, 0):
            # Windows subprocess module does not actually support Unicode
            # on Python 2.x
            # See http://stackoverflow.com/a/9951851/35070
            subprocess_encoding = sys.getfilesystemencoding()
            cmd = [a.encode(subprocess_encoding, 'ignore') for a in cmd]
        else:
            subprocess_encoding = None
        self._debug_cmd(cmd, subprocess_encoding)

        p = subprocess.Popen(
            cmd, stderr=subprocess.PIPE)
        _, stderr = p.communicate()
        if p.returncode != 0:
            self.to_stderr(stderr)
        return p.returncode


class CurlFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-o', tmpfilename]
        for key, val in info_dict['http_headers'].items():
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._source_address('--interface')
        cmd += ['--', info_dict['url']]
        return cmd


class WgetFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [self.exe, '-O', tmpfilename, '-nv', '--no-cookies']
        for key, val in info_dict['http_headers'].items():
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._source_address('--bind-address')
        cmd += ['--', info_dict['url']]
        return cmd


class Aria2cFD(ExternalFD):
    def _make_cmd(self, tmpfilename, info_dict):
        cmd = [
            self.exe, '-c',
            '--min-split-size', '1M', '--max-connection-per-server', '4']
        dn = os.path.dirname(tmpfilename)
        if dn:
            cmd += ['--dir', dn]
        cmd += ['--out', os.path.basename(tmpfilename)]
        for key, val in info_dict['http_headers'].items():
            cmd += ['--header', '%s: %s' % (key, val)]
        cmd += self._source_address('--interface')
        cmd += ['--', info_dict['url']]
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
    bn = os.path.basename(external_downloader)
    return _BY_NAME[bn]
