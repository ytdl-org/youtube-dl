# coding: utf-8
from __future__ import unicode_literals
from ..compat import compat_str
from ..utils import (
    int_or_none,
    unified_timestamp,
    try_get,
    base_url,
    ExtractorError
)
from .common import InfoExtractor


class PictaBaseIE(InfoExtractor):
    API_BASE_URL = 'https://api.picta.cu/api/v1/'

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
    _VALID_URL = r'https?://(?:www\.)?picta\.cu/(?:medias|embed)/(?:\?v=)?(?P<id>[\da-z-]+)'
    _formats = {
        # Dash webm
        '0': {'ext': 'webm', 'height': 144, 'format_note': 'DASH video', 'container': 'webm', 'vcodec': 'vp9'},
        '1': {'ext': 'webm', 'height': 240, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '2': {'ext': 'webm', 'height': 360, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '3': {'ext': 'webm', 'height': 480, 'format_note': 'DASH video', 'vcodec': 'vp9'},
        '4': {'ext': 'webm', 'height': 720, 'format_note': 'DASH video', 'vcodec': 'vp9'},

        # Dash webm audio with opus inside
        '5': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 128},
        '6': {'ext': 'webm', 'format_note': 'DASH audio', 'acodec': 'opus', 'abr': 134},

    }

    _TESTS = [{
        'url': 'https://www.picta.cu/medias/orishas-everyday-2019-01-16-16-36-42-443003',
        'file': 'Orishas - Everyday-orishas-everyday-2019-01-16-16-36-42-443003.webm',
        'md5': '7ffdeb0043500c4bb660c04e74e90f7a',
        'info_dict': {
            'id': 'orishas-everyday-2019-01-16-16-36-42-443003',
            'ext': 'webm',
            'title': 'Orishas - Everyday',
            'thumbnail': r're:^https?://.*imagen/img.*\.png$',
            'upload_date': '20190116',
            'description': 'Orishas - Everyday (Video Oficial)',
            'uploader': 'admin',
            'timestamp': 1547656602,
        },
        'params': {
            'format': '4',
        },
    }, {
        'url': 'https://www.picta.cu/embed/?v=818',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        if base_url(url).find('medias') != -1:
            json_url = self.API_BASE_URL + 'publicacion/?format=json&slug_url=%s&tipo=publicacion' % video_id
        else:
            json_url = self.API_BASE_URL + 'publicacion/?format=json&id_publicacion=%s&tipo=publicacion' % video_id

        video = self._download_json(json_url, video_id, 'Downloading video JSON')

        info = self._extract_video(video, video_id)

        formats = []
        # MPD manifest
        if info.get('manifest_url'):
            formats.extend(self._extract_mpd_formats(info.get('manifest_url'), video_id, formats_dict=self._formats))
            # Fix some Picta DASH video vp09.00.[dd].08 for 'vcodec': 'vp9', 'acodec':'none'
            for f in formats:
                if f.get('acodec') is None and f.get('vcodec') == 'none':
                    f.update({'vcodec':'vp9'})
                    f.update({'acodec':'none'})
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
        'file': 'Orishas - Everyday-orishas-everyday-2019-01-16-16-36-42-443003.webm',
        'md5': '7ffdeb0043500c4bb660c04e74e90f7a',
        'info_dict': {
            'id': 'orishas-everyday-2019-01-16-16-36-42-443003',
            'ext': 'webm',
            'title': 'Orishas - Everyday',
            'thumbnail': r're:^https?://.*imagen/img.*\.png$',
            'upload_date': '20190116',
            'description': 'Orishas - Everyday (Video Oficial)',
            'uploader': 'admin',
            'timestamp': 1547656602,
        },
        'params': {
            'format': '4',
        },
    }

    def _real_extract(self, url):
        return self.url_result(url, PictaIE.ie_key())
