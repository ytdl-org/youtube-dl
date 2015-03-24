from __future__ import unicode_literals

from .atomicparsley import AtomicParsleyPP
from .ffmpeg import (
    FFmpegPostProcessor,
    FFmpegAudioFixPP,
    FFmpegEmbedSubtitlePP,
    FFmpegExtractAudioPP,
    FFmpegFixupStretchedPP,
    FFmpegFixupM4aPP,
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
    'AtomicParsleyPP',
    'ExecAfterDownloadPP',
    'FFmpegAudioFixPP',
    'FFmpegEmbedSubtitlePP',
    'FFmpegExtractAudioPP',
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
