from __future__ import unicode_literals

from .common import FileDownloader
from .external import get_external_downloader
from .f4m import F4mFD
from .hls import HlsFD
from .hls import NativeHlsFD
from .http import HttpFD
from .rtsp import RtspFD
from .rtmp import RtmpFD
from .dash import DashSegmentsFD

from ..utils import (
    determine_protocol,
)

PROTOCOL_MAP = {
    'rtmp': RtmpFD,
    'm3u8_native': NativeHlsFD,
    'm3u8': HlsFD,
    'mms': RtspFD,
    'rtsp': RtspFD,
    'f4m': F4mFD,
    'http_dash_segments': DashSegmentsFD,
}


def get_suitable_downloader(info_dict, params={}):
    """Get the downloader class that can handle the info dict."""
    protocol = determine_protocol(info_dict)
    info_dict['protocol'] = protocol

    external_downloader = params.get('external_downloader')
    if external_downloader is not None:
        ed = get_external_downloader(external_downloader)
        if ed.supports(info_dict):
            return ed

    if protocol == 'm3u8' and params.get('hls_prefer_native'):
        return NativeHlsFD

    return PROTOCOL_MAP.get(protocol, HttpFD)


__all__ = [
    'get_suitable_downloader',
    'FileDownloader',
]
