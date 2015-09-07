# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


preferences = {'xl': 4, 'l': 3, 'm': 2, 's': 1, 'xs': 0,}


class NDRBaseIE(InfoExtractor):
    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_data = self._download_json('http://www.ndr.de/%s-ppjson.json' % video_id, video_id, 'Downloading page')

        formats = []
        objetType = json_data.get('config').get('objectType')
        if objetType == 'video':
            for key, f in json_data.get('playlist').items():
                if key != 'config':
                    src = f['src']
                    if '.f4m' in src:
                        formats.extend(self._extract_f4m_formats(src, video_id))
                    elif '.m3u8' in src:
                        formats.extend(self._extract_m3u8_formats(src, video_id))
                    else:
                        quality = f.get('quality')
                        formats.append({
                            'url': src,
                            'format_id': quality,
                            'preference': preferences.get(quality),
                        })
        elif objetType == 'audio':
            for key, f in json_data.get('playlist').items():
                if key != 'config':
                    formats.append({
                        'url': f['src'],
                        'format_id': 'mp3',
                        
                    })
        else:
            raise ExtractorError('No media links available for %s' % video_id)

        self._sort_formats(formats)

        config = json_data.get('playlist').get('config')

        title = config['title']
        duration = int_or_none(config.get('duration'))
        thumbnails = [{
            'id': thumbnail.get('quality'),
            'url': thumbnail.get('src'),
            'preference': preferences.get(thumbnail.get('quality'))
        } for thumbnail in config.get('poster').values()]

        return {
            'id': video_id,
            'title': title,
            'thumbnails': thumbnails,
            'duration': duration,
            'formats': formats,
        }


class NDRIE(NDRBaseIE):
    IE_NAME = 'ndr'
    IE_DESC = 'NDR.de - Mediathek'
    _VALID_URL = r'https?://www\.ndr\.de/.+?,(?P<id>\w+)\.html'

    _TESTS = [
        {
            'url': 'http://www.ndr.de/fernsehen/sendungen/nordmagazin/Kartoffeltage-in-der-Lewitz,nordmagazin25866.html',
            'md5': '5bc5f5b92c82c0f8b26cddca34f8bb2c',
            'note': 'Video file',
            'info_dict': {
                'id': 'nordmagazin25866',
                'ext': 'mp4',
                'title': 'Kartoffeltage in der Lewitz',
                'duration': 166,
            },
            'skip': '404 Not found',
        },
        {
            'url': 'http://www.ndr.de/fernsehen/Party-Poette-und-Parade,hafengeburtstag988.html',
            'md5': 'dadc003c55ae12a5d2f6bd436cd73f59',
            'info_dict': {
                'id': 'hafengeburtstag988',
                'ext': 'mp4',
                'title': 'Party, Pötte und Parade',
                'duration': 3498,
            },
        },
        {
            'url': 'http://www.ndr.de/info/La-Valette-entgeht-der-Hinrichtung,audio51535.html',
            'md5': 'bb3cd38e24fbcc866d13b50ca59307b8',
            'note': 'Audio file',
            'info_dict': {
                'id': 'audio51535',
                'ext': 'mp3',
                'title': 'La Valette entgeht der Hinrichtung',
                'duration': 884,
            }
        }
    ]


class NJoyIE(NDRBaseIE):
    IE_NAME = 'N-JOY'
    _VALID_URL = r'https?://www\.n-joy\.de/.+?,(?P<id>\w+)\.html'

    _TEST = {
        'url': 'http://www.n-joy.de/entertainment/comedy/comedy_contest/Benaissa-beim-NDR-Comedy-Contest,comedycontest2480.html',
        'md5': 'cb63be60cd6f9dd75218803146d8dc67',
        'info_dict': {
            'id': '2480',
            'ext': 'mp4',
            'title': 'Benaissa beim NDR Comedy Contest',
            'duration': 654,
        }
    }
