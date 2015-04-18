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

        os.remove(encodeFilename(temp_thumbnail))
        # for formats that don't support thumbnails (like 3gp) AtomicParsley
        # won't create to the temporary file
        if b'No changes' in stdout:
            self._downloader.report_warning('The file format doesn\'t support embedding a thumbnail')
        else:
            os.remove(encodeFilename(filename))
            os.rename(encodeFilename(temp_filename), encodeFilename(filename))

        return [], info
