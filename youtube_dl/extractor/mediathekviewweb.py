import datetime
import itertools
import json

from .common import InfoExtractor, SearchInfoExtractor
from ..compat import compat_parse_qs, compat_urlparse
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
        'audio_description': 'Audiodeskription',
        'sign_language': 'mit Gebärdensprache',
    }
    _future = True
    _everywhere = False

    def _build_conditions(self, search):
        # @note So far, there is no API endpoint to convert a query string into
        #   a complete query object, as required by the /api/query endpoint.
        filters = {}
        extra = {}

        for component in search.lower().split():
            if len(component) == 0:
                continue

            operator = component[0:1]
            value = component[1:]
            if len(value) == 0:
                # Treat single character query as such.
                # @note This differs from MVW's implementation.
                operator = ''
                value = component

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
            if operator == '!':
                field = 'channel'
            elif operator == '#':
                field = 'topic'
            elif operator == '+':
                field = 'title'
            elif operator == '*':
                field = 'description'
            else:
                # No known operator specified.
                field = 'generic'
                value = component

            # @note In theory, comma-joined values are for AND queries. However
            #   so far, each condition is AND joined, even without comma.
            filters.setdefault(field, []).append(' '.join(value.split(',')))

        # Generic filters can apply to different fields, based on the query.
        if 'generic' in filters:
            if self._everywhere:
                filters['channel,topic,title,description'] = filters['generic']
            elif 'topic' in filters:
                filters['title'] = filters['generic']
            else:
                filters['topic,title'] = filters['generic']
            filters.pop('generic')

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
                if item.setdefault('title', '').find(value) != -1:
                    variant = key

            formats = []
            formats.append({
                'url': item['url_video'],
                'format': ('medium (' + self._variants[variant] + ')') if variant else None,
                'format_id': ('medium-' + variant) if variant else 'medium',
                'language_preference': -10 if variant else 10,
                'quality': -2,
                'filesize': item.get('size'),
            })
            if len(item.get('url_video_low', '')) > 0:
                formats.append({
                    'url': item['url_video_low'],
                    'format': ('low (' + self._variants[variant] + ')') if variant else None,
                    'format_id': ('low-' + variant) if variant else 'low',
                    'language_preference': -10 if variant else 10,
                    'quality': -3,
                })
            if len(item.get('url_video_hd', '')) > 0:
                formats.append({
                    'url': item['url_video_hd'],
                    'format': ('high (' + self._variants[variant] + ')') if variant else None,
                    'format_id': ('high-' + variant) if variant else 'high',
                    'language_preference': -10 if variant else 10,
                    'quality': -1,
                })
            self._sort_formats(formats)

            video = {
                '_type': 'video',
                'formats': formats,
                'id': item.get('id'),
                'title': item.get('title'),
                'description': item.get('description'),
                'series': item.get('topic'),
                'channel': item.get('channel'),
                'uploader': item.get('channel'),
                'duration': int_or_none(item.get('duration')),
                'webpage_url': item.get('url_website'),
            }

            if item.get('timestamp'):
                upload_date = datetime.datetime.utcfromtimestamp(item['timestamp'])
                video['upload_date'] = upload_date.strftime('%Y%m%d')
            if item.get('url_subtitle'):
                video.setdefault('subtitles', {}).setdefault('de', []).append({
                    'url': item.get('url_subtitle'),
                })
            entries.append(video)

        return entries

    def _get_n_results(self, query, n):
        queries, extra = self._build_conditions(query)
        queryObject = {
            'queries': queries,
            'sortBy': 'timestamp',
            'sortOrder': 'desc',
            'future': self._future,
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
            if len(entries) >= n:
                entries = entries[:n]
                break
            elif meta['resultCount'] == 0:
                break

        return self.playlist_result(entries, playlist_title=query)


class MediathekViewWebIE(InfoExtractor):
    # @see https://github.com/mediathekview/mediathekviewweb
    IE_NAME = 'mediathekviewweb'
    _VALID_URL = r'https?://mediathekviewweb\.de/\#query=(?P<id>.+)'

    # @todo Specify test cases.
    # https://mediathekviewweb.de/#query=%23tagesschau%20%3E5&everywhere=true&future=false
    # & und ! #: https://mediathekviewweb.de/#query=%26%20und%20!%20%23

    def _real_extract(self, url):
        query_hash = self._match_id(url)

        url_stub = '?query=' + query_hash
        query = compat_parse_qs(compat_urlparse.urlparse(url_stub).query)
        search = query['query'][0]
        query.pop('query')

        if len(query) > 0:
            # Detect global flags, MVW is very strict about accepted values.
            extractor = MediathekViewWebSearchIE(self._downloader)
            if query.get('everywhere', []) == ['true']:
                extractor._everywhere = True
            if query.get('future', []) == ['false']:
                extractor._future = False
            return extractor._real_extract('mvwsearchall:' + search)

        return self.url_result('mvwsearchall:' + search, ie=MediathekViewWebSearchIE.ie_key())
