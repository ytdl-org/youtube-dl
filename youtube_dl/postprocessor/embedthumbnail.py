# coding: utf-8
from __future__ import unicode_literals


import os

try:
    import imghdr
    from mutagen.id3 import PictureType, ID3, APIC, ID3NoHeaderError
    from mutagen.mp4 import MP4, MP4Cover, MP4MetadataError
except ImportError:
    raise Exception('[embedthumbnail] Mutagen isn\'t found as a dependency to embed thumbnails!')

from .ffmpeg import FFmpegPostProcessor

from ..utils import (
    encodeFilename,
    PostProcessingError
)


class EmbedThumbnailPPError(PostProcessingError):
    pass


class EmbedThumbnailPP(FFmpegPostProcessor):
    def __init__(self, downloader=None, already_have_thumbnail=False):
        super(EmbedThumbnailPP, self).__init__(downloader)
        self._already_have_thumbnail = already_have_thumbnail

    def run(self, info):
        filename = info['filepath']

        if not info.get('thumbnails'):
            self._downloader.to_screen('[embedthumbnail] There aren\'t any thumbnails to embed')
            return [], info

        thumbnail_filename = info['thumbnails'][-1]['filename']

        if not os.path.exists(encodeFilename(thumbnail_filename)):
            self._downloader.report_warning(
                'Skipping embedding the thumbnail because the file is missing.')
            return [], info

        if info['ext'] == 'mp3':
            try:
                meta = ID3(filename)
            except ID3NoHeaderError:
                raise EmbedThumbnailPPError("MP3 file doesn't have a existing ID3v2 tag.")

            # Appends a Cover-front thumbnail, it's the most common
            # type of thumbnail distributed with.
            meta.add(APIC(
                data=open(thumbnail_filename, 'rb').read(),
                mime='image/' + imghdr.what(thumbnail_filename),
                type=PictureType.COVER_FRONT))

            meta.save()  # Save the changes to file, does in-place replacement.
            self._downloader.to_screen('[mutagen.id3] Merged Thumbnail into "%s"' % filename)

            if not self._already_have_thumbnail:
                os.remove(encodeFilename(thumbnail_filename))

        elif info['ext'] in ['m4a', 'mp4']:
            try:
                meta = MP4(filename)
            except MP4MetadataError:
                raise EmbedThumbnailPPError("MPEG-4 file's atomic structure for embedding isn't correct!")

            # NOTE: the 'covr' atom is a non-standard MPEG-4 atom,
            # Apple iTunes 'M4A' files include the 'moov.udta.meta.ilst' atom.
            meta.tags['covr'] = [MP4Cover(
                data=open(thumbnail_filename, 'rb').read(),
                imageformat=MP4Cover.FORMAT_JPEG if
                imghdr.what(thumbnail_filename) == 'jpeg'
                else MP4Cover.FORMAT_PNG)]

            meta.save()
            self._downloader.to_screen('[mutagen.mp4] Merged thumbnail to "%s"' % filename)

            if not self._already_have_thumbnail:
                os.remove(encodeFilename(thumbnail_filename))
        else:
            raise EmbedThumbnailPPError('Only mp3, m4a/mp4 are supported for thumbnail embedding for now.')

        return [], info
