from __future__ import unicode_literals

from .common import FileDownloader
from .hls import HlsFD
from .http import HttpFD
from .mplayer import MplayerFD
from .rtmp import RtmpFD
from .f4m import F4mFD

from ..utils import (
    determine_ext,
)


def get_suitable_downloader(info_dict):
    """Get the downloader class that can handle the info dict."""
    url = info_dict['url']
    protocol = info_dict.get('protocol')

    if url.startswith('rtmp'):
        return RtmpFD
    if (protocol == 'm3u8') or (protocol is None and determine_ext(url) == 'm3u8'):
        return HlsFD
    if url.startswith('mms') or url.startswith('rtsp'):
        return MplayerFD
    if determine_ext(url) == 'f4m':
        return F4mFD
    else:
        return HttpFD
