# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    urlencode_postdata,
    int_or_none,
    str_or_none,
)

from ..compat import compat_HTTPError


class AnimeLabBaseIE(InfoExtractor):
    _LOGIN_REQUIRED = True
    _LOGIN_URL = 'https://www.animelab.com/login'
    _NETRC_MACHINE = 'animelab'

    def _login(self):
        def is_logged_in(login_webpage):
            return '<title>AnimeLab - Login' not in login_webpage

        login_page = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login page')

        # Check if already logged in
        if is_logged_in(login_page):
            return

        (username, password) = self._get_login_info()
        if username is None and self._LOGIN_REQUIRED:
            self.raise_login_required('Login is required to access any AnimeLab content')

        login_form = {
            'email': username,
            'password': password,
        }

        try:
            response = self._download_webpage(
                self._LOGIN_URL, None, 'Logging in', 'Wrong login info',
                data=urlencode_postdata(login_form),
                headers={'Content-Type': 'application/x-www-form-urlencoded'})
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                page = e.cause.read().decode('utf-8')
                js_error = self._search_regex(
                    r'Utils\.notify\( *?[\'"]error[\'"] *?, *?[\'"](.*?)[\'"]',
                    page, 'Trying to get error message in js', default=None)
                if js_error:
                    raise ExtractorError('Unable to log in: %s' % js_error, expected=True)

                raise ExtractorError('Unable to log in (could not find error)', expected=True)
            else:
                raise

        # if login was successful
        if is_logged_in(response):
            return

        raise ExtractorError('Unable to login (cannot verify if logged in)')

    def _real_initialize(self):
        self._login()

    def _extract_video_collection_from_player(self, webpage):
        video_collection_str = self._search_regex(r'new +?VideoCollection *?\((.*?)\);', webpage, 'AnimeLab VideoCollection')
        return self._parse_json(video_collection_str, None)

    def _extract_position_from_player(self, webpage):
        position_str = self._search_regex(r'playlistPosition *?= *?(\d+)', webpage, 'Playlist Position')
        position = int_or_none(position_str)
        if position is None:
            raise ExtractorError('Could not get playlist position as integer. Extracted string was %s' % position_str)

        return position

    def _create_title(self, webpage, title_parts):
        if None not in title_parts:
            return '%s - %s %s - %s' % title_parts
        else:
            self.report_warning('Could not get all necessary data to contruct title manually, trying alternative sources...')
            return self._search_regex(r'AnimeLab - (.*) - Watch Online', webpage, 'Title from html')

    def _get_available_formats(self, webpage, raw_data):
        formats = []
        for video_data in raw_data['videoList']:
            current_video_list = {}
            current_video_list['language'] = video_data.get('language', {}).get('languageCode')

            is_hardsubbed = video_data.get('hardSubbed')

            for video_instance in video_data['videoInstances']:
                httpurl = video_instance.get('httpUrl')
                url = httpurl if httpurl else video_instance.get('rtmpUrl')
                if url is None:
                    # this video format is unavailable to the user (not premium etc.)
                    continue

                current_format = current_video_list.copy()

                current_format['url'] = url
                quality_data = video_instance.get('videoQuality')
                if quality_data:
                    quality = quality_data.get('name') or quality_data.get('description')
                else:
                    quality = None

                if quality:
                    height = int_or_none(self._search_regex(r'(\d+)p?$', quality, 'Video format height', default=None, fatal=False))
                else:
                    height = None

                if height is None:
                    self.report_warning('Could not get height of video')
                else:
                    current_format['height'] = height

                format_id_parts = []

                format_id_parts.append(str_or_none(video_instance.get('id')))

                if is_hardsubbed is not None:
                    if is_hardsubbed:
                        format_id_parts.append('yeshardsubbed')
                    else:
                        format_id_parts.append('nothardsubbed')

                format_id_parts.append(current_format['language'])

                format_id = '_'.join([x for x in format_id_parts if x is not None])
                current_format['format_id'] = format_id

                formats.append(current_format)

        # due to Python's sorting algorithm having the property of being 'stable', the following
        # means that videos are sorted by height, but in the case of the same height,
        # are sorted by language
        formats.sort(key=lambda k: str.lower(k.get('language') or ''))
        formats.sort(key=lambda k: k.get('height') or 0)

        return formats

    def _extract_video_from_collection(self, webpage, video_collection, position):
        raw_data = video_collection[position]['videoEntry']

        video_id = str_or_none(raw_data['id'])

        # create a title from many sources (while grabbing other info)
        # TODO use more fallback sources to get some of these
        series = raw_data.get('showTitle')
        video_type = raw_data.get('videoEntryType', {}).get('name')
        episode_number = raw_data.get('episodeNumber')
        episode_name = raw_data.get('name')

        title_parts = (series, video_type, episode_number, episode_name)
        title = self._create_title(webpage, title_parts)

        description = raw_data.get('synopsis') or self._og_search_description(webpage, default=None)

        formats = self._get_available_formats(webpage, raw_data)

        # TODO extract thumbnails and other things youtube-dl optionally wants

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'series': series,
            'episode': episode_name,
            'episode_number': int_or_none(episode_number),
            'formats': formats,
        }

    def _extract_video_from_player(self, webpage):
        video_collection = self._extract_video_collection_from_player(webpage)
        position = self._extract_position_from_player(webpage)
        return self._extract_video_from_collection(webpage, video_collection, position)


class AnimeLabIE(AnimeLabBaseIE):
    _VALID_URL = r'https?://(?:www\.)?animelab\.com/player/.+'

    # the following tests require authentication, but a free account will suffice
    # just set 'netrc' to true in test/local_parameters.json if you use a .netrc file
    # or you can set 'username' and 'password' there
    # the tests also select a specific format so that the same video is downloaded
    # regardless of whether the user is premium or not (needs testing on a premium account)
    _TESTS = [
        {
            'url': 'https://www.animelab.com/player/death-note-episode-1',
            'md5': 'cfb6eab52b32f687c1cad1adc945ca65',
            'info_dict': {
                'id': '46000',
                'ext': 'mp4',
                'title': 'Death Note - Episode 1 - Rebirth',
                'description': 'md5:82581ad67bf1f714409a434fd96ff85d',
                'series': 'Death Note',
                'episode': 'Rebirth',
                'episode_number': 1,
            },
            'params': {
                'format': '[format_id=59288_yeshardsubbed_ja-JP]',
            }
        },

        {
            'url': 'https://www.animelab.com/player/fullmetal-alchemist-brotherhood-episode-42',
            'md5': '05bde4b91a5d1ff46ef5b94df05b0f7f',
            'info_dict': {
                'id': '383',
                'ext': 'mp4',
                'title': 'Fullmetal Alchemist: Brotherhood - Episode 42 - Signs of a Counteroffensive',
                'description': 'md5:103eb61dd0a56d3dfc5dbf748e5e83f4',
                'series': 'Fullmetal Alchemist: Brotherhood',
                'episode': 'Signs of a Counteroffensive',
                'episode_number': 42,
            },
            'params': {
                'format': '[format_id=21711_yeshardsubbed_ja-JP]',
            }
        },
    ]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None, 'Downloading requested URL')
        return self._extract_video_from_player(webpage)

# TODO implement shows and myqueue (playlists)
