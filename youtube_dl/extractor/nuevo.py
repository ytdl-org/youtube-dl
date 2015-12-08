# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import float_or_none

class NuevoBaseIE(InfoExtractor):
    def _extract_nuevo(self, config_url, video_id, info=None, ignore_hd=False):
        if info is None:
            info = {}

        sdformats, hdformats = [], []
        tree = self._download_xml(config_url, video_id, transform_source=lambda s: s.strip())

        for child in tree:
            tag, val = child.tag, child.text

            if tag == "file":
                sdformats.append({"url": val})
            elif tag == "filehd" and not ignore_hd:
                hdformats.append({"url": val})
            elif tag == "duration":
                info["duration"] = float_or_none(val)
            elif tag == "image":
                info["thumbnail"] = val
            elif tag == "title":
                info["title"] = val.strip()

        info["id"] = video_id
        info["formats"] = sdformats + hdformats

        return info
