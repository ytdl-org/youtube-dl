# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


from ..compat import (
    compat_urllib_parse_unquote_to_bytes,
)

from ..utils import (
    clean_html,
    ExtractorError,
    int_or_none,
    OnDemandPagedList,
    strip_or_none,
    unified_timestamp,
    url_or_none,
)


class SimplecastIE(InfoExtractor):
    IE_NAME = 'simplecast'
    _VALID_URL = r'https://api\.simplecast\.com/episodes/(?P<id>[^?/]+)'
    _TEST = {
        'url': 'https://api.simplecast.com/episodes/b6dc49a2-9404-4853-9aa9-9cfc097be876',
        'md5': '8c93be7be54251bf29ee97464eabe61c',
        'info_dict': {
            'display_id': 'errant-signal-chris-franklin-new-wave-video-essays',
            'id': 'b6dc49a2-9404-4853-9aa9-9cfc097be876',
            'ext': 'mp3',
            'title': 'Errant Signal - Chris Franklin & New Wave Video Essays',
            'thumbnail': r're:^https?://.*\.jpg$',
            'episode_number': 1,
            'episode_id': 'b6dc49a2-9404-4853-9aa9-9cfc097be876',
            'description': 'md5:72c89d3ae63a77a6c55ce8becf170f2e',
            'season_number': 1,
            'season_id': 'e23df0da-bae4-4531-8bbf-71364a88dc13',
            'series': 'The RE:BIND.io Podcast',
            'duration': 5343,
            'timestamp': 1580979475,
            'upload_date': '20200206',
            'webpage_url': r're:^https://.+\.simplecast.com/episodes/[^?/]+',
            'channel_url': r're:^https://.+\.simplecast.com$',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        meta = self._download_json(
            url, display_id,
            expected_status=404)

        if meta.get('status') == 404:
            raise ExtractorError(
                'The requested episode could not be found', expected=True)

        summary = strip_or_none(meta.get('description'))
        long_description = strip_or_none(
            clean_html(meta.get('long_description')))
        description = summary or long_description
        if summary and long_description:
            description = summary + '\n\n' + long_description

        season_href = url_or_none(meta.get('season', {}).get('href'))
        season_id = None
        if season_href:
            id_regex = re.match(
                r'https?://api.simplecast.com/seasons/(?P<id>[^?]+)',
                season_href)
            if id_regex:
                season_id = id_regex.group('id')

        webpage_url = url_or_none(meta.get('episode_url'))
        channel_url = None
        if webpage_url:
            channel_regex = re.match(
                r'(?P<wp>https?://.+\.simplecast\.com)',
                webpage_url)
            if channel_regex:
                channel_url = channel_regex.group('wp')

        return {
            'id': meta['id'],
            'display_id': meta.get('slug') or display_id,
            'title': meta['title'],
            'url': meta['audio_file_url'],
            'webpage_url': webpage_url,
            'channel_url': channel_url,
            'series': strip_or_none(meta.get('podcast', {}).get('title')),
            'season_number': int_or_none(meta.get('season', {}).get('number')),
            'season_id': season_id,
            'thumbnail': url_or_none(
                meta.get('image_url')
                or meta.get('podcast', {}).get('image_url')),
            'episode_id': meta.get('id'),
            'episode_number': int_or_none(meta.get('number')),
            'description': description,
            'timestamp': unified_timestamp(meta.get('published_at')),
            'duration': int_or_none(meta.get('duration')),
        }


class SimplecastEmbedIE(InfoExtractor):
    IE_NAME = 'simplecast:embed'
    _VALID_URL = r'https?://(?:embed|player)\.simplecast\.com/(?P<id>[^?]+)'
    _TESTS = [{
        'url': 'https://player.simplecast.com/b6dc49a2-9404-4853-9aa9-9cfc097be876',
        'md5': '8c93be7be54251bf29ee97464eabe61c',
        'info_dict': {
            'display_id': 'errant-signal-chris-franklin-new-wave-video-essays',
            'id': 'b6dc49a2-9404-4853-9aa9-9cfc097be876',
            'ext': 'mp3',
            'title': 'Errant Signal - Chris Franklin & New Wave Video Essays',
            'thumbnail': r're:^https?://.*\.jpg$',
            'episode_number': 1,
            'episode_id': 'b6dc49a2-9404-4853-9aa9-9cfc097be876',
            'description': 'md5:72c89d3ae63a77a6c55ce8becf170f2e',
            'season_number': 1,
            'season_id': 'e23df0da-bae4-4531-8bbf-71364a88dc13',
            'series': 'The RE:BIND.io Podcast',
            'duration': 5343,
            'timestamp': 1580979475,
            'upload_date': '20200206',
            'webpage_url': r're:^https://.+\.simplecast.com/episodes/[^?/]+',
            'channel_url': r're:^https://.+\.simplecast.com$',
        }
    }, {
        'url': 'https://embed.simplecast.com/0bab9525',
        'md5': '580b1cc614c8ba33d929aaeeb38c274b',
        'info_dict': {
            'id': '565b3059-5227-4439-86e7-3eb1d43bf209',
            'ext': 'mp3',
            'title': 'Talib Kweli',
            'thumbnail': r're:^https?://.*\.jpg$',
            'episode_number': 22,
            'episode_id': '565b3059-5227-4439-86e7-3eb1d43bf209',
            'description': 'md5:d9d22ebcc84b6938efd3896fd18cc047',
            'season_number': 1,
            'season_id': 'b9df4072-7bd7-4704-b314-8dba46369de4',
            'series': 'Armchair Expert with Dax Shepard',
            'duration': 10435,
            'timestamp': 1528707600,
            'upload_date': '20180611',
            'webpage_url': r're:^https://.+\.simplecast.com/episodes/[^?/]+',
            'channel_url': r're:^https://.+\.simplecast.com$',
        }
    }]

    def _real_extract(self, url):
        if re.match(r'https?://embed\.', url):
            disp_id = self._match_id(url)
            return self.url_result(
                self._request_webpage(
                    'https://embed.simplecast.com/{0}'.format(disp_id), disp_id,
                    'Resolving ID', 'Unable to resolve ID').geturl(),
                'SimplecastEmbed')
        episode_id = self._match_id(url)
        return self.url_result(
            'https://api.simplecast.com/episodes/{0}'.format(episode_id),
            'Simplecast', episode_id)


class SimplecastEpisodeIE(InfoExtractor):
    IE_NAME = 'simplecast:episode'
    _VALID_URL = r'https?://(?!(?:cdn|embed|player|api|www)\.).*\.simplecast\.com/episodes/(?P<id>[^?]+)'
    _TEST = {
        'url': 'https://the-re-bind-io-podcast.simplecast.com/episodes/errant-signal-chris-franklin-new-wave-video-essays',
        'md5': '8c93be7be54251bf29ee97464eabe61c',
        'info_dict': {
            'display_id': 'errant-signal-chris-franklin-new-wave-video-essays',
            'id': 'b6dc49a2-9404-4853-9aa9-9cfc097be876',
            'ext': 'mp3',
            'title': 'Errant Signal - Chris Franklin & New Wave Video Essays',
            'thumbnail': r're:^https?://.*\.jpg$',
            'episode_number': 1,
            'episode_id': 'b6dc49a2-9404-4853-9aa9-9cfc097be876',
            'description': 'md5:72c89d3ae63a77a6c55ce8becf170f2e',
            'season_number': 1,
            'season_id': 'e23df0da-bae4-4531-8bbf-71364a88dc13',
            'series': 'The RE:BIND.io Podcast',
            'duration': 5343,
            'timestamp': 1580979475,
            'upload_date': '20200206',
            'webpage_url': r're:^https://.+\.simplecast.com/episodes/[^?/]+',
            'channel_url': r're:^https://.+\.simplecast.com$',
        }
    }

    def _real_extract(self, url):
        url = url.rstrip('/')
        display_id = self._match_id(url)

        search_result = self._download_json(
            'https://api.simplecast.com/episodes/search', display_id,
            'Looking up episode info', 'Unable to look up episode info',
            data=compat_urllib_parse_unquote_to_bytes(
                '{{"url":"{0}"}}'.format(url)),
            headers={'Content-Type': 'application/json;charset=utf-8'},
            expected_status=404)

        if search_result.get('status') == 404:
            raise ExtractorError(
                'The requested episode could not be found', expected=True)

        episode_id = search_result['id']
        self.to_screen('{0}: Real ID is {1}'.format(display_id, episode_id))

        return self.url_result(
            'https://api.simplecast.com/episodes/{0}'.format(episode_id),
            'Simplecast', episode_id, search_result.get('title'))


class SimplecastPodcastIE(InfoExtractor):
    IE_NAME = 'simplecast:podcast'
    _VALID_URL = r'https?://(?!(?:cdn|embed|player|api|www))(?P<id>.+)\.simplecast\.com(?:/episodes/?)?'
    _PAGE_SIZE = 25
    _PAGE_TOTAL = '?'
    _TEST = {
        'url': 'https://the-re-bind-io-podcast.simplecast.com',
        'playlist_mincount': 3,
        'info_dict': {
            'id': '07d28d26-7522-42eb-8c53-2bdcfc81c43c',
            'description': 'md5:5b83928525a22effaee9dd5c2addc378',
            'title': 'The RE:BIND.io Podcast',
        }
    }

    @classmethod
    def suitable(cls, url):
        return (False
                if SimplecastEpisodeIE.suitable(url)
                else super(SimplecastPodcastIE, cls).suitable(url))

    def _real_extract(self, url):
        podcast_id = self._match_id(url)

        search_result = self._download_json(
            'https://api.simplecast.com/sites/search', podcast_id,
            'Looking up podcast info', 'Unable to look up podcast info',
            data=compat_urllib_parse_unquote_to_bytes(
                '{{"url":"{0}"}}'.format(url)),
            headers={'Content-Type': 'application/json;charset=utf-8'},
            expected_status=404)

        if search_result.get('status') == 404:
            raise ExtractorError(
                'The requested podcast could not be found', expected=True)

        series_id = search_result['podcast']['id']

        pod_meta = self._download_json(
            'https://api.simplecast.com/podcasts/{0}'.format(series_id),
            podcast_id, 'Downloading podcast metadata',
            'Unable to download podcast metadata',
            fatal=False)

        series_description = series_thumbnail = license = None
        if type(pod_meta) is dict:
            series_description = strip_or_none(pod_meta.get('description'))
            license = strip_or_none(pod_meta.get('copyright'))
            series_thumbnail = pod_meta.get('image_url')

        season_list = self._download_json(
            'https://api.simplecast.com/podcasts/{0}/seasons'.format(series_id),
            podcast_id, 'Downloading season list',
            'Unable to download season list')

        if len(season_list['collection']) > 1:
            # Haven't seen anything with multiple seasons,
            # not sure how to handle that
            raise ExtractorError(
                'Support for podcasts with more than one season'
                ' has not been implemented')
        for season in season_list['collection']:
            season_number = int_or_none(season.get('number'))
            season_id = re.match(
                r'https?://api.simplecast.com/seasons/(?P<id>[^?]+)',
                season['href']).group('id')

        series = strip_or_none(search_result.get('podcast', {}).get('title'))
        subdomain = search_result.get('subdomain')
        channel_url = None
        if subdomain:
            channel_url = 'https://{0}.simplecast.com'.format(subdomain)

        def get_page(page_num):
            episode_list = self._download_json(
                'https://api.simplecast.com/seasons/{0}/episodes?limit={1}&offset={2}'.format(
                    season_id, self._PAGE_SIZE, self._PAGE_SIZE * page_num),
                podcast_id,
                'Downloading episode list page {0} of {1}'.format(
                    page_num + 1, self._PAGE_TOTAL),
                'Unable to download episode list page {0} of {1}'.format(
                    page_num + 1, self._PAGE_TOTAL))
            self._PAGE_TOTAL = (
                int_or_none(episode_list.get('pages', {}).get('total'))
                or '?')

            for episode in episode_list['collection']:
                yield {
                    '_type': 'url',
                    'ie_key': 'Simplecast',
                    'url': 'https://api.simplecast.com/episodes/{0}'.format(episode['id']),
                    'id': episode['id'],
                    'display_id': episode.get('slug'),
                    'title': episode.get('title'),
                    'webpage_url': url_or_none(search_result.get('episode_url')),
                    'channel_id': search_result.get('id'),
                    'channel_url': channel_url,
                    'series': series,
                    'season_id': season_id,
                    'season_number': season_number,
                    'thumbnail': url_or_none(episode.get('image_url') or series_thumbnail),
                    'episode_id': episode['id'],
                    'episode_number': int_or_none(episode.get('number')),
                    'description': strip_or_none(episode.get('description')),
                    'timestamp': unified_timestamp(episode.get('published_at')),
                    'license': license,
                }

        return self.playlist_result(
            OnDemandPagedList(get_page, self._PAGE_SIZE),
            series_id, series, series_description)
