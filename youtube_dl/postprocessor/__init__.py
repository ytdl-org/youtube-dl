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
)
from .xattrpp import XAttrMetadataPP
from .execafterdownload import ExecAfterDownloadPP


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
    'FFmpegVideoConvertorPP',
    'XAttrMetadataPP',
]
