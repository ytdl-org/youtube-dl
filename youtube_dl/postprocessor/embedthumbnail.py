# coding: utf-8
from __future__ import unicode_literals


import os
import subprocess

from .ffmpeg import FFmpegPostProcessor

from ..utils import (
    check_executable,
    encodeArgument,
    encodeFilename,
    PostProcessingError,
    prepend_extension,
    shell_quote
)


class EmbedThumbnailPPError(PostProcessingError):
    pass


class EmbedThumbnailPP(FFmpegPostProcessor):
    def __init__(self, downloader=None, already_have_thumbnail=False):
        super(EmbedThumbnailPP, self).__init__(downloader)
        self._already_have_thumbnail = already_have_thumbnail

    def run(self, info):
        filename = info['filepath']
        temp_filename = prepend_extension(filename, 'temp')

        if not info.get('thumbnails'):
            self._downloader.to_screen('[embedthumbnail] There aren\'t any thumbnails to embed')
            return [], info

        thumbnail_filename = info['thumbnails'][-1]['filename']

        if not os.path.exists(encodeFilename(thumbnail_filename)):
            self._downloader.report_warning(
                'Skipping embedding the thumbnail because the file is missing.')
            return [], info

        # Check for mislabeled webp file
        with open(encodeFilename(thumbnail_filename), "rb") as f:
            b = f.read(16)
        if b'\x57\x45\x42\x50' in b:  # Binary for WEBP
            [thumbnail_filename_path, thumbnail_filename_extension] = os.path.splitext(thumbnail_filename)
            if not thumbnail_filename_extension == ".webp":
                webp_thumbnail_filename = thumbnail_filename_path + ".webp"
                os.rename(encodeFilename(thumbnail_filename), encodeFilename(webp_thumbnail_filename))
                thumbnail_filename = webp_thumbnail_filename

        # If not a jpg or png thumbnail, convert it to jpg using ffmpeg
        if not os.path.splitext(thumbnail_filename)[1].lower() in ['.jpg', '.png']:
            jpg_thumbnail_filename = os.path.splitext(thumbnail_filename)[0] + ".jpg"
            jpg_thumbnail_filename = os.path.join(os.path.dirname(jpg_thumbnail_filename), os.path.basename(jpg_thumbnail_filename).replace('%', '_'))  # ffmpeg interprets % as image sequence

            self._downloader.to_screen('[ffmpeg] Converting thumbnail "%s" to JPEG' % thumbnail_filename)

            self.run_ffmpeg(thumbnail_filename, jpg_thumbnail_filename, ['-bsf:v', 'mjpeg2jpeg'])

            os.remove(encodeFilename(thumbnail_filename))
            thumbnail_filename = jpg_thumbnail_filename

        if info['ext'] == 'mp3':
            options = [
                '-c', 'copy', '-map', '0', '-map', '1',
                '-metadata:s:v', 'title="Album cover"', '-metadata:s:v', 'comment="Cover (Front)"']

            self._downloader.to_screen('[ffmpeg] Adding thumbnail to "%s"' % filename)

            self.run_ffmpeg_multiple_files([filename, thumbnail_filename], temp_filename, options)

            if not self._already_have_thumbnail:
                os.remove(encodeFilename(thumbnail_filename))
            os.remove(encodeFilename(filename))
            os.rename(encodeFilename(temp_filename), encodeFilename(filename))

        elif info['ext'] in ['m4a', 'mp4']:
            if not check_executable('AtomicParsley', ['-v']):
                raise EmbedThumbnailPPError('AtomicParsley was not found. Please install.')

            cmd = [encodeFilename('AtomicParsley', True),
                   encodeFilename(filename, True),
                   encodeArgument('--artwork'),
                   encodeFilename(thumbnail_filename, True),
                   encodeArgument('-o'),
                   encodeFilename(temp_filename, True)]

            self._downloader.to_screen('[atomicparsley] Adding thumbnail to "%s"' % filename)

            if self._downloader.params.get('verbose', False):
                self._downloader.to_screen('[debug] AtomicParsley command line: %s' % shell_quote(cmd))

            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()

            if p.returncode != 0:
                msg = stderr.decode('utf-8', 'replace').strip()
                raise EmbedThumbnailPPError(msg)

            if not self._already_have_thumbnail:
                os.remove(encodeFilename(thumbnail_filename))
            # for formats that don't support thumbnails (like 3gp) AtomicParsley
            # won't create to the temporary file
            if b'No changes' in stdout:
                self._downloader.report_warning('The file format doesn\'t support embedding a thumbnail')
            else:
                os.remove(encodeFilename(filename))
                os.rename(encodeFilename(temp_filename), encodeFilename(filename))
        else:
            raise EmbedThumbnailPPError('Only mp3 and m4a/mp4 are supported for thumbnail embedding for now.')

        return [], info
