# coding: utf-8
from __future__ import unicode_literals

import re

from .theplatform import ThePlatformIE
from ..compat import compat_urllib_parse
from ..utils import int_or_none


class CBSInteractiveIE(ThePlatformIE):
    _VALID_URL = r'https?://(?:www\.)?(?P<site>cnet|zdnet)\.com/(?:videos|video/share)/(?P<id>[^/?]+)'
    _TESTS = [{
        'url': 'http://www.cnet.com/videos/hands-on-with-microsofts-windows-8-1-update/',
        'md5': '041233212a0d06b179c87cbcca1577b8',
        'info_dict': {
            'id': '56f4ea68-bd21-4852-b08c-4de5b8354c60',
            'ext': 'mp4',
            'title': 'Hands-on with Microsoft Windows 8.1 Update',
            'description': 'The new update to the Windows 8 OS brings improved performance for mouse and keyboard users.',
            'uploader_id': '6085384d-619e-11e3-b231-14feb5ca9861',
            'uploader': 'Sarah Mitroff',
            'duration': 70,
            'timestamp': 1396479627,
            'upload_date': '20140402',
        },
        'params': {
            'format': 'mp4',
        },
    }, {
        'url': 'http://www.cnet.com/videos/whiny-pothole-tweets-at-local-government-when-hit-by-cars-tomorrow-daily-187/',
        'md5': 'f2b16d73e08d69591dd9e25564695c0c',
        'info_dict': {
            'id': '56527b93-d25d-44e3-b738-f989ce2e49ba',
            'ext': 'mp4',
            'title': 'Whiny potholes tweet at local government when hit by cars (Tomorrow Daily 187)',
            'description': 'Khail and Ashley wonder what other civic woes can be solved by self-tweeting objects, investigate a new kind of VR camera and watch an origami robot self-assemble, walk, climb, dig and dissolve. #TDPothole',
            'uploader_id': 'b163284d-6b73-44fc-b3e6-3da66c392d40',
            'uploader': 'Ashley Esqueda',
            'duration': 1482,
            'timestamp': 1433289889,
            'upload_date': '20150603',
        },
        'params': {
            'format': 'mp4',
        },
    }, {
        'url': 'http://www.zdnet.com/video/share/video-keeping-android-smartphones-and-tablets-secure/',
        'info_dict': {
            'id': 'bc1af9f0-a2b5-4e54-880d-0d95525781c0',
            'ext': 'mp4',
            'title': 'Video: Keeping Android smartphones and tablets secure',
            'description': 'Here\'s the best way to keep Android devices secure, and what you do when they\'ve come to the end of their lives.',
            'uploader_id': 'f2d97ea2-8175-11e2-9d12-0018fe8a00b0',
            'uploader': 'Adrian Kingsley-Hughes',
            'timestamp': 1449129925,
            'upload_date': '20151203',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }]
    TP_RELEASE_URL_TEMPLATE = 'http://link.theplatform.com/s/kYEXFC/%s?mbr=true'
    MPX_ACCOUNTS = {
        'cnet': 2288573011,
        'zdnet': 2387448114,
    }

    def _real_extract(self, url):
        site, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)

        data_json = self._html_search_regex(
            r"data-(?:cnet|zdnet)-video(?:-uvp(?:js)?)?-options='([^']+)'",
            webpage, 'data json')
        data = self._parse_json(data_json, display_id)
        vdata = data.get('video') or data['videos'][0]

        video_id = vdata['id']
        title = vdata['title']
        author = vdata.get('author')
        if author:
            uploader = '%s %s' % (author['firstName'], author['lastName'])
            uploader_id = author.get('id')
        else:
            uploader = None
            uploader_id = None

        media_guid_path = 'media/guid/%d/%s' % (self.MPX_ACCOUNTS[site], vdata['mpxRefId'])
        formats, subtitles = [], {}
        for (fkey, vid) in vdata.get('files', {}).items():
            if fkey == 'hls_phone' and 'hls_tablet' in vdata['files']:
                continue
            release_url = self.TP_RELEASE_URL_TEMPLATE % vid
            if fkey == 'hds':
                release_url += '&manifest=f4m'
            tp_formats, tp_subtitles = self._extract_theplatform_smil(release_url, video_id, 'Downloading %s SMIL data' % fkey)
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)

        if 'm3u8' in vdata:
            parsed_url = compat_urllib_parse.urlparse(url)
            m3u8_url = ('%s://%s%s'
                % (parsed_url.scheme, parsed_url.netloc, vdata['m3u8']))
            m3u8_formats = self._extract_m3u8_formats(m3u8_url, video_id)
            for format in m3u8_formats:
                format['url'] = format['url'].replace('https://', 'http://')
            formats.extend(m3u8_formats)

        if 'mp4' in vdata:
            formats.append({
                'url': vdata['mp4'],
                'format_id': 'mp4',
                'ext': 'mp4',
            })

        self._sort_formats(formats)

        info = self._extract_theplatform_metadata('kYEXFC/%s' % media_guid_path, video_id)
        info.update({
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'duration': int_or_none(vdata.get('duration')),
            'uploader': uploader,
            'uploader_id': uploader_id,
            'subtitles': subtitles,
            'formats': formats,
        })
        return info
