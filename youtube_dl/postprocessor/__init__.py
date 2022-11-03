from __future__ import unicode_literals

from .embedthumbnail import EmbedThumbnailPP
from .execafterdownload import ExecAfterDownloadPP
from .ffmpeg import (FFmpegEmbedSubtitlePP, FFmpegExtractAudioPP,
                     FFmpegFixupM3u8PP, FFmpegFixupM4aPP,
                     FFmpegFixupStretchedPP, FFmpegMergerPP, FFmpegMetadataPP,
                     FFmpegPostProcessor, FFmpegSubtitlesConvertorPP,
                     FFmpegVideoConvertorPP)
from .metadatafromtitle import MetadataFromTitlePP
from .xattrpp import XAttrMetadataPP


def get_postprocessor(key):
    return globals()[key + 'PP']


__all__ = [
    'EmbedThumbnailPP',
    'ExecAfterDownloadPP',
    'FFmpegEmbedSubtitlePP',
    'FFmpegExtractAudioPP',
    'FFmpegFixupM3u8PP',
    'FFmpegFixupM4aPP',
    'FFmpegFixupStretchedPP',
    'FFmpegMergerPP',
    'FFmpegMetadataPP',
    'FFmpegPostProcessor',
    'FFmpegSubtitlesConvertorPP',
    'FFmpegVideoConvertorPP',
    'MetadataFromTitlePP',
    'XAttrMetadataPP',
]
