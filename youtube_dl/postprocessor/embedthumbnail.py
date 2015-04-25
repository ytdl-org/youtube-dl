# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import os
import subprocess

from .ffmpeg import FFmpegPostProcessor

from ..compat import (
    compat_urlretrieve,
)
from ..utils import (
    determine_ext,
    check_executable,
    encodeFilename,
    PostProcessingError,
    prepend_extension,
    shell_quote
)


class EmbedThumbnailPPError(PostProcessingError):
    pass


class EmbedThumbnailPP(FFmpegPostProcessor):
    def run(self, info):
        filename = info['filepath']
        temp_filename = prepend_extension(filename, 'temp')
        temp_thumbnail = filename + '.' + determine_ext(info['thumbnail'])

        if not info.get('thumbnail'):
            raise EmbedThumbnailPPError('Thumbnail was not found. Nothing to do.')

        compat_urlretrieve(info['thumbnail'], temp_thumbnail)

        if info['ext'] == 'mp3':
            options = [
                '-i', temp_thumbnail, '-c', 'copy', '-map', '0', '-map', '1',
                '-metadata:s:v', 'title="Album cover"', '-metadata:s:v', 'comment="Cover (Front)"']

            self._downloader.to_screen('[ffmpeg] Adding thumbnail to "%s"' % filename)

            self.run_ffmpeg(filename, temp_filename, options)

            os.remove(encodeFilename(temp_thumbnail))
            os.remove(encodeFilename(filename))
            os.rename(encodeFilename(temp_filename), encodeFilename(filename))

        elif info['ext'] == 'm4a':
            if not check_executable('AtomicParsley', ['-v']):
                raise EmbedThumbnailPPError('AtomicParsley was not found. Please install.')

            cmd = ['AtomicParsley', filename, '--artwork', temp_thumbnail, '-o', temp_filename]

            self._downloader.to_screen('[atomicparsley] Adding thumbnail to "%s"' % filename)

            if self._downloader.params.get('verbose', False):
                self._downloader.to_screen('[debug] AtomicParsley command line: %s' % shell_quote(cmd))

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                msg = stderr.decode('utf-8', 'replace').strip()
                raise EmbedThumbnailPPError(msg)

            os.remove(encodeFilename(temp_thumbnail))
            # for formats that don't support thumbnails (like 3gp) AtomicParsley
            # won't create to the temporary file
            if b'No changes' in stdout:
                self._downloader.report_warning('The file format doesn\'t support embedding a thumbnail')
            else:
                os.remove(encodeFilename(filename))
                os.rename(encodeFilename(temp_filename), encodeFilename(filename))
        else:
            raise EmbedThumbnailPPError('Only mp3 and m4a are supported for thumbnail embedding for now.')

        return [], info
