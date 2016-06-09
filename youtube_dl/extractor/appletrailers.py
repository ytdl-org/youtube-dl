from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    int_or_none,
    unified_strdate,
    parse_duration,
)


class AppleTrailersIE(InfoExtractor):
    IE_NAME = 'appletrailers'
    _VALID_URL = r'https?://(?:www\.|movie)?trailers\.apple\.com/(?:trailers|ca)/(?P<company>[^/]+)/(?P<movie>[^/]+)'
    _TESTS = [{
        'url': 'http://trailers.apple.com/trailers/wb/manofsteel/',
        'info_dict': {
            'id': 'manofsteel',
        },
        'playlist': [
            {
                'md5': 'd97a8e575432dbcb81b7c3acb741f8a8',
                'info_dict': {
                    'id': 'manofsteel-trailer4',
                    'ext': 'mov',
                    'duration': 111,
                    'title': 'Trailer 4',
                    'upload_date': '20130523',
                    'uploader_id': 'wb',
                },
            },
            {
                'md5': 'b8017b7131b721fb4e8d6f49e1df908c',
                'info_dict': {
                    'id': 'manofsteel-trailer3',
                    'ext': 'mov',
                    'duration': 182,
                    'title': 'Trailer 3',
                    'upload_date': '20130417',
                    'uploader_id': 'wb',
                },
            },
            {
                'md5': 'd0f1e1150989b9924679b441f3404d48',
                'info_dict': {
                    'id': 'manofsteel-trailer',
                    'ext': 'mov',
                    'duration': 148,
                    'title': 'Trailer',
                    'upload_date': '20121212',
                    'uploader_id': 'wb',
                },
            },
            {
                'md5': '5fe08795b943eb2e757fa95cb6def1cb',
                'info_dict': {
                    'id': 'manofsteel-teaser',
                    'ext': 'mov',
                    'duration': 93,
                    'title': 'Teaser',
                    'upload_date': '20120721',
                    'uploader_id': 'wb',
                },
            },
        ],
        'expected_warnings': ['Unable to download JSON metadata: HTTP Error 404: Not Found'],
    }, {
        'url': 'http://trailers.apple.com/trailers/magnolia/blackthorn/',
        'info_dict': {
            'id': 'blackthorn',
        },
        'playlist_mincount': 2,
        'expected_warnings': ['Unable to download JSON metadata: HTTP Error 404: Not Found'],
    }, {
        'url': 'http://trailers.apple.com/ca/metropole/autrui/',
        'info_dict': {
            'id': 'autrui',
        },
        'playlist_mincount': 1,
        'expected_warnings': ['Unable to download JSON metadata: HTTP Error 404: Not Found'],
    }, {
        'url': 'http://movietrailers.apple.com/trailers/focus_features/kuboandthetwostrings/',
        'info_dict': {
            'id': 'kuboandthetwostrings',
        },
        'playlist_mincount': 4,
    }]

    _JSON_RE = r'iTunes.playURL\((.*?)\);'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        movie = mobj.group('movie')
        uploader_id = mobj.group('company')

        playlist = []

        def create_playlist_item(source, uncommon={}):
            title = source['title']
            video_id = movie + '-' + re.sub(r'[^a-zA-Z0-9]', '', title).lower()

            item = {
                '_type': 'video',
                'id': video_id,
                'title': title,
                'duration': parse_duration(source['runtime']),
                'upload_date': unified_strdate(source['posted']),
                'uploader_id': uploader_id,
                'http_headers': {
                    'User-Agent': 'QuickTime compatible (youtube-dl)',
                },
            }
            item.update(uncommon)
            return item

        def create_format_item(source, uncommon={}):
            item = {
                # The src is a file pointing to the real video file
                'url': re.sub(r'_(\d*p.mov)' , r'_h\1', source['src']),
                'width': int_or_none(source['width']),
                'height': int_or_none(source['height']),
            }
            item.update(uncommon)
            return item

        # Test for presence of newer JSON format.
        html = self._download_webpage(url, movie, fatal=False)
        film_id = self._search_regex(r"^\s*var\s+FilmId\s*=\s*'(?P<film_id>\d+)'", html, 'FilmId', fatal=False, flags=re.MULTILINE, group='film_id')
        json_data = None
        if film_id:
            data_url = 'http://trailers.apple.com/trailers/feeds/data/%s.json' % film_id
            json_data = self._download_json(data_url, movie, 'Downloading trailer JSON', fatal=False)

        if json_data:
            for clip in json_data['clips']:
                formats = []
                for kind, meta in clip['versions']['enus']['sizes'].items():
                    formats.append(create_format_item(meta, {
                        'format_id': kind,
                    }))
                self._sort_formats(formats)

                playlist.append(create_playlist_item(clip, {
                    'formats': formats,
                    'thumbnail': clip['thumb'],
                }))
        else:
            playlist_url = compat_urlparse.urljoin(url, 'includes/playlists/itunes.inc')

            def fix_html(s):
                s = re.sub(r'(?s)<script[^<]*?>.*?</script>', '', s)
                s = re.sub(r'<img ([^<]*?)/?>', r'<img \1/>', s)
                # The ' in the onClick attributes are not escaped, it couldn't be parsed
                # like: http://trailers.apple.com/trailers/wb/gravity/

                def _clean_json(m):
                    return 'iTunes.playURL(%s);' % m.group(1).replace('\'', '&#39;')
                s = re.sub(self._JSON_RE, _clean_json, s)
                s = '<html>%s</html>' % s
                return s
            doc = self._download_xml(playlist_url, movie, transform_source=fix_html)

            for li in doc.findall('./div/ul/li'):
                on_click = li.find('.//a').attrib['onClick']
                trailer_info_json = self._search_regex(self._JSON_RE,
                                                       on_click, 'trailer info')
                trailer_info = json.loads(trailer_info_json)
                first_url = trailer_info.get('url')
                if not first_url:
                    continue
                thumbnail = li.find('.//img').attrib['src']
                trailer_id = first_url.split('/')[-1].rpartition('_')[0].lower()
                settings_json_url = compat_urlparse.urljoin(url, 'includes/settings/%s.json' % trailer_id)
                settings = self._download_json(settings_json_url, trailer_id, 'Downloading settings json')

                formats = []
                for format in settings['metadata']['sizes']:
                    formats.append(create_format_item(format, {
                        'format': format['type'],
                    }))

                self._sort_formats(formats)

                playlist.append(create_playlist_item(trailer_info, {
                    'formats': formats,
                    'thumbnail': thumbnail,
                }))

        return {
            '_type': 'playlist',
            'id': movie,
            'entries': playlist,
        }


