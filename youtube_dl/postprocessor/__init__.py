from __future__ import unicode_literals

from .embedthumbnail import EmbedThumbnailPP
from .ffmpeg import (
    FFmpegPostProcessor,
    FFmpegEmbedSubtitlePP,
    FFmpegExtractAudioPP,
    FFmpegFixupStretchedPP,
    FFmpegFixupM4aPP,
    FFmpegJoinVideosPP,
    FFmpegMergerPP,
    FFmpegMetadataPP,
    FFmpegVideoConvertorPP,
    FFmpegSubtitlesConvertorPP,
)
from .xattrpp import XAttrMetadataPP
from .execafterdownload import ExecAfterDownloadPP
from .metadatafromtitle import MetadataFromTitlePP


def get_postprocessor(key):
    return globals()[key + 'PP']


__all__ = [
    'EmbedThumbnailPP',
    'ExecAfterDownloadPP',
    'FFmpegEmbedSubtitlePP',
    'FFmpegExtractAudioPP',
    'FFmpegFixupM4aPP',
    'FFmpegFixupStretchedPP',
    'FFmpegJoinVideosPP',
    'FFmpegMergerPP',
    'FFmpegMetadataPP',
    'FFmpegPostProcessor',
    'FFmpegSubtitlesConvertorPP',
    'FFmpegVideoConvertorPP',
    'MetadataFromTitlePP',
    'XAttrMetadataPP',
]
