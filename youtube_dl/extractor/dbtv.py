# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    float_or_none,
    int_or_none,
    clean_html,
)


class DBTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dbtv\.no/(?:(?:lazyplayer|player)/)?(?P<id>[0-9]+)(?:#(?P<display_id>.+))?'
    _TESTS = [{
        'url': 'http://dbtv.no/3649835190001#Skulle_teste_ut_fornøyelsespark,_men_kollegaen_var_bare_opptatt_av_bikinikroppen',
        'md5': 'b89953ed25dacb6edb3ef6c6f430f8bc',
        'info_dict': {
            'id': '33100',
            'display_id': 'Skulle_teste_ut_fornøyelsespark,_men_kollegaen_var_bare_opptatt_av_bikinikroppen',
            'ext': 'mp4',
            'title': 'Skulle teste ut fornøyelsespark, men kollegaen var bare opptatt av bikinikroppen',
            'description': 'md5:1504a54606c4dde3e4e61fc97aa857e0',
            'thumbnail': 're:https?://.*\.jpg$',
            'timestamp': 1404039863.438,
            'upload_date': '20140629',
            'duration': 69.544,
            'view_count': int,
            'categories': list,
        }
    }, {
        'url': 'http://dbtv.no/3649835190001',
        'only_matching': True,
    }, {
        'url': 'http://www.dbtv.no/lazyplayer/4631135248001',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        data = self._download_json(
            'http://api.dbtv.no/discovery/%s' % video_id, display_id)

        video = data['playlist'][0]

        formats = [{
            'url': f['URL'],
            'vcodec': f.get('container'),
            'width': int_or_none(f.get('width')),
            'height': int_or_none(f.get('height')),
            'vbr': float_or_none(f.get('rate'), 1000),
            'filesize': int_or_none(f.get('size')),
        } for f in video['renditions'] if 'URL' in f]

        if not formats:
            for url_key, format_id in [('URL', 'mp4'), ('HLSURL', 'hls')]:
                if url_key in video:
                    formats.append({
                        'url': video[url_key],
                        'format_id': format_id,
                    })

        self._sort_formats(formats)

        return {
            'id': compat_str(video['id']),
            'display_id': display_id,
            'title': video['title'],
            'description': clean_html(video['desc']),
            'thumbnail': video.get('splash') or video.get('thumb'),
            'timestamp': float_or_none(video.get('publishedAt'), 1000),
            'duration': float_or_none(video.get('length'), 1000),
            'view_count': int_or_none(video.get('views')),
            'categories': video.get('tags'),
            'formats': formats,
        }
