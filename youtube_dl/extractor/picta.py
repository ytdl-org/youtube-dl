# coding: utf-8
from __future__ import unicode_literals
from ..compat import compat_str
from ..utils import (
    int_or_none,
    unified_timestamp,
    try_get,
    ExtractorError
)
from .common import InfoExtractor


class PictaBaseIE(InfoExtractor):
    def _extract_video(self, video, video_id=None, require_title=True):
        title = video['results'][0]['nombre'] if require_title else video.get('results')[0].get('nombre')
        description = try_get(video, lambda x: x['results'][0]['descripcion'], compat_str)
        uploader = try_get(video, lambda x: x['results'][0]['usuario'], compat_str)
        add_date = try_get(video, lambda x: x['results'][0]['fecha_creacion'])
        timestamp = int_or_none(unified_timestamp(add_date))
        thumbnail = try_get(video, lambda x: x['results'][0]['url_imagen'])
        manifest_url = try_get(video, lambda x: x['results'][0]['url_manifiesto'])
        category = try_get(video, lambda x: x['results'][0]['canal'], compat_str)

        return {
            'id': try_get(video, lambda x: x['results'][0]['id'], compat_str) or video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'timestamp': timestamp,
            'category': [category] if category else None,
            'manifest_url': manifest_url,
        }


class PictaIE(PictaBaseIE):
    IE_NAME = 'picta'
    IE_DESC = 'Picta videos'
    _VALID_URL = r'https?://(?:www\.)?picta\.cu/(?:medias|embed)/(?:\?v=)?(?P<id>[0-9]+)'

    _TESTS = [{
        'url': 'https://www.picta.cu/medias/818',
        'file': 'Orishas - Everyday-818.webm',
        'md5': 'ebd10d5a34f23059e08419aa123aebdb',
        'info_dict': {
            'id': '818',
            'ext': 'webm',
            'title': 'Orishas - Everyday',
            'thumbnail': r're:^https?://.*imagen/img.*\.png$',
        }
    }, {
        'url': 'https://www.picta.cu/embed/?v=818',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        api_url = 'https://www.picta.cu/api/v1/publicacion/'
        json_url = api_url + '?format=json&id_publicacion=%s&tipo=publicacion' % video_id

        video = self._download_json(json_url, video_id, 'Downloading video JSON')

        info = self._extract_video(video, video_id)

        formats = []
        # MPD manifest
        if info.get('manifest_url'):
            formats.extend(self._extract_mpd_formats(info.get('manifest_url'), video_id))
        if not formats:
            raise ExtractorError('Cannot find video formats')

        self._sort_formats(formats)

        info['formats'] = formats
        return info


class PictaEmbedIE(InfoExtractor):
    IE_NAME = 'picta:embed'
    IE_DESC = 'Picta embedded videos'
    _VALID_URL = r'https?://www\.picta\.cu/embed/\?v=(?P<id>[0-9]+)'

    _TEST = {
        'url': 'https://www.picta.cu/embed/?v=818',
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
        embed_id = self._match_id(url)
        video_url = 'https://www.picta.cu/medias/%s' % embed_id
        return self.url_result(video_url, PictaIE.ie_key())
