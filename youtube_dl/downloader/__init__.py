from __future__ import unicode_literals

from ..utils import (
    determine_protocol,
)


def get_suitable_downloader(info_dict, params={}):
    info_dict['protocol'] = determine_protocol(info_dict)
    info_copy = info_dict.copy()
    return _get_suitable_downloader(info_copy, params)


# Some of these require get_suitable_downloader
from .common import FileDownloader
from .dash import DashSegmentsFD
from .f4m import F4mFD
from .hls import HlsFD
from .http import HttpFD
from .rtmp import RtmpFD
from .rtsp import RtspFD
from .ism import IsmFD
from .niconico import NiconicoDmcFD
from .external import (
    get_external_downloader,
    FFmpegFD,
)

PROTOCOL_MAP = {
    'rtmp': RtmpFD,
    'm3u8_native': HlsFD,
    'm3u8': FFmpegFD,
    'mms': RtspFD,
    'rtsp': RtspFD,
    'f4m': F4mFD,
    'http_dash_segments': DashSegmentsFD,
    'ism': IsmFD,
    'niconico_dmc': NiconicoDmcFD,
}


def _get_suitable_downloader(info_dict, params={}):
    """Get the downloader class that can handle the info dict."""

    # if (info_dict.get('start_time') or info_dict.get('end_time')) and not info_dict.get('requested_formats') and FFmpegFD.can_download(info_dict):
    #     return FFmpegFD

    external_downloader = params.get('external_downloader')
    if external_downloader is not None:
        ed = get_external_downloader(external_downloader)
        if ed.can_download(info_dict):
            return ed
        # Avoid using unwanted args since external_downloader was rejected
        if params.get('external_downloader_args'):
            params['external_downloader_args'] = None

    protocol = info_dict['protocol']
    if protocol.startswith('m3u8') and info_dict.get('is_live'):
        return FFmpegFD

    if protocol == 'm3u8' and params.get('hls_prefer_native') is True:
        return HlsFD

    if protocol == 'm3u8_native' and params.get('hls_prefer_native') is False:
        return FFmpegFD

    if params.get('_clip_args'):
        return FFmpegFD

    return PROTOCOL_MAP.get(protocol, HttpFD)


__all__ = [
    'get_suitable_downloader',
    'FileDownloader',
]
