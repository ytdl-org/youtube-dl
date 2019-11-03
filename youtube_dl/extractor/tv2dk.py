# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import extract_attributes


class TV2DKIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            tvsyd|
                            tv2ostjylland|
                            tvmidtvest|
                            tv2fyn|
                            tv2east|
                            tv2lorry|
                            tv2nord
                        )\.dk/
                        (:[^/]+/)*
                        (?P<id>[^/?\#&]+)
                    '''
    _TESTS = [{
        'url': 'https://www.tvsyd.dk/nyheder/28-10-2019/1930/1930-28-okt-2019?autoplay=1#player',
        'info_dict': {
            'id': '0_52jmwa0p',
            'ext': 'mp4',
            'title': '19:30 - 28. okt. 2019',
            'timestamp': 1572290248,
            'upload_date': '20191028',
            'uploader_id': 'tvsyd',
            'duration': 1347,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Kaltura'],
    }, {
        'url': 'https://www.tv2ostjylland.dk/artikel/minister-gaar-ind-i-sag-om-diabetes-teknologi',
        'only_matching': True,
    }, {
        'url': 'https://www.tv2ostjylland.dk/nyheder/28-10-2019/22/2200-nyhederne-mandag-d-28-oktober-2019?autoplay=1#player',
        'only_matching': True,
    }, {
        'url': 'https://www.tvmidtvest.dk/nyheder/27-10-2019/1930/1930-27-okt-2019',
        'only_matching': True,
    }, {
        'url': 'https://www.tv2fyn.dk/artikel/fyn-kan-faa-landets-foerste-fabrik-til-groent-jetbraendstof',
        'only_matching': True,
    }, {
        'url': 'https://www.tv2east.dk/artikel/gods-faar-indleveret-tonsvis-af-aebler-100-kilo-aebler-gaar-til-en-aeblebrandy',
        'only_matching': True,
    }, {
        'url': 'https://www.tv2lorry.dk/koebenhavn/rasmus-paludan-evakueret-til-egen-demonstration#player',
        'only_matching': True,
    }, {
        'url': 'https://www.tv2nord.dk/artikel/dybt-uacceptabelt',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        entries = []
        for video_el in re.findall(r'(?s)<[^>]+\bdata-entryid\s*=[^>]*>', webpage):
            video = extract_attributes(video_el)
            kaltura_id = video.get('data-entryid')
            if not kaltura_id:
                continue
            partner_id = video.get('data-partnerid')
            if not partner_id:
                continue
            entries.append(self.url_result(
                'kaltura:%s:%s' % (partner_id, kaltura_id), 'Kaltura',
                video_id=kaltura_id))
        return self.playlist_result(entries)
