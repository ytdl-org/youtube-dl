# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    float_or_none,
    xpath_text
)


class NuevoBaseIE(InfoExtractor):
    def _extract_nuevo(self, config_url, video_id):
        tree = self._download_xml(config_url, video_id, transform_source=lambda s: s.strip())

        title = xpath_text(tree, './title')
        if title:
            title = title.strip()

        thumbnail = xpath_text(tree, './image')
        duration = float_or_none(xpath_text(tree, './duration'))

        formats = []
        for element_name, format_id in (('file', 'sd'), ('filehd', 'hd')):
            video_url = tree.find(element_name)
            video_url is None or formats.append({
                'format_id': format_id,
                'url': video_url.text
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats
        }
