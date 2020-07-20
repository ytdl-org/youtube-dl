# coding: utf-8
from __future__ import unicode_literals
from collections import defaultdict
import subprocess
import json

from .common import InfoExtractor


class YleDLIE(InfoExtractor):
    _VALID_URL = r'https?://(?:areena|arenan).yle.fi/(?P<id>[0-9]-[0-9]+)'
    _GEO_COUNTRIES = ['FI']

    _TEST = {
        'url': 'https://areena.yle.fi/1-4256816',
        'md5': 'b9658c5960a8c2ca4ba8f1b0ff079df2',
        'info_dict': {
            'id': '1_iq074q8b',
            'ext': 'mxf',
            'title': 'Luottomies | Luottomies jouluspeciaali',
            'description':
                'Tommia harmittaa kun sukulaiset ovat tulossa pilaamaan '
                'mukavan perhejoulun. Muuttuuko mieli isosta yllätyksestä? '
                'Joulun erikoisjakson on ohjannut Jalmari Helander.',
            'upload_date': '20171207',
            'height': 1080,
            'width': 1920,
            'fps': 25,
            'duration': 1302,
            'timestamp': 1512633989,
            'extractor': 'Kaltura',
            'uploader_id': 'ovp@yle.fi',
            'webpage_url_basename': '1-4256816',
            'webpage_url': 'https://areena.yle.fi/1-4256816'
        }
    }

    def _real_extract(self, url):
        props = {}

        # Get essential data
        props['id'] = self._match_id(url)

        cp = subprocess.run(["yle-dl", "-q", "--showmetadata", url], capture_output=True, encoding='utf-8')
        cp.check_returncode()
        yledl = json.loads(cp.stdout)[0]

        props['title'] = yledl.get('title', '<none>')
        description = yledl.get('description', None)
        if description:
            props['description'] = description

        ysubs = yledl.get('subtitles', [])
        subtitles = defaultdict(list)
        for s in ysubs:
            subtitles[s['language']].append({'url': s['url'], 'ext': s['category']})
        props['subtitles'] = subtitles

        formats = []
        for f in yledl.get('flavors', []):
            formats.append({
                'url': f.get('url', ""),
                'tbr': f.get('bitrate', None),
                'width': f.get('width', None),
                'height': f.get('height', None),
                'protocol': 'm3u8',
            })
        props['formats'] = formats

        return props
