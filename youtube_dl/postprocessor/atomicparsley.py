# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import os
import subprocess

from .common import PostProcessor
from ..compat import (
    compat_urlretrieve,
)
from ..utils import (
    check_executable,
    encodeFilename,
    PostProcessingError,
    prepend_extension,
    shell_quote
)


class AtomicParsleyPPError(PostProcessingError):
    pass


class AtomicParsleyPP(PostProcessor):
    def run(self, info):
        if not check_executable('AtomicParsley', ['-v']):
            raise AtomicParsleyPPError('AtomicParsley was not found. Please install.')

        filename = info['filepath']
        temp_filename = prepend_extension(filename, 'temp')
        temp_thumbnail = prepend_extension(filename, 'thumb')

        if not info.get('thumbnail'):
            raise AtomicParsleyPPError('Thumbnail was not found. Nothing to do.')

        compat_urlretrieve(info['thumbnail'], temp_thumbnail)

        cmd = ['AtomicParsley', filename, '--artwork', temp_thumbnail, '-o', temp_filename]

        self._downloader.to_screen('[atomicparsley] Adding thumbnail to "%s"' % filename)

        if self._downloader.params.get('verbose', False):
            self._downloader.to_screen('[debug] AtomicParsley command line: %s' % shell_quote(cmd))

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            msg = stderr.decode('utf-8', 'replace').strip()
            raise AtomicParsleyPPError(msg)

        os.remove(encodeFilename(filename))
        os.remove(encodeFilename(temp_thumbnail))
        os.rename(encodeFilename(temp_filename), encodeFilename(filename))

        return True, info
