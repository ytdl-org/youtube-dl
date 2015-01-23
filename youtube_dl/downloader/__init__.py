from __future__ import unicode_literals

from .common import FileDownloader
from .hls import HlsFD
from .hls import NativeHlsFD
from .http import HttpFD
from .mplayer import MplayerFD
from .rtmp import RtmpFD
from .f4m import F4mFD

from ..utils import (
    determine_protocol,
)

PROTOCOL_MAP = {
    'rtmp': RtmpFD,
    'm3u8_native': NativeHlsFD,
    'm3u8': HlsFD,
    'mms': MplayerFD,
    'rtsp': MplayerFD,
    'f4m': F4mFD,
}


def get_suitable_downloader(info_dict, params={}):
    """Get the downloader class that can handle the info dict."""
    protocol = determine_protocol(info_dict)
    info_dict['protocol'] = protocol

    return PROTOCOL_MAP.get(protocol, HttpFD)


__all__ = [
    'get_suitable_downloader',
    'FileDownloader',
]
