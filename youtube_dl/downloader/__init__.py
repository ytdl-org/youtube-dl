from .common import FileDownloader
from .hls import HlsFD
from .http import HttpFD
from .mplayer import MplayerFD
from .rtmp import RtmpFD

from ..utils import (
    determine_ext,
)

def get_suitable_downloader(info_dict):
    """Get the downloader class that can handle the info dict."""
    url = info_dict['url']

    if url.startswith('rtmp'):
        return RtmpFD
    if determine_ext(url) == u'm3u8':
        return HlsFD
    if url.startswith('mms') or url.startswith('rtsp'):
        return MplayerFD
    else:
        return HttpFD

