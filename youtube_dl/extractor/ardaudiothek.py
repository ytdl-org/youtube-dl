# coding: utf-8
from __future__ import unicode_literals

import re

try:
    from urllib.parse import unquote as _unquote_compat
except ImportError:
    from urllib import unquote

    def _unquote_compat(str):
        return unquote(str.encode('utf-8')).decode('utf-8')

from .common import InfoExtractor
from ..utils import (
    compat_str,
    ExtractorError,
    int_or_none,
    parse_duration,
    str_or_none,
    try_get,
    unified_strdate,
    unified_timestamp,
)


class ARDAudiothekBaseIE(InfoExtractor):

    def _extract_episode_info(self, title):
        """Try to extract episode data from the title."""
        res = {}
        if not title:
            return res

        for pattern in [
            r'.*(?P<ep_info> \(S(?P<season_number>\d+)/E(?P<episode_number>\d+)\)).*',
            r'.*(?P<ep_info> \((?:Folge |Teil )?(?P<episode_number>\d+)(?:/\d+)?\)).*',
            r'.*(?P<ep_info>Folge (?P<episode_number>\d+)(?:\:| -|) )\"(?P<episode>.+)\".*',
            r'.*(?P<ep_info>Folge (?P<episode_number>\d+)(?:/\d+)?(?:\:| -|) ).*',
        ]:
            m = re.match(pattern, title)
            if m:
                groupdict = m.groupdict()
                for int_entry in ['season_number', 'episode_number']:
                    res[int_entry] = int_or_none(groupdict.get(int_entry))

                for str_entry in ['episode']:
                    res[str_entry] = str_or_none(groupdict.get(str_entry))

                # Build the episode title by removing numeric episode
                # information.
                if groupdict.get('ep_info') and not res['episode']:
                    res['episode'] = str_or_none(
                        title.replace(groupdict.get('ep_info'), ''))

                if res['episode']:
                    res['episode'] = res['episode'].strip()

                break

        # As a fallback use the whole title as the episode name
        if not res.get('episode'):
            res['episode'] = title.strip()

        return res

    def _extract_id_title_desc(self, json_data):
        res = {
            'id': try_get(json_data, lambda x: x['id'], compat_str),
            'display_id': try_get(json_data, lambda x: x['slug'], compat_str),
        }
        res['title'] = try_get(
            json_data, lambda x: x['title'], compat_str)
        res['description'] = try_get(
            json_data, lambda x: x['summary'], compat_str)
        return res

    def _extract_episode(self, ep_data):
        res = self._extract_id_title_desc(ep_data)

        res['url'] = try_get(ep_data, [
            lambda x: x['enclosure']['download_url'],
            lambda x: x['enclosure']['playback_url'],
            lambda x: x['guid'],
        ], compat_str)
        if not res['url']:
            raise ExtractorError(msg='Could not find a URL to download',
                                 expected=True)

        res['format_note'] = try_get(
            ep_data, lambda x: x['enclosure']['type'], compat_str)
        res['duration'] = parse_duration(
            try_get(ep_data, lambda x: x['duration'], compat_str))
        res['release_date'] = unified_strdate(
            try_get(ep_data, lambda x: x['publication_date'], compat_str))
        res['timestamp'] = unified_timestamp(
            try_get(ep_data, lambda x: x['publication_date'], compat_str))
        res['channel'] = try_get(ep_data, [
            lambda x: x['podcast']['station'],
            lambda x: x['podcast']['organization_name'],
        ], compat_str)

        # 'sharing_url' might be a redirecting URL. The generic extractor will
        # handle the redirection just fine, so that this extractor here will
        # be used.
        res['webpage_url'] = try_get(
            ep_data, lambda x: x['sharing_url'], compat_str)

        res['categories'] = [
            try_get(ep_data, lambda x: x['podcast']['category'], compat_str),
        ]

        res['is_live'] = False

        res['series'] = try_get(ep_data,
                                lambda x: x['podcast']['title'],
                                compat_str)

        def make_thumbnail(url, id, preference):
            # Note that the images don't necessarily have the advertised
            # aspect ratio! So don't set the height based on the aspect
            # ratio.
            # Also note that the server will not return an image of any given
            # width. Most multiples of 32 (or of 64 for higher numbers) seem to
            # work. When requesting a width of 1080, the server returns an
            # image with a width of 1024, for instance. Requesting 1400 gives
            # us 1344, and so on. So a width of 1920 works best for both 1x1
            # and 16x9 images.
            thumb_width = 1920
            return {
                'id': id,
                # Only set the width if we actually replace the {width}
                # placeholder in the URL.
                'width': thumb_width if '{width}' in url else None,
                'url': url.replace('{width}', str(thumb_width)),
                'preference': preference,
            }

        # We prefer 1x1 images and we prefer episode images. But still provide
        # all available images so that the user can choose. We use the
        # thumbnail's 'preference' entry to sort them (the higher the better).
        # The preferred thumbnail order is:
        #     (0) podcast-16x9 < (1) episode-16x9
        #   < (2) podcast-1x1 < (3) episode-1x1
        thumbnails = []
        for ar_index, aspect_ratio in enumerate(['16x9', '1x1']):
            image_key = 'image_%s' % aspect_ratio
            image_sources = [
                {'name': 'podcast',
                 'access': lambda x: x['podcast'][image_key]},
                {'name': 'episode',
                 'access': lambda x: x[image_key]},
            ]
            for src_index, src in enumerate(image_sources):
                thumb_url = try_get(ep_data, src['access'], compat_str)

                if thumb_url:
                    thumbnails.append(make_thumbnail(
                        thumb_url,
                        src['name'] + '-' + aspect_ratio,
                        ar_index * len(image_sources) + src_index))
        res['thumbnails'] = thumbnails

        res.update(self._extract_episode_info(res.get('title')))

        return res


