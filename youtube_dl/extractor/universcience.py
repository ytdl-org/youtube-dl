# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    xpath_text,
    xpath_element,
    xpath_attr,
    clean_html,
    update_url_query,
)


class UniverscienceIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?universcience\.tv/video-.*-(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.universcience.tv/video-haro-sur-les-loups-o-5466.html',
        'info_dict': {
            'id': '5466',
            'duration': 1990,
            'ext': 'mp4',
            'title': 'Haro sur les loups ?',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'startswith:Face au retour',
            'creator': 'Sylvie Allonneau',
            'subtitles': {
                'fr': [{
                    'url': 'http://universcience-webtv2-videos-pad.brainsonic.com/1/20121217-100607/attachedFiles/subtitles/2c4a2240149dbb984edc8afefea23a7c.srt',
                }],
            },
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        APIKey = self._html_search_regex(r'["\']APIKey["\'].*["\'](?P<APIKey>.*)["\']', webpage, 'APIKey', group='APIKey')
        url_get_media = update_url_query(
            'http://universcience-webtv2-services-pad.brainsonic.com/rest/getMedia',
            {'APIKey': APIKey, 'byMediaId': video_id})
        xml = self._download_xml(url_get_media, video_id)
        path_media = xpath_element(xml, './medias/media', fatal=True)

        title = xpath_text(path_media, './title')
        creator = xpath_text(path_media, './author')
        duration = int_or_none(xpath_text(path_media, './length'))
        description = clean_html(xpath_text(path_media, './description'))
        thumbnail = xpath_text(path_media, './thumbnail_url')

        subtitles = {}
        subtitle_urls = path_media.findall('./subtitles/subtitle')
        for subtitle in subtitle_urls:
            lang = subtitle.get('lang')
            subtitles[lang] = [{
                'url': subtitle.text,
            }]

        formats = []
        path_media_source = './medias/media/media_sources/media_source'
        for media_source in xml.findall(path_media_source):
            format_url = xpath_text(media_source, 'source', fatal=True)
            media_label = xpath_attr(media_source, './streaming_type', 'label')
            media_width = int_or_none(self._search_regex(r'(\d*) x \d*', media_label, 'width', default=None))
            media_height = int_or_none(self._search_regex(r'\d* x (\d*)', media_label, 'height', default=None))
            media_label = self._search_regex(
                r'(.*) (\d* x \d*)', media_label, 'media_label', default=media_label, fatal=False)

            if media_label in ('HLS', 'm3u8'):
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', 'm3u8_native', m3u8_id='hds', fatal=False))
            else:
                format_info = {
                    'width': media_width,
                    'height': media_height,
                    'tbr': int_or_none(xpath_attr(media_source, './streaming_type', 'bitrate')),
                    # 'vcodec': xpath_attr -> bug sur regexp?
                    'vcodec': media_source.find('streaming_type').get('html5_codec'),
                    'url': format_url,
                    'format_id': 'http-%s' % media_label,
                }
                formats.append(format_info)

        podcast_url = xpath_text(path_media, './podcast_url')
        if podcast_url is not None:
            formats.append({'format_id': 'podcast', 'vcodec': 'none', 'url': podcast_url})

        self._sort_formats(formats)

        return {
            'id': video_id,
            'duration': duration,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
            'creator': creator,
            'subtitles': subtitles,
        }
