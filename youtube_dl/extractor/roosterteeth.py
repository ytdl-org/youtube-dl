# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    str_or_none,
    unified_timestamp,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/episode/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://roosterteeth.com/login'
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '9156',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But... The Game Announcement',
            'description': 'md5:0cc3b21986d54ed815f5faeccd9a9ca5',
            'thumbnail': r're:^https?://.*\.png$',
            'series': 'Million Dollars, But...',
            'episode': 'S2:E10 - Million Dollars, But... The Game Announcement',
        },
    }, {
        'url': 'http://achievementhunter.roosterteeth.com/episode/off-topic-the-achievement-hunter-podcast-2016-i-didn-t-think-it-would-pass-31',
        'only_matching': True,
    }, {
        'url': 'http://funhaus.roosterteeth.com/episode/funhaus-shorts-2016-austin-sucks-funhaus-shorts',
        'only_matching': True,
    }, {
        'url': 'http://screwattack.roosterteeth.com/episode/death-battle-season-3-mewtwo-vs-shadow',
        'only_matching': True,
    }, {
        'url': 'http://theknow.roosterteeth.com/episode/the-know-game-news-season-1-boring-steam-sales-are-better',
        'only_matching': True,
    }, {
        # only available for FIRST members
        'url': 'http://roosterteeth.com/episode/rt-docs-the-world-s-greatest-head-massage-the-world-s-greatest-head-massage-an-asmr-journey-part-one',
        'only_matching': True,
    }]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note='Downloading login page',
            errnote='Unable to download login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'username': username,
            'password': password,
        })

        login_request = self._download_webpage(
            self._LOGIN_URL, None,
            note='Logging in',
            data=urlencode_postdata(login_form),
            headers={
                'Referer': self._LOGIN_URL,
            })

        if not any(re.search(p, login_request) for p in (
                r'href=["\']https?://(?:www\.)?roosterteeth\.com/logout"',
                r'>Sign Out<')):
            error = self._html_search_regex(
                r'(?s)<span[^>]+class=(["\']).*?\bmessage\b.+\1[^>]*>(?P<error>.+?)</span>',
                login_request, 'alert', default=None, group='error')
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)

        api_path = "https://svod-be.roosterteeth.com/api/v1/episodes/{}"
        video_path = api_path + "/videos"

        api_response = self._download_json(
            api_path.format(display_id),
            display_id
        )

        if api_response.get('data') is None:
            raise ExtractorError('Unable to get API response')

        if len(api_response.get('data', [])) == 0:
            raise ExtractorError('Unable to get API response')

        data = api_response.get('data')[0]

        attributes = data.get('attributes', {})
        episode = attributes.get('display_title')
        title = attributes.get('title')
        description = attributes.get('caption')
        series = attributes.get('show_title')
        thumbnail = self.get_thumbnail(data.get('included', {}).get('images'))

        video_response = self._download_json(
            video_path.format(display_id),
            display_id
        )

        if video_response.get('access') is not None:
            now = time.time()
            sponsor_golive = unified_timestamp(attributes.get('sponsor_golive_at'))
            member_golive = unified_timestamp(attributes.get('member_golive_at'))
            public_golive = unified_timestamp(attributes.get('public_golive_at'))

            if attributes.get('is_sponsors_only'):
                if now < sponsor_golive:
                    self.golive_error(display_id, 'FIRST members')
                else:
                    self.raise_login_required('{0} is only available for FIRST members'.format(display_id))
            else:
                if now < member_golive:
                    self.golive_error(display_id, 'site members')
                elif now < public_golive:
                    self.golive_error(display_id, 'the public')
                else:
                    raise ExtractorError('Video is not available')
        if len(video_response.get('data', [])) > 0:
            video_attributes = video_response.get('data')[0].get('attributes')
        else:
            raise ExtractorError('Unable to get API response')

        m3u8_url = video_attributes.get('url')
        if not m3u8_url:
            raise ExtractorError('Unable to extract m3u8 URL')

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        video_id = str_or_none(video_attributes.get('content_id'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'series': series,
            'episode': episode,
            'formats': formats,
        }

    def golive_error(self, video_id, member_level):
        raise ExtractorError('{0} is not yet live for {1}'.format(video_id, member_level))

    def get_thumbnail(self, images):
        if not images or len(images) == 0:
            return None

        images = images[0]
        return images.get('attributes', {}).get('thumb')
