from __future__ import unicode_literals

from .common import InfoExtractor


class MwaveIE(InfoExtractor):
    IE_NAME = 'mwave'
    _VALID_URL = r'https?://mwave\.interest\.me/mnettv/videodetail\.m\?searchVideoDetailVO\.clip_id=(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://mwave.interest.me/mnettv/videodetail.m?searchVideoDetailVO.clip_id=168859',
        'info_dict': {
            'id': '168859',
            'ext': 'flv',
            'title': '[M COUNTDOWN] SISTAR - SHAKE IT',
            'creator': 'M COUNTDOWN',
        }
    }, {
        'url': 'http://mwave.interest.me/mnettv/videodetail.m?searchVideoDetailVO.clip_id=168860',
        'info_dict': {
            'id': '168860',
            'ext': 'flv',
            'title': '[Full Ver.] M GIGS Ep. 59 - IDIOTAPE Live Part 1',
            'creator': 'M-GIGS',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        stream_info = self._download_json(
            'http://mwave.interest.me/onair/vod_info.m?vodtype=CL&sectorid=&endinfo=Y&id=%s' % video_id,
            'Download stream info')

        formats = []
        for info in stream_info['cdn']:
            f4m_stream = self._download_json(info['url'], video_id, 'Download f4m stream')
            formats.extend(
                self._extract_f4m_formats(f4m_stream['fileurl'] + '&g=PCROWKHLYUDY&hdcore=3.0.3', video_id))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': stream_info['title'],
            'creator': stream_info.get('program_title'),
            'formats': formats,
        }
