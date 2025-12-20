# coding: utf-8

from __future__ import unicode_literals

import itertools

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
    compat_zip as zip,
)
from ..utils import (
    dict_get,
    int_or_none,
    parse_iso8601,
    str_or_none,
    try_get,
    unified_timestamp,
    urljoin,
)


class BeegIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beeg\.(?:com|porn(?:/video)?)/-?(?P<id>\d+)'
    _TESTS = [{
        # api/v6 v1
        'url': 'http://beeg.com/5416503',
        'md5': 'a1a1b1a8bc70a89e49ccfd113aed0820',
        'info_dict': {
            'id': '5416503',
            'ext': 'mp4',
            'title': 'Sultry Striptease',
            'description': 'md5:d22219c09da287c14bed3d6c37ce4bc2',
            'timestamp': 1391813355,
            'upload_date': '20140207',
            'duration': 383,
            'tags': list,
            'age_limit': 18,
        },
        'skip': 'no longer available',
    }, {
        # api/v6 v2
        'url': 'https://beeg.com/1941093077?t=911-1391',
        'only_matching': True,
    }, {
        # api/v6 v2 w/o t
        'url': 'https://beeg.com/1277207756',
        'only_matching': True,
    }, {
        'url': 'https://beeg.porn/video/5416503',
        'only_matching': True,
    }, {
        'url': 'https://beeg.porn/5416503',
        'only_matching': True,
    }, {
        'url': 'https://beeg.com/-01882333214',
        'md5': 'f8fd97a58a09bc6d2ac25b6bbc98c220',
        'info_dict': {
            'id': '1882333214',
            'ext': 'mp4',
            'title': 'Be mine',
            'description': 'Lil cam dork living in Canada with 4 kitties',
            'timestamp': 1628218803,
            'upload_date': '20210806',
            'duration': 559,
            'tags': list,
            'age_limit': 18,
            'thumbnail': r're:https?://thumbs\.beeg\.com/videos/1882333214/\d+\.jpe?g',
        },
        'params': {
            # ignore variable HLS file data
            'skip_download': True,
        },
    }]

    def _old_real_extract(self, url, video_id, webpage):
        beeg_version = self._search_regex(
            r'beeg_version\s*=\s*([\da-zA-Z_-]+)', webpage, 'beeg version',
            default='1546225636701')

        if len(video_id) >= 10:
            query = {
                'v': 2,
            }
            qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            t = qs.get('t', [''])[0].split('-')
            if len(t) > 1:
                query.update({
                    's': t[0],
                    'e': t[1],
                })
        else:
            query = {'v': 1}

        def reverse_enumerate(l):
            return zip(reversed(next(zip(*enumerate(l)), [])), l)

        for rcnt, api_path in reverse_enumerate(('', 'api.')):
            video = self._download_json(
                'https://%sbeeg.com/api/v6/%s/video/%s'
                % (api_path, beeg_version, video_id), video_id,
                fatal=(rcnt == 0), query=query)
            if video:
                break

        formats = []
        for format_id, video_url in video.items():
            if not video_url:
                continue
            height = self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)
            if not height:
                continue
            formats.append({
                'url': self._proto_relative_url(
                    video_url.replace('{DATA_MARKERS}', 'data=pc_XX__%s_0' % beeg_version), 'https:'),
                'format_id': format_id,
                'height': int(height),
            })
        self._sort_formats(formats)

        title = video['title']
        video_id = compat_str(video.get('id') or video_id)
        display_id = video.get('code')
        description = video.get('desc')
        series = video.get('ps_name')

        timestamp = unified_timestamp(video.get('date'))
        duration = int_or_none(video.get('duration'))

        tags = [tag.strip() for tag in video['tags'].split(',')] if video.get('tags') else None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'series': series,
            'timestamp': timestamp,
            'duration': duration,
            'tags': tags,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = []
        # leading 0s stripped from ID by site, though full ID also works
        video = self._download_json(
            'https://store.externulls.com/facts/file/%d' % int(video_id),
            video_id, fatal=False)
        if video:
            video_data = try_get(video, lambda x: x['file'], dict) or {}
            video_data.update(video_data.get('stuff', {}))
            video_data.update(try_get(video, lambda x: x['fc_facts'][0], dict))
            for format_id, key in itertools.chain(
                    try_get(video_data, lambda x: x['resources'].items()) or [],
                    try_get(video_data, lambda x: x['hls_resources'].items()) or []):
                if not format_id:
                    continue
                formats.append({
                    'url': urljoin('https://video.beeg.com', key),
                    'format_id': format_id,
                    'height': int_or_none(format_id.rsplit('_', 1)[-1]),
                })
            if formats:
                self._sort_formats(formats)
                tags = try_get(video, lambda v: [tag['tg_slug'] for tag in v['tags'] if tag.get('tg_slug')])
                result = {
                    'id': str_or_none(video.get('fc_file_id')) or video_id,
                    'title': video_data.get('sf_name') or 'Beeg video %s' % video_id,
                    'description': video_data.get('sf_story'),
                    'timestamp': parse_iso8601(video_data.get('fc_created')),
                    'duration': int_or_none(dict_get(video_data, ('fl_duration', 'sf_duration'))),
                    'tags': tags,
                    'formats': formats,
                    'age_limit': self._rta_search(webpage) or 18,
                    'height': int_or_none(video_data.get('fl_height')),
                    'width': int_or_none(video_data.get('fl_width')),
                }
                thumb_id = try_get(video_data, lambda x: x['fc_thumbs'][0], int)
                if thumb_id is not None:
                    set_id = video_data.get('resources', {}).get('set_id')
                    result['thumbnail'] = (
                        'https://thumbs.beeg.com/videos/%s/%d.jpg' % (result['id'], thumb_id)
                        if set_id is None else
                        'https://thumbs-015.externulls.com/sets/%s/thumbs/%s-%0.4d.jpg' % (set_id, set_id, thumb_id))
                return result

        return self._old_real_extract(url, video_id, webpage)
