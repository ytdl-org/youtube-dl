from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
    unescapeHTML,
)


class WistiaIE(InfoExtractor):
    _VALID_URL = r'(?:wistia:|https?://(?:fast\.)?wistia\.(?:net|com)/embed/(?:iframe|medias)/)(?P<id>[a-z0-9]{10})'
    _EMBED_BASE_URL = 'http://fast.wistia.com/embed/'

    _TESTS = [{
        'url': 'http://fast.wistia.net/embed/iframe/sh7fpupwlt',
        'md5': 'cafeb56ec0c53c18c97405eecb3133df',
        'info_dict': {
            'id': 'sh7fpupwlt',
            'ext': 'mov',
            'title': 'Being Resourceful',
            'description': 'a Clients From Hell Video Series video from worldwidewebhosting',
            'upload_date': '20131204',
            'timestamp': 1386185018,
            'duration': 117,
        },
    }, {
        'url': 'wistia:sh7fpupwlt',
        'only_matching': True,
    }, {
        # with hls video
        'url': 'wistia:807fafadvk',
        'only_matching': True,
    }, {
        'url': 'http://fast.wistia.com/embed/iframe/sh7fpupwlt',
        'only_matching': True,
    }, {
        'url': 'http://fast.wistia.net/embed/medias/sh7fpupwlt.json',
        'only_matching': True,
    }]

    # https://wistia.com/support/embed-and-share/video-on-your-website
    @staticmethod
    def _extract_url(webpage):
        urls = WistiaIE._extract_urls(webpage)
        return urls[0] if urls else None

    @staticmethod
    def _extract_urls(webpage):
        urls = []
        for match in re.finditer(
                r'<(?:meta[^>]+?content|(?:iframe|script)[^>]+?src)=["\'](?P<url>(?:https?:)?//(?:fast\.)?wistia\.(?:net|com)/embed/(?:iframe|medias)/[a-z0-9]{10})', webpage):
            urls.append(unescapeHTML(match.group('url')))
        for match in re.finditer(
                r'''(?sx)
                    <div[^>]+class=(["'])(?:(?!\1).)*?\bwistia_async_(?P<id>[a-z0-9]{10})\b(?:(?!\1).)*?\1
                ''', webpage):
            urls.append('wistia:%s' % match.group('id'))
        for match in re.finditer(r'(?:data-wistia-?id=["\']|Wistia\.embed\(["\']|id=["\']wistia_)(?P<id>[a-z0-9]{10})', webpage):
            urls.append('wistia:%s' % match.group('id'))
        return urls

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data_json = self._download_json(
            self._EMBED_BASE_URL + 'medias/%s.json' % video_id, video_id,
            # Some videos require this.
            headers={
                'Referer': url if url.startswith('http') else self._EMBED_BASE_URL + 'iframe/' + video_id,
            })

        if data_json.get('error'):
            raise ExtractorError(
                'Error while getting the playlist', expected=True)

        data = data_json['media']
        title = data['name']

        formats = []
        thumbnails = []
        for a in data['assets']:
            aurl = a.get('url')
            if not aurl:
                continue
            astatus = a.get('status')
            atype = a.get('type')
            if (astatus is not None and astatus != 2) or atype in ('preview', 'storyboard'):
                continue
            elif atype in ('still', 'still_image'):
                thumbnails.append({
                    'url': aurl,
                    'width': int_or_none(a.get('width')),
                    'height': int_or_none(a.get('height')),
                    'filesize': int_or_none(a.get('size')),
                })
            else:
                aext = a.get('ext')
                display_name = a.get('display_name')
                format_id = atype
                if atype and atype.endswith('_video') and display_name:
                    format_id = '%s-%s' % (atype[:-6], display_name)
                f = {
                    'format_id': format_id,
                    'url': aurl,
                    'tbr': int_or_none(a.get('bitrate')) or None,
                    'preference': 1 if atype == 'original' else None,
                }
                if display_name == 'Audio':
                    f.update({
                        'vcodec': 'none',
                    })
                else:
                    f.update({
                        'width': int_or_none(a.get('width')),
                        'height': int_or_none(a.get('height')),
                        'vcodec': a.get('codec'),
                    })
                if a.get('container') == 'm3u8' or aext == 'm3u8':
                    ts_f = f.copy()
                    ts_f.update({
                        'ext': 'ts',
                        'format_id': f['format_id'].replace('hls-', 'ts-'),
                        'url': f['url'].replace('.bin', '.ts'),
                    })
                    formats.append(ts_f)
                    f.update({
                        'ext': 'mp4',
                        'protocol': 'm3u8_native',
                    })
                else:
                    f.update({
                        'container': a.get('container'),
                        'ext': aext,
                        'filesize': int_or_none(a.get('size')),
                    })
                formats.append(f)

        self._sort_formats(formats)

        subtitles = {}
        for caption in data.get('captions', []):
            language = caption.get('language')
            if not language:
                continue
            subtitles[language] = [{
                'url': self._EMBED_BASE_URL + 'captions/' + video_id + '.vtt?language=' + language,
            }]

        return {
            'id': video_id,
            'title': title,
            'description': data.get('seoDescription'),
            'formats': formats,
            'thumbnails': thumbnails,
            'duration': float_or_none(data.get('duration')),
            'timestamp': int_or_none(data.get('createdAt')),
            'subtitles': subtitles,
        }
