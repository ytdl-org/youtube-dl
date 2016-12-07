# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_urlparse,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    update_url_query,
    xpath_element,
    xpath_text,
)


class AfreecaTVIE(InfoExtractor):
    IE_DESC = 'afreecatv.com'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:(?:live|afbbs|www)\.)?afreeca(?:tv)?\.com(?::\d+)?
                            (?:
                                /app/(?:index|read_ucc_bbs)\.cgi|
                                /player/[Pp]layer\.(?:swf|html)
                            )\?.*?\bnTitleNo=|
                            vod\.afreecatv\.com/PLAYER/STATION/
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [{
        'url': 'http://live.afreecatv.com:8079/app/index.cgi?szType=read_ucc_bbs&szBjId=dailyapril&nStationNo=16711924&nBbsNo=18605867&nTitleNo=36164052&szSkin=',
        'md5': 'f72c89fe7ecc14c1b5ce506c4996046e',
        'info_dict': {
            'id': '36164052',
            'ext': 'mp4',
            'title': '데일리 에이프릴 요정들의 시상식!',
            'thumbnail': 're:^https?://(?:video|st)img.afreecatv.com/.*$',
            'uploader': 'dailyapril',
            'uploader_id': 'dailyapril',
            'upload_date': '20160503',
        }
    }, {
        'url': 'http://afbbs.afreecatv.com:8080/app/read_ucc_bbs.cgi?nStationNo=16711924&nTitleNo=36153164&szBjId=dailyapril&nBbsNo=18605867',
        'info_dict': {
            'id': '36153164',
            'title': "BJ유트루와 함께하는 '팅커벨 메이크업!'",
            'thumbnail': 're:^https?://(?:video|st)img.afreecatv.com/.*$',
            'uploader': 'dailyapril',
            'uploader_id': 'dailyapril',
        },
        'playlist_count': 2,
        'playlist': [{
            'md5': 'd8b7c174568da61d774ef0203159bf97',
            'info_dict': {
                'id': '36153164_1',
                'ext': 'mp4',
                'title': "BJ유트루와 함께하는 '팅커벨 메이크업!'",
                'upload_date': '20160502',
            },
        }, {
            'md5': '58f2ce7f6044e34439ab2d50612ab02b',
            'info_dict': {
                'id': '36153164_2',
                'ext': 'mp4',
                'title': "BJ유트루와 함께하는 '팅커벨 메이크업!'",
                'upload_date': '20160502',
            },
        }],
    }, {
        'url': 'http://www.afreecatv.com/player/Player.swf?szType=szBjId=djleegoon&nStationNo=11273158&nBbsNo=13161095&nTitleNo=36327652',
        'only_matching': True,
    }, {
        'url': 'http://vod.afreecatv.com/PLAYER/STATION/15055030',
        'only_matching': True,
    }]

    @staticmethod
    def parse_video_key(key):
        video_key = {}
        m = re.match(r'^(?P<upload_date>\d{8})_\w+_(?P<part>\d+)$', key)
        if m:
            video_key['upload_date'] = m.group('upload_date')
            video_key['part'] = m.group('part')
        return video_key

    def _real_extract(self, url):
        video_id = self._match_id(url)
        parsed_url = compat_urllib_parse_urlparse(url)
        info_url = compat_urlparse.urlunparse(parsed_url._replace(
            netloc='afbbs.afreecatv.com:8080',
            path='/api/video/get_video_info.php'))

        video_xml = self._download_xml(
            update_url_query(info_url, {'nTitleNo': video_id}), video_id)

        if xpath_element(video_xml, './track/video/file') is None:
            raise ExtractorError('Specified AfreecaTV video does not exist',
                                 expected=True)

        title = xpath_text(video_xml, './track/title', 'title')
        uploader = xpath_text(video_xml, './track/nickname', 'uploader')
        uploader_id = xpath_text(video_xml, './track/bj_id', 'uploader id')
        duration = int_or_none(xpath_text(video_xml, './track/duration',
                                          'duration'))
        thumbnail = xpath_text(video_xml, './track/titleImage', 'thumbnail')

        entries = []
        for i, video_file in enumerate(video_xml.findall('./track/video/file')):
            video_key = self.parse_video_key(video_file.get('key', ''))
            if not video_key:
                continue
            entries.append({
                'id': '%s_%s' % (video_id, video_key.get('part', i + 1)),
                'title': title,
                'upload_date': video_key.get('upload_date'),
                'duration': int_or_none(video_file.get('duration')),
                'url': video_file.text,
            })

        info = {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'thumbnail': thumbnail,
        }

        if len(entries) > 1:
            info['_type'] = 'multi_video'
            info['entries'] = entries
        elif len(entries) == 1:
            info['url'] = entries[0]['url']
            info['upload_date'] = entries[0].get('upload_date')
        else:
            raise ExtractorError(
                'No files found for the specified AfreecaTV video, either'
                ' the URL is incorrect or the video has been made private.',
                expected=True)

        return info
