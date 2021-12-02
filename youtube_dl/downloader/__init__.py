from __future__ import unicode_literals

from .common import FileDownloader
from .f4m import F4mFD
from .hls import HlsFD
from .http import HttpFD
from .rtmp import RtmpFD
from .dash import DashSegmentsFD
from .rtsp import RtspFD
from .ism import IsmFD
from .external import (
    get_external_downloader,
    FFmpegFD,
)

from ..utils import (
    determine_protocol,
    ExternalDownloaderError,
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
}


def get_suitable_downloader(info_dict, ydl, params={}):
    """Get the downloader class that can handle the info dict."""
    protocol = determine_protocol(info_dict)
    info_dict['protocol'] = protocol

    # if (info_dict.get('start_time') or info_dict.get('end_time')) and not info_dict.get('requested_formats') and FFmpegFD.can_download(info_dict):
    #     return FFmpegFD

    external_downloader = params.get('external_downloader')
    if external_downloader is not None:
        ed = get_external_downloader(external_downloader)
        if not ed:
            raise ExternalDownloaderError(
                'unknown/unsupported external downloader %s specified' % external_downloader)
        if not ed.available():
            raise ExternalDownloaderError(
                'external downloader %s not found in PATH' % external_downloader)
        if ed.supports(info_dict):
            return ed
        else:
            ydl.report_warning(
                'external downloader %s is not used for protocol %s' % (external_downloader, protocol))

    if protocol.startswith('m3u8') and info_dict.get('is_live'):
        return FFmpegFD

    if protocol == 'm3u8' and params.get('hls_prefer_native') is True:
        return HlsFD

    if protocol == 'm3u8_native' and params.get('hls_prefer_native') is False:
        return FFmpegFD

    return PROTOCOL_MAP.get(protocol, HttpFD)


__all__ = [
    'get_suitable_downloader',
    'FileDownloader',
]
