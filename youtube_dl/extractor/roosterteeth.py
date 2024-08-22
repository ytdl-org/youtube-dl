# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    urlencode_postdata,
    parse_m3u8_attributes,
    try_get,
    url_or_none,
    urljoin,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/(?:episode|watch)/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '9156',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But... The Game Announcement',
            'description': 'md5:168a54b40e228e79f4ddb141e89fe4f5',
            'thumbnail': r're:^https?://.*\.png$',
            'series': 'Million Dollars, But...',
            'episode': 'Million Dollars, But... The Game Announcement',
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
    }, {
        'url': 'https://roosterteeth.com/watch/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'only_matching': True,
    }]
    _EPISODE_BASE_URL = 'https://svod-be.roosterteeth.com/api/v1/episodes/'

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        try:
            self._download_json(
                'https://auth.roosterteeth.com/oauth/token',
                None, 'Logging in', data=urlencode_postdata({
                    'client_id': '4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5',
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                }))
        except ExtractorError as e:
            msg = 'Unable to login'
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                resp = self._parse_json(e.cause.read().decode(), None, fatal=False)
                if resp:
                    error = resp.get('extra_info') or resp.get('error_description') or resp.get('error')
                    if error:
                        msg += ': ' + error
            self.report_warning(msg)

    def _real_initialize(self):
        if self._get_cookies(self._EPISODE_BASE_URL).get('rt_access_token'):
            return
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)
        api_episode_url = self._EPISODE_BASE_URL + display_id

        try:
            video_json = self._download_json(
                api_episode_url + '/videos', display_id)['data'][0]
            m3u8_url = url_or_none(try_get(
                video_json, [
                    lambda j: j['attributes']['url'],
                    lambda j: j['links']['master']],
                compat_str))
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                if self._parse_json(e.cause.read().decode(), display_id).get('access') is False:
                    self.raise_login_required(
                        '%s is only available for FIRST members' % display_id)
            raise

        if m3u8_url:
            formats = self._extract_m3u8_formats(
                m3u8_url, display_id, 'mp4', 'm3u8_native', m3u8_id='hls')
            self._sort_formats(formats)

            subtitles = self._extract_m3u8_subtitles(m3u8_url, display_id)
        else:
            formats = []
            subtitles = None

        episode = self._download_json(
            api_episode_url, display_id,
            'Downloading episode JSON metadata')['data'][0]
        attributes = episode['attributes']
        title = attributes.get('title') or attributes['display_title']
        video_id = compat_str(episode['id'])

        thumbnails = []
        for image in episode.get('included', {}).get('images', []):
            if image.get('type') == 'episode_image':
                img_attributes = image.get('attributes') or {}
                for k in ('thumb', 'small', 'medium', 'large'):
                    img_url = img_attributes.get(k)
                    if img_url:
                        thumbnails.append({
                            'id': k,
                            'url': img_url,
                        })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': attributes.get('description') or attributes.get('caption'),
            'thumbnails': thumbnails,
            'series': attributes.get('show_title'),
            'season_number': int_or_none(attributes.get('season_number')),
            'season_id': attributes.get('season_id'),
            'episode': title,
            'episode_number': int_or_none(attributes.get('number')),
            'episode_id': str_or_none(episode.get('uuid')),
            'formats': formats,
            'channel_id': attributes.get('channel_id'),
            'subtitles': subtitles,
            'duration': int_or_none(attributes.get('length')),
        }

    def _extract_m3u8_subtitles(self, m3u8_url, video_id):
        res = self._download_webpage_handle(
            m3u8_url, video_id,
            note='Downloading subtitle information',
            errnote='Failed to download subtitle information',
            fatal=False, data=None, headers={}, query={})
        if res is False:
            return None

        m3u8_doc, urlh = res
        m3u8_url = urlh.geturl()

        subtitles = {}
        for line in m3u8_doc.splitlines():
            if not line.startswith("#EXT-X-MEDIA:"):
                continue
            media = parse_m3u8_attributes(line)

            media_type, media_url_raw, media_lang = (
                media.get('TYPE'), media.get('URI'), media.get('LANGUAGE'),)
            if not (media_type in ('SUBTITLES',) and media_url_raw and media_lang):
                continue

            media_url = urljoin(m3u8_url, media_url_raw)
            if not media_url:
                continue

            res = self._download_webpage_handle(
                media_url, video_id,
                note='Downloading subtitle information ({})'.format(media_lang),
                errnote='Failed to download subtitle information ({})'.format(media_lang),
                fatal=False, data=None, headers={}, query={})
            if res is False:
                continue

            m3u8_subtitle_doc, _ = res
            subtitle_url = None
            for subtitle_line in m3u8_subtitle_doc.splitlines():
                if subtitle_line.startswith("#"):
                    continue
                subtitle_url = urljoin(media_url, subtitle_line)
                break

            if subtitle_url:
                subtitles[compat_str(media_lang)] = [{'url': subtitle_url, }, ]
        return subtitles if len(subtitles) > 0 else None
