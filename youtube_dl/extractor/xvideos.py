from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_str
)
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_duration,
    get_element_by_class,
    js_to_json,
    try_get
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:www\.)?xvideos\.com/video|
                            flashservice\.xvideos\.com/embedframe/|
                            static-hw\.xvideos\.com/swf/xv-player\.swf\?.*?\bid_video=
                        )
                        (?P<id>[0-9]+)
                    '''
    _TESTS = [{
        'url': 'http://www.xvideos.com/video4588838/biker_takes_his_girl',
        'md5': '14cea69fcb84db54293b1e971466c2e1',
        'info_dict': {
            'id': '4588838',
            'ext': 'mp4',
            'title': 'Biker Takes his Girl',
            'duration': 108,
            'age_limit': 18,
            'uploader': 'Kandys Kisses',
            'uploader_id': 'kandyskisses',
            'categories': list,
            'tags': list
        },
    }, {
        'url': 'https://www.xvideos.com/video43548989/petite_brooke_haze_is_so_cute',
        'md5': 'b629ee68705da901dbd60c3b3a7c16bc',
        'info_dict': {
            'id': '43548989',
            'ext': 'mp4',
            'title': 'Petite Brooke Haze is so cute',
            'duration': 521,
            'uploader': 'Amkempire',
            'uploader_id': 'amkempire',
            'categories': list,
            'tags': list,
            'creator': 'AMKEmpire',
            'age_limit': 18,
        },
    }, {
        # anonymous / unavailable uploader
        'url': 'https://www.xvideos.com/video91/3_young_school_girls',
        'md5': '86f6a54c5f3ad45a01c5daac512c59a6',
        'info_dict': {
            'id': '91',
            'ext': 'mp4',
            'title': '3 young school girls',
            'duration': 35,
            'uploader': None,
            'uploader_id': None,
            'categories': list,
            'tags': list,
            'age_limit': 18,
        },
    }, {
        'url': 'https://flashservice.xvideos.com/embedframe/4588838',
        'only_matching': True,
    }, {
        'url': 'http://static-hw.xvideos.com/swf/xv-player.swf?id_video=4588838',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.xvideos.com/video%s/' % video_id, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        title = self._html_search_regex(
            (r'<title>(?P<title>.+?)\s+-\s+XVID',
             r'setVideoTitle\s*\(\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', default=None,
            group='title') or self._og_search_title(webpage)

        thumbnails = []
        for preference, thumbnail in enumerate(('', '169')):
            thumbnail_url = self._search_regex(
                r'setThumbUrl%s\(\s*(["\'])(?P<thumbnail>(?:(?!\1).)+)\1' % thumbnail,
                webpage, 'thumbnail', default=None, group='thumbnail')
            if thumbnail_url:
                thumbnails.append({
                    'url': thumbnail_url,
                    'preference': preference,
                })

        duration = int_or_none(self._og_search_property(
            'duration', webpage, default=None)) or parse_duration(
            self._search_regex(
                r'<span[^>]+class=["\']duration["\'][^>]*>.*?(\d[^<]+)',
                webpage, 'duration', fatal=False))

        formats = []

        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'flv_url=(.+?)&', webpage, 'video URL', default=''))
        if video_url:
            formats.append({
                'url': video_url,
                'format_id': 'flv',
            })

        for kind, _, format_url in re.findall(
                r'setVideo([^(]+)\((["\'])(http.+?)\2\)', webpage):
            format_id = kind.lower()
            if format_id == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            elif format_id in ('urllow', 'urlhigh'):
                formats.append({
                    'url': format_url,
                    'format_id': '%s-%s' % (determine_ext(format_url, 'mp4'), format_id[3:]),
                    'quality': -2 if format_id.endswith('low') else None,
                })

        self._sort_formats(formats)

        metadata_node = get_element_by_class("video-metadata", webpage)
        uploader_node = get_element_by_class("uploader-tag", metadata_node)

        uploader = None
        if uploader_node is not None:
            uploader = self._search_regex(
                r'<span[^>]+class=["\']name["\'][^>]*>.*?(?P<name>[^<]+)', uploader_node,
                'name', default=None, group='name', fatal=False)

        uploader_id = self._search_regex(
            r'<a[^>]+href=["\']/?(?:profiles|channels)/(?P<channel>[^"]+)', metadata_node,
            'channel', default=None, group='channel', fatal=False)

        tags = [item.replace("-", " ") for item in re.findall(r'<a[^>]+href=["\']/?tags/(?P<tags>[^"]+)',
                                                              metadata_node)]

        raw_conf = self._search_regex(
            r'conf\s?=\s?(?P<json>.+);', webpage, 'json', default=None, group='json', fatal=False)

        parsed_conf = self._parse_json(
            raw_conf, video_id, transform_source=js_to_json, fatal=False)

        rc_list = try_get(parsed_conf, lambda x: x['data']['related_keywords']) or []
        rc_list_alt = try_get(parsed_conf, lambda x: x['dyn']['ads']['categories'], compat_str) or None
        categories = rc_list or [item.replace('_', ' ') for item in rc_list_alt.split(',')]

        sponsor_dict = try_get(parsed_conf, lambda x: x['data']['sponsors'][0]) or {}
        creator = sponsor_dict.get('n')

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'duration': duration,
            'thumbnails': thumbnails,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'categories': categories,
            'tags': tags,
            'creator': creator,
            'age_limit': 18,
        }

