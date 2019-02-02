# coding: utf-8
from __future__ import unicode_literals
from ..utils import (
    int_or_none,
    unified_timestamp,
    ExtractorError
)
from .common import InfoExtractor


class PictaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?picta\.cu/medias/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.picta.cu/medias/818',
        'file': 'Orishas - Everyday-818.webm',
        'md5': 'ebd10d5a34f23059e08419aa123aebdb',
        'info_dict': {
            'id': '818',
            'ext': 'webm',
            'title': 'Orishas - Everyday',
            'thumbnail': r're:^https?://.*imagen/img.*\.png$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        # https://www.picta.cu/api/v1/publicacion/?id_publicacion=818&tipo=publicacion
        # https://www.picta.cu/api/v1/publicacion/?format=json&id_publicacion=818&tipo=publicacion
        json_url = 'https://www.picta.cu/api/v1/publicacion/?format=json&id_publicacion=' + \
                   str(video_id) + '&tipo=publicacion'
        # JSON MetaFields
        meta = self._download_json(json_url, video_id)
        # Fields
        title = meta.get('results')[0].get('nombre') or self._search_regex(
            r'<h5[^>]+class="post-video-title"[^>]*>([^<]+)', webpage, 'title')
        description = meta.get('results')[0].get('descripcion')
        uploader = meta.get('results')[0].get('usuario')
        add_date = meta.get('results')[0].get('fecha_creacion')
        timestamp = int_or_none(unified_timestamp(add_date))
        thumbnail = meta.get('results')[0].get('url_imagen')
        manifest_url = meta.get('results')[0].get('url_manifiesto')
        # Formats
        formats = []
        # MPD manifest
        if manifest_url:
            formats.extend(self._extract_mpd_formats(manifest_url, video_id))
        if not formats:
            raise ExtractorError('Cannot find video formats')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'uploader': uploader,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
        }