class ARDAudiothekIE(ARDAudiothekBaseIE):
    _VALID_URL = r'https?://(?:www\.|beta\.)?ardaudiothek\.de/(?:[^/]+)/(?:[^/]+)/(?P<id>[0-9]+)(?:/.*)?'
    _TESTS = [{
        'url': 'https://www.ardaudiothek.de/hoerspiel-pool/virginia-woolf-zum-leuchtturm-1-3-die-tuer-aus-glas/53728640',
        'md5': 'dc12a86bb46faadbdba7a8c9b5a24246',
        'info_dict': {
            'id': '53728640',
            'ext': 'mp3',
            'title': 'Virginia Woolf: Zum Leuchtturm (1/3) - Die Tür aus Glas',
            'description': r're:^Am Anfang steht die Frage.*',
            'thumbnail': compat_str,
            'timestamp': 1478818860,
            'upload_date': '20161110',
        }
    }, {
        'url': 'https://www.ardaudiothek.de/eine-stunde-talk/soziologe-matthias-quent-nicht-neutral-gegenueber-rechtsradikalismus/65904422',
        'md5': '326065e45e8172124165c3b0addd4553',
        'info_dict': {
            'id': '65904422',
            'ext': 'mp3',
            'title': 'Soziologe Matthias Quent - Nicht neutral gegenüber Rechtsradikalismus',
            'description': r're:^Matthias Quent erforscht die Ziele.*',
            'thumbnail': compat_str,
            'timestamp': 1565809200,
            'upload_date': '20190814',
        }
    }]

    def _real_extract(self, url):
        episode_id = self._match_id(url)

        api_url = 'https://www.ardaudiothek.de/api/episodes/%s' % episode_id
        result_data = self._download_json(api_url, episode_id, fatal=False)
        ep_data = try_get(result_data, lambda x: x['result']['episode'], dict)

        if not ep_data:
            raise ExtractorError(msg="Could not find any episode data",
                                 expected=True)

        return self._extract_episode(ep_data)


