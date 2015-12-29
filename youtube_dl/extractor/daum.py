# encoding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import (
    int_or_none,
    str_to_int,
    xpath_text,
)


class DaumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tvpot\.daum\.net/v/(?P<id>[^?#&]+)'
    IE_NAME = 'daum.net'

    _TESTS = [{
        'url': 'http://tvpot.daum.net/v/vab4dyeDBysyBssyukBUjBz',
        'info_dict': {
            'id': 'vab4dyeDBysyBssyukBUjBz',
            'ext': 'mp4',
            'title': '마크 헌트 vs 안토니오 실바',
            'description': 'Mark Hunt vs Antonio Silva',
            'upload_date': '20131217',
            'duration': 2117,
            'view_count': int,
            'comment_count': int,
        },
    }, {
        'url': 'http://tvpot.daum.net/v/07dXWRka62Y%24',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        query = compat_urllib_parse.urlencode({'vid': video_id})
        info = self._download_xml(
            'http://tvpot.daum.net/clip/ClipInfoXml.do?' + query, video_id,
            'Downloading video info')
        movie_data = self._download_json(
            'http://videofarm.daum.net/controller/api/closed/v1_2/IntegratedMovieData.json?' + query,
            video_id, 'Downloading video formats info')

        formats = []
        for format_el in movie_data['output_list']['output_list']:
            profile = format_el['profile']
            format_query = compat_urllib_parse.urlencode({
                'vid': video_id,
                'profile': profile,
            })
            url_doc = self._download_xml(
                'http://videofarm.daum.net/controller/api/open/v1_2/MovieLocation.apixml?' + format_query,
                video_id, note='Downloading video data for %s format' % profile)
            format_url = url_doc.find('result/url').text
            formats.append({
                'url': format_url,
                'format_id': profile,
                'width': int_or_none(format_el.get('width')),
                'height': int_or_none(format_el.get('height')),
                'filesize': int_or_none(format_el.get('filesize')),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info.find('TITLE').text,
            'formats': formats,
            'thumbnail': xpath_text(info, 'THUMB_URL'),
            'description': xpath_text(info, 'CONTENTS'),
            'duration': int_or_none(xpath_text(info, 'DURATION')),
            'upload_date': info.find('REGDTTM').text[:8],
            'view_count': str_to_int(xpath_text(info, 'PLAY_CNT')),
            'comment_count': str_to_int(xpath_text(info, 'COMMENT_CNT')),
        }


class DaumClipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tvpot\.daum\.net/(?:clip/ClipView.do|mypot/View.do)\?.*?clipid=(?P<id>\d+)'
    IE_NAME = 'daum.net:clip'

    _TESTS = [{
        'url': 'http://tvpot.daum.net/clip/ClipView.do?clipid=52554690',
        'info_dict': {
            'id': '52554690',
            'ext': 'mp4',
            'title': 'DOTA 2GETHER 시즌2 6회 - 2부',
            'description': 'DOTA 2GETHER 시즌2 6회 - 2부',
            'upload_date': '20130831',
            'duration': 3868,
            'view_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        clip_info = self._download_json(
            'http://tvpot.daum.net/mypot/json/GetClipInfo.do?clipid=%s' % video_id,
            video_id, 'Downloading clip info')['clip_bean']

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': 'http://tvpot.daum.net/v/%s' % clip_info['vid'],
            'title': clip_info['title'],
            'thumbnail': clip_info.get('thumb_url'),
            'description': clip_info.get('contents'),
            'duration': int_or_none(clip_info.get('duration')),
            'upload_date': clip_info.get('up_date')[:8],
            'view_count': int_or_none(clip_info.get('play_count')),
            'ie_key': 'Daum',
        }
