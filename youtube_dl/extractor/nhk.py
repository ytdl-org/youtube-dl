from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class NhkBaseIE(InfoExtractor):
    _API_URL_TEMPLATE = 'https://api.nhk.or.jp/nhkworld/%sod%slist/v7a/%s/%s/%s/all%s.json'

    def _get_clean_field(self, episode, key):
        return episode.get(key + '_clean') or episode.get(key)

    def _list_episodes(self, m_id, lang, is_video, is_episode):
        return self._download_json(
            self._API_URL_TEMPLATE % (
                'v' if is_video else 'r',
                'clip' if m_id[:4] == '9999' else 'esd',
                'episode' if is_episode else 'program',
                m_id, lang, '/all' if is_video else ''),
            m_id, query={'apikey': 'EJfK8jdS57GqlupFgAfAAwr573q01y6k'})['data']['episodes']

    def _parse_episode_json(self, episode, lang, is_video):
        title = episode.get('sub_title_clean') or episode['sub_title']

        episode_id = None
        if is_video:
            pgm_id = episode.get('pgm_id')
            pgm_no = episode.get('pgm_no')

            if not (pgm_id and pgm_no):
                missing_field = 'pgm_id' if not pgm_id else 'pgm_no'
                raise ExtractorError('Cannot download episode. Field %s is missing from episode JSON.' % missing_field)

            episode_id = pgm_id + pgm_no
        else:
            pgm_gr_id = episode.get('pgm_gr_id')
            first_onair_date = episode.get('first_onair_date')
            first_onair_no = episode.get('first_onair_no')

            if not (pgm_gr_id and first_onair_date and first_onair_no):
                missing_field = 'pgm_gr_id' if not pgm_gr_id else 'first_onair_date' if not first_onair_date else 'first_onair_no'
                raise ExtractorError('Cannot download episode. Field %s is missing from episode JSON.' % missing_field)

            episode_id = pgm_gr_id + '-' + first_onair_date + '-' + first_onair_no

        series = self._get_clean_field(episode, 'title')

        thumbnails = []
        for s, w, h in [('', 640, 360), ('_l', 1280, 720)]:
            img_path = episode.get('image' + s)
            if not img_path:
                continue
            thumbnails.append({
                'id': '%dp' % h,
                'height': h,
                'width': w,
                'url': 'https://www3.nhk.or.jp' + img_path,
            })

        info = {
            'id': episode_id + '-' + lang,
            'title': '%s - %s' % (series, title) if series and title else title,
            'description': self._get_clean_field(episode, 'description'),
            'thumbnails': thumbnails,
            'series': series,
            'episode': title,
        }

        if is_video:
            info.update({
                '_type': 'url_transparent',
                'ie_key': 'Piksel',
                'url': 'https://player.piksel.com/v/refid/nhkworld/prefid/' + episode['vod_id'],
            })
        else:
            audio = episode['audio']
            audio_path = audio['audio']
            info['formats'] = self._extract_m3u8_formats(
                'https://nhkworld-vh.akamaihd.net/i%s/master.m3u8' % audio_path,
                episode_id, 'm4a', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False)
            for f in info['formats']:
                f['language'] = lang

        return info


class NhkVodIE(NhkBaseIE):
    _VALID_URL = r'https?://www3\.nhk\.or\.jp/nhkworld/(?P<lang>[a-z]{2})/ondemand/(?P<type>video|audio)/(?P<id>\d{7}|[^/]+?-\d{8}-\d+)'
    # Content available only for a limited period of time. Visit
    # https://www3.nhk.or.jp/nhkworld/en/ondemand/ for working samples.
    _TESTS = [{
        # clip
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/video/9999011/',
        'md5': '256a1be14f48d960a7e61e2532d95ec3',
        'info_dict': {
            'id': 'a95j5iza',
            'ext': 'mp4',
            'title': "Dining with the Chef - Chef Saito's Family recipe: MENCHI-KATSU",
            'description': 'md5:5aee4a9f9d81c26281862382103b0ea5',
            'timestamp': 1565965194,
            'upload_date': '20190816',
        },
    }, {
        # audio clip
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/audio/r_inventions-20201104-1/',
        'info_dict': {
            'id': 'r_inventions-20201104-1-en',
            'ext': 'm4a',
            'title': "Japan's Top Inventions - Miniature Video Cameras",
            'description': 'md5:07ea722bdbbb4936fdd360b6a480c25b',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/video/2015173/',
        'only_matching': True,
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/audio/plugin-20190404-1/',
        'only_matching': True,
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/fr/ondemand/audio/plugin-20190404-1/',
        'only_matching': True,
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/audio/j_art-20150903-1/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        lang, m_type, episode_id = re.match(self._VALID_URL, url).groups()

        if episode_id.isdigit():
            episode_id = episode_id[:4] + '-' + episode_id[4:]

        episode = self._list_episodes(episode_id, lang, m_type == 'video', True)[0]

        return self._parse_episode_json(episode, lang, m_type == 'video')


class NhkVodProgramIE(NhkBaseIE):
    _VALID_URL = r'https?://www3\.nhk\.or\.jp/nhkworld/(?P<lang>[a-z]{2})/ondemand/(program/video)/(?P<id>\w+)'
    # Content available only for a limited period of time. Visit
    # https://www3.nhk.or.jp/nhkworld/en/ondemand/ for working samples.
    _TESTS = [{
        # video program
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/program/video/japanrailway',
        'info_dict': {
            'id': 'japanrailway',
            'title': 'Japan Railway Journal',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/program/video/10yearshayaomiyazaki/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        lang, m_type, program_id = re.match(self._VALID_URL, url).groups()

        episodes = self._list_episodes(program_id, lang, True, False)

        if episodes:
            return self.playlist_result(
                [self._parse_episode_json(episode, lang, True)
                    for episode in episodes],
                self._get_clean_field(episodes[0], 'pgm_gr_id'), self._get_clean_field(episodes[0], 'title'))
        else:
            raise ExtractorError('No episodes returned for program with ID: %s' % program_id, expected=True)