class ARDAudiothekPlaylistIE(ARDAudiothekBaseIE):
    _VALID_URL = r'https?://(?:www\.|beta\.)?ardaudiothek\.de/(?!kategorie)(?:[^/]+)/(?P<id>[0-9]+)(?:/.*)?'
    _TESTS = [{
        'url': 'https://www.ardaudiothek.de/wirtschaft/62037362',
        'info_dict': {
            'id': '62037362',
            'title': 'Wirtschaft',
            'description': compat_str,
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://www.ardaudiothek.de/redezeit/7852070',
        'info_dict': {
            'id': '7852070',
            'title': 'Redezeit',
            'description': compat_str,
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://www.ardaudiothek.de/nur-fuer-starke-nerven-krimis-und-thriller/51581650/alle',
        'info_dict': {
            'id': '51581650',
            'title': r're:^Nur für starke Nerven',
            'description': compat_str,
        },
        'playlist_mincount': 5,
    }]

    def _get_page_str(self, page):
        # The API sometimes returns 404s for page=1. So only add that
        # parameter if we actually are past the first page
        return '&page=' + compat_str(page) if page > 1 else ''

    def _get_episode_from_array_entry(self, array_entry):
        # The array entry already is a an 'episode' dict.
        return array_entry

    def _extract_episodes(
            self, display_id, api_url_template, default_items_per_page):
        """
        Extract episodes by calling a web API end point.

        Sometimes the server does not respond properly when requesting a page.
        This also happens on the website. It sometimes hangs when trying to
        load more search results, for instance. Thus the number of entries
        reported by the API is often wrong and we do not solely rely on that
        number to stop reading episodes.

        This function handles paginated content in a robust way by skipping
        over faulty server responses. In this case it reduces the page size to
        get as many episodes as possible. It also removes duplicate entries
        from the result.

        Args:
            display_id: Only used for user feedback.
            api_url_template: This is the URL of the API to download JSON data
                from. It is a format string expected to have the following
                fields:
                    - {items_per_page}
                    - {page_str}
            default_items_per_page: The number of items to fetch per page.
                It is best to set this to the same value that is used by the
                website when accessing the API. This function automatically
                reduces the number of items per page when the server responds
                with errors or missing data.

        Returns:
            A list of extracted episode dicts to be used as playlist entries.

        Raises:
            ExtractorError: Might be raised when extracting episode data.

        """
        items_per_page = default_items_per_page
        page = 1

        entries = []

        # The number of entries as reported by the API
        n_entries = None

        # The API sometimes returns an empty page without any episodes. In this
        # case the next page often has episodes. This, however, throws off
        # the total number of entries and it no longer becomes a reliable
        # stopping condition when comparing it with the number of entries
        # reported by the API. So we deal with this by not stopping at the
        # first occurance of an empty page. We skip over a certain number of
        # empty pages before giving up.
        max_n_skipped_pages = default_items_per_page + 3
        n_skipped_pages = 0

        while True:
            # We need this to check if we actually added any entries
            n_entries_before_this_page = len(entries)

            # Fetch data
            api_url = api_url_template.format(
                page_str=self._get_page_str(page),
                items_per_page=items_per_page)
            result_data = self._download_json(api_url, display_id, fatal=False)
            episodes = try_get(result_data,
                               lambda x: x['result']['episodes'],
                               list)

            # Add entries
            for episode in episodes or []:
                entry = self._extract_episode(
                    self._get_episode_from_array_entry(episode))
                if entry not in entries:
                    entries.append(entry)

            # Fetch how many episodes the API says it has (it's enough to
            # read it once)
            n_entries = n_entries if n_entries is not None else try_get(
                result_data,
                lambda x: x['result']['meta']['episodes']['total'],
                int)

            # Check if we have read the reported number of episodes
            if n_entries is not None and len(entries) >= n_entries:
                break

            # Check if we actually added any entries
            if n_entries_before_this_page == len(entries):
                # This was an empty page so we have to skip it
                n_skipped_pages += 1
                if n_skipped_pages >= max_n_skipped_pages:
                    # Enough skipping, give up
                    break

                # Throttle by reading only half as many entries as before
                if items_per_page > 1:
                    new_items_per_page = int(max(1, items_per_page / 2))
                    page = int((page - 1) * items_per_page /
                               new_items_per_page)
                    items_per_page = new_items_per_page
            else:
                # This page had episodes, so we're no longer skipping
                n_skipped_pages = 0

                # Try to go back to full speed by going back to the default
                # items_per_page value if possible.
                if items_per_page * page % default_items_per_page == 0:
                    page = int(page * items_per_page /
                               default_items_per_page)
                    items_per_page = default_items_per_page

            page += 1

        # Tell the user if we received less entries than the API reported
        if n_entries is not None and len(entries) < n_entries:
            self.to_screen('Received {} of {} reported episodes'.format(
                len(entries), n_entries))

        return entries

    def _real_extract(self, url):
        podcast_id = self._match_id(url)

        api_url = 'https://www.ardaudiothek.de/api/podcasts/%s' % podcast_id
        result_data = self._download_json(api_url, podcast_id, fatal=False)
        pc_data = try_get(result_data, lambda x: x['result']['podcast'], dict)

        if not pc_data:
            raise ExtractorError(msg="Could not find any playlist data",
                                 expected=True)

        res = self._extract_id_title_desc(pc_data)
        res['_type'] = 'playlist'

        # items_per_page works from 1 up to 2147483647 (2^31 - 1).
        # The website calls the API with items_per_page set to 24. Setting it
        # to 500 or 1000 would download the data of all episodes in one or two
        # pages. Increasing this value might however trigger server errors in
        # the future. So to avoid any problems we will keep using the default
        # value and just download a few more pages.
        res['entries'] = self._extract_episodes(
            podcast_id,
            'https://www.ardaudiothek.de/api/podcasts/%s/episodes?items_per_page={items_per_page}{page_str}' % podcast_id,
            24)

        return res


class ARDAudiothekSearchIE(ARDAudiothekPlaylistIE):
    _VALID_URL = r'https?://(?:www\.|beta\.)?ardaudiothek\.de/suche\?(?:(?!q=).*&)?q=(?P<id>[^&]+)(?:&.*)?'
    _TESTS = [{
        'url': 'https://www.ardaudiothek.de/suche?q=Sommer',
        'info_dict': {
            'id': 'Sommer',
            'title': 'Sommer',
            'description': compat_str,
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://www.ardaudiothek.de/suche?q=Angela%20Merkel',
        'info_dict': {
            'id': 'Angela%20Merkel',
            'title': 'Angela Merkel',
            'description': compat_str,
        },
        'playlist_mincount': 5,
    }]

    def _get_page_str(self, page):
        # The search API always works with a page number
        return '&page=' + compat_str(page)

    def _get_episode_from_array_entry(self, array_entry):
        # The array entry is a dict with an 'episode' and a 'search_meta' entry
        return try_get(array_entry, lambda x: x['episode'], dict)

    def _real_extract(self, url):
        search_str = self._match_id(url)
        display_str = _unquote_compat(search_str)

        return {
            '_type': 'playlist',
            'id': search_str,
            'display_id': display_str,
            'title': display_str,
            'description': 'ARD Audiothek-Suche nach "' + display_str + '"',
            # Searching on the website calls the API with items_per_page set
            # to 8. Other values sometimes cause server errors.
            'entries': self._extract_episodes(
                display_str,
                'https://www.ardaudiothek.de/api/search/%s?focus=episodes{page_str}&items_per_page={items_per_page}' % search_str,
                8),
        }
