from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urlparse,
    compat_str,
)
from ..utils import (
    parse_duration,
    js_to_json,
    parse_iso8601,
)


class ViideaIE(InfoExtractor):
    _VALID_URL = r'''(?x)http://(?:www\.)?(?:
            videolectures\.net|
            flexilearn\.viidea\.net|
            presentations\.ocwconsortium\.org|
            video\.travel-zoom\.si|
            video\.pomp-forum\.si|
            tv\.nil\.si|
            video\.hekovnik.com|
            video\.szko\.si|
            kpk\.viidea\.com|
            inside\.viidea\.net|
            video\.kiberpipa\.org|
            bvvideo\.si|
            kongres\.viidea\.net|
            edemokracija\.viidea\.com
        )(?:/lecture)?/(?P<id>[^/]+)(?:/video/(?P<part>\d+))?/*(?:[#?].*)?$'''

    _TESTS = [{
        'url': 'http://videolectures.net/promogram_igor_mekjavic_eng/',
        'info_dict': {
            'id': '20171_part1',
            'ext': 'mp4',
            'title': 'Automatics, robotics and biocybernetics',
            'description': 'md5:815fc1deb6b3a2bff99de2d5325be482',
            'upload_date': '20130627',
            'duration': 565,
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        # video with invalid direct format links (HTTP 403)
        'url': 'http://videolectures.net/russir2010_filippova_nlp/',
        'info_dict': {
            'id': '14891_part1',
            'ext': 'flv',
            'title': 'NLP at Google',
            'description': 'md5:fc7a6d9bf0302d7cc0e53f7ca23747b3',
            'duration': 5352,
            'thumbnail': 're:http://.*\.jpg',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        'url': 'http://videolectures.net/deeplearning2015_montreal/',
        'info_dict': {
            'id': '23181',
            'title': 'Deep Learning Summer School, Montreal 2015',
            'description': 'md5:0533a85e4bd918df52a01f0e1ebe87b7',
            'timestamp': 1438560000,
        },
        'playlist_count': 30,
    }, {
        # multi part lecture
        'url': 'http://videolectures.net/mlss09uk_bishop_ibi/',
        'info_dict': {
            'id': '9737',
            'title': 'Introduction To Bayesian Inference',
            'timestamp': 1251622800,
        },
        'playlist': [{
            'info_dict': {
                'id': '9737_part1',
                'ext': 'wmv',
                'title': 'Introduction To Bayesian Inference',
            },
        }, {
            'info_dict': {
                'id': '9737_part2',
                'ext': 'wmv',
                'title': 'Introduction To Bayesian Inference',
            },
        }],
        'playlist_count': 2,
    }]

    def _real_extract(self, url):
        lecture_slug, part = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, lecture_slug)

        cfg = self._parse_json(self._search_regex([r'cfg\s*:\s*({.+?}),[\da-zA-Z_]:\(?function', r'cfg\s*:\s*({[^}]+})'], webpage, 'cfg'), lecture_slug, js_to_json)

        lecture_id = str(cfg['obj_id'])

        base_url = self._proto_relative_url(cfg['livepipe'], 'http:')

        lecture_data = self._download_json('%s/site/api/lecture/%s?format=json' % (base_url, lecture_id), lecture_id)['lecture'][0]

        lecture_info = {
            'id': lecture_id,
            'display_id': lecture_slug,
            'title': lecture_data['title'],
            'timestamp': parse_iso8601(lecture_data.get('time')),
            'description': lecture_data.get('description_wiki'),
            'thumbnail': lecture_data.get('thumb'),
        }

        entries = []
        parts = cfg.get('videos')
        if parts:
            if len(parts) == 1:
                part = compat_str(parts[0])
            if part:
                smil_url = '%s/%s/video/%s/smil.xml' % (base_url, lecture_slug, part)
                smil = self._download_smil(smil_url, lecture_id)
                info = self._parse_smil(smil, smil_url, lecture_id)
                info['id'] = '%s_part%s' % (lecture_id, part)
                switch = smil.find('.//switch')
                if switch is not None:
                    info['duration'] = parse_duration(switch.attrib.get('dur'))
                return info
            else:
                for part in parts:
                    entries.append(self.url_result('%s/%s/video/%s' % (base_url, lecture_slug, part), 'Viidea'))
                lecture_info['_type'] = 'multi_video'
        if not parts or lecture_data.get('type') == 'evt':
            # Probably a playlist
            playlist_webpage = self._download_webpage('%s/site/ajax/drilldown/?id=%s' % (base_url, lecture_id), lecture_id)
            entries = [
                self.url_result(compat_urlparse.urljoin(url, video_url), 'Viidea')
                for _, video_url in re.findall(r'<a[^>]+href=(["\'])(.+?)\1[^>]+id=["\']lec=\d+', playlist_webpage)]
            lecture_info['_type'] = 'playlist'

        lecture_info['entries'] = entries
        return lecture_info
