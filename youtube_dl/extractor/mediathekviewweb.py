import datetime
import itertools
import json
import re

from .common import InfoExtractor, SearchInfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import ExtractorError, int_or_none

class MediathekViewWebSearchIE(SearchInfoExtractor):
    IE_NAME = 'mediathekviewweb:search'
    IE_DESC = 'MediathekViewWeb search'
    _SEARCH_KEY = 'mvwsearch'
    _MAX_RESULTS = float('inf')
    _MAX_RESULTS_PER_PAGE = 50
    # _GEO_COUNTRIES = ['DE']

    # _TESTS = [{
    #     'url': 'mvwsearch:tagesschau',
    #     'info_dict': {
    #         'title': 'post-avant jazzcore',
    #     },
    #     'playlist_count': 15,
    # }]

    # Map of title affixes indicating video variants.
    _variants = {
        'audio_description': '(Audiodeskription)',
        'sign_language': '(mit Gebärdensprache)',
    }

    def _build_conditions(self, search):
        # @note So far, there is no API endpoint to convert a query string into
        #   a complete query object, as required by the /api/query endpoint.
        # @see https://github.com/mediathekview/mediathekviewweb/blob/master/client/index.ts#L144
        #   for parsing the search string into properties.
        # @see https://github.com/mediathekview/mediathekviewweb/blob/master/client/index.ts#L389
        #   for converting properties into field queries.
        filters = {}
        extra = {}
        for component in search.lower().split():
            if len(component) == 0:
                continue

            field = None
            operator = component[0:1]
            value = component[1:]
            # Extra, non-field settings.
            if operator == '>':
                value = int(value.split(',')[0]) * 60
                extra['duration_min'] = max(extra.get('duration_min', 0), value)
                continue
            elif operator == '<':
                value = int(value.split(',')[0]) * 60
                extra['duration_max'] = min(extra.get('duration_max', float('inf')), value)
                continue

            # Field query operators.
            elif operator == '!':
                field = 'channel'
            elif operator == '#':
                field = 'topic'
            elif operator == '+':
                field = 'title'
            elif operator == '*':
                field = 'description'
            else:
                field = 'topic,title'
                operator = ''
                value = component

            if field:
                # @todo In theory, comma-joined values are for AND queries.
                #   But so far, each is an AND component, even without comma.
                filters.setdefault(field, []).append(' '.join(value.split(',')))

        conditions = []
        for field, keys in filters.items():
            for query in keys:
                conditions.append({
                    'fields': field.split(','),
                    'query': query,
                })

        return conditions, extra

    def _extract_playlist_entries(self, results):
        entries = []
        for item in results:
            variant = None
            for key, value in self._variants.items():
                if item['title'].find(value) != -1:
                    variant = key

            formats = []
            formats.append({
                'url': item['url_video'],
                'format': ('medium ' + self._variants[variant]) if variant else None,
                'format_id': ('medium-' + variant) if variant else 'medium',
                'language_preference': -10 if variant else 10,
                'quality': -2,
                'filesize': item['size'],
            })
            if len(item.get('url_video_low', '')) > 0:
                formats.append({
                    'url': item['url_video_low'],
                    'format': ('low ' + self._variants[variant]) if variant else None,
                    'format_id': ('low-' + variant) if variant else 'low',
                    'language_preference': -10 if variant else 10,
                    'quality': -3,
                })
            if len(item.get('url_video_hd', '')) > 0:
                formats.append({
                    'url': item['url_video_hd'],
                    'format': ('high ' + self._variants[variant]) if variant else None,
                    'format_id': ('high-' + variant) if variant else 'high',
                    'language_preference': -10 if variant else 10,
                    'quality': -1,
                })
            self._sort_formats(formats)

            video = {
                '_type': 'video',
                'formats': formats,
                'id': item['id'],
                'title': item['title'],
                'description': item['description'],
                'series': item['topic'],
                'channel': item['channel'],
                'uploader': item['channel'],
                'duration': int_or_none(item['duration']),
                'webpage_url': item['url_website'],
            }

            upload_date = datetime.datetime.utcfromtimestamp(item['timestamp'])
            video['upload_date'] = upload_date.strftime('%Y%m%d')
            if item['url_subtitle']:
                video.setdefault('subtitles', {}).setdefault('de', []).append({
                    'url': item['url_subtitle'],
                })
            entries.append(video)

        return entries

    def _get_n_results(self, query, n):
        # @todo Add support for everywhere/future options.
        queries, extra = self._build_conditions(query)
        queryObject = {
            'queries': queries,
            'sortBy': 'timestamp',
            'sortOrder': 'desc',
            'future': True,
            'duration_min': extra.get('duration_min'),
            'duration_max': extra.get('duration_max'),
            'offset': 0,
            'size': min(n, self._MAX_RESULTS_PER_PAGE),
        }

        entries = []
        for page_num in itertools.count(1):
            queryObject.update({'offset': (page_num - 1) * queryObject['size']})
            results = self._download_json('https://mediathekviewweb.de/api/query', query,
                note='Fetching page %d' % page_num,
                data=json.dumps(queryObject).encode('utf-8'),
                headers={'Content-Type': 'text/plain'})
            if results['err'] is not None:
                raise ExtractorError('API returned an error: %s' % results['err'][0])
            entries.extend(self._extract_playlist_entries(results['result']['results']))

            meta = results['result']['queryInfo']
            # @todo This returns full pages: 100 results if 51 are requested.
            if len(entries) >= n or meta['resultCount'] == 0:
                break

        return self.playlist_result(entries, playlist_title=query)

class MediathekViewWebIE(InfoExtractor):
    # @see https://github.com/mediathekview/mediathekviewweb
    IE_NAME = 'mediathekviewweb'
    _VALID_URL = r'https?://mediathekviewweb\.de/\#query=(?P<id>.+)'

    # @todo Specify test cases.
    def _real_extract(self, url):
        query = self._match_id(url)
        search = compat_urllib_parse_unquote(query)
        return {
            '_type': 'url',
            'url': 'mvwsearchall:' + search,
            'ie_key': 'MediathekViewWebSearch',
        }