class AppleTrailersSectionIE(InfoExtractor):
    IE_NAME = 'appletrailers:section'
    _SECTIONS = {
        'justadded': {
            'feed_path': 'just_added',
            'title': 'Just Added',
        },
        'exclusive': {
            'feed_path': 'exclusive',
            'title': 'Exclusive',
        },
        'justhd': {
            'feed_path': 'just_hd',
            'title': 'Just HD',
        },
        'mostpopular': {
            'feed_path': 'most_pop',
            'title': 'Most Popular',
        },
        'moviestudios': {
            'feed_path': 'studios',
            'title': 'Movie Studios',
        },
    }
    _VALID_URL = r'https?://(?:www\.)?trailers\.apple\.com/#section=(?P<id>%s)' % '|'.join(_SECTIONS)
    _TESTS = [{
        'url': 'http://trailers.apple.com/#section=justadded',
        'info_dict': {
            'title': 'Just Added',
            'id': 'justadded',
        },
        'playlist_mincount': 80,
    }, {
        'url': 'http://trailers.apple.com/#section=exclusive',
        'info_dict': {
            'title': 'Exclusive',
            'id': 'exclusive',
        },
        'playlist_mincount': 80,
    }, {
        'url': 'http://trailers.apple.com/#section=justhd',
        'info_dict': {
            'title': 'Just HD',
            'id': 'justhd',
        },
        'playlist_mincount': 80,
    }, {
        'url': 'http://trailers.apple.com/#section=mostpopular',
        'info_dict': {
            'title': 'Most Popular',
            'id': 'mostpopular',
        },
        'playlist_mincount': 80,
    }, {
        'url': 'http://trailers.apple.com/#section=moviestudios',
        'info_dict': {
            'title': 'Movie Studios',
            'id': 'moviestudios',
        },
        'playlist_mincount': 80,
    }]

    def _real_extract(self, url):
        section = self._match_id(url)
        section_data = self._download_json(
            'http://trailers.apple.com/trailers/home/feeds/%s.json' % self._SECTIONS[section]['feed_path'],
            section)
        entries = [
            self.url_result('http://trailers.apple.com' + e['location'])
            for e in section_data]
        return self.playlist_result(entries, section, self._SECTIONS[section]['title'])
