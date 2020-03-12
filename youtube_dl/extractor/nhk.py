from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NhkVodIE(InfoExtractor):
    _VALID_URL = r'https?://www3\.nhk\.or\.jp/nhkworld/(?P<lang>[a-z]{2})/ondemand/(?P<type>video|audio)/(?P<id>\d{7}|[a-z]+-\d{8}-\d+)'
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
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/video/2015173/',
        'only_matching': True,
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/en/ondemand/audio/plugin-20190404-1/',
        'only_matching': True,
    }, {
        'url': 'https://www3.nhk.or.jp/nhkworld/fr/ondemand/audio/plugin-20190404-1/',
        'only_matching': True,
    }]
    _API_URL_TEMPLATE = 'https://api.nhk.or.jp/nhkworld/%sod%slist/v7a/episode/%s/%s/all%s.json'

    def _real_extract(self, url):
        lang, m_type, episode_id = re.match(self._VALID_URL, url).groups()
        if episode_id.isdigit():
            episode_id = episode_id[:4] + '-' + episode_id[4:]

        is_video = m_type == 'video'
        episode = self._download_json(
            self._API_URL_TEMPLATE % (
                'v' if is_video else 'r',
                'clip' if episode_id[:4] == '9999' else 'esd',
                episode_id, lang, '/all' if is_video else ''),
            episode_id, query={'apikey': 'EJfK8jdS57GqlupFgAfAAwr573q01y6k'})['data']['episodes'][0]
        title = episode.get('sub_title_clean') or episode['sub_title']

        def get_clean_field(key):
            return episode.get(key + '_clean') or episode.get(key)

        series = get_clean_field('title')

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
            'description': get_clean_field('description'),
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
                'https://nhks-vh.akamaihd.net/i%s/master.m3u8' % audio_path,
                episode_id, 'm4a', m3u8_id='hls', fatal=False)
            for proto in ('rtmpt', 'rtmp'):
                info['formats'].append({
                    'ext': 'flv',
                    'format_id': proto,
                    'url': '%s://flv.nhk.or.jp/ondemand/mp4:flv%s' % (proto, audio_path),
                    'vcodec': 'none',
                })
            for f in info['formats']:
                f['language'] = lang
        return info
