# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class YouviIE(InfoExtractor):
    _VALID_URL = r'https://youvi.ru/post/(?P<id>.*)'
    _TEST = {
        'url': 'https://youvi.ru/post/Ni2BmFhUwUt',
        'md5': '510062b5b3f32f6ba2f6888607d7a434',
        'info_dict': {
            'id': 'Ni2BmFhUwUt',
            'ext': 'mp4',
            'title': 'TikTok показал собственный спецэффект для IPhone 12 Pro, использующий датчик LiDAR.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._search_regex(
            r'title:"(?P<title>[^"]+)"', webpage, 'title')

        formats = []
        for url_type in ('url', 'hls'):
            url = self._search_regex(
                r'source_file:[^}]+(?:%s):"(?P<url>[^"]+?)"' % url_type,
                webpage, 'youvi-hosted-url', fatal=False)
            if url:
                url = url.replace(r'\u002F', r'/')
                format_entry = {'url': url}
                formats.append(format_entry)
                
        if formats:
            self._sort_formats(formats)
            return {
                'id': video_id,
                'title': title,
                'formats': formats,
            }
        else:
            external_embed = self._search_regex(
                r'service_type:"(?P<embed>[^"]+?)"', webpage, 'external-embed')
            external_id = self._search_regex(
                r'external_id:"(?P<id>[^"]+?)"', webpage, 'external-id')

            if external_embed == 'youtube':
                return self.url_result(external_id, 'Youtube')

            elif external_embed == 'vimeo':
                return self.url_result(
                    'https://vimeo.com/' + external_id, 'Vimeo')
