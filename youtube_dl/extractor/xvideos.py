from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    clean_html,
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_duration,
    str_to_int,
    urljoin,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[^/]+\.)?xvideos2?\.com/video|
                            (?:www\.)?xvideos\.es/video|
                            flashservice\.xvideos\.com/embedframe/|
                            static-hw\.xvideos\.com/swf/xv-player\.swf\?.*?\bid_video=
                        )
                        (?P<id>[0-9]+)
                    '''
    _TESTS = [{
        'url': 'https://www.xvideos.com/video50011247/when_girls_play_-_adriana_chechik_abella_danger_-_tradimento_-_twistys',
        'md5': 'aa54f96311768b3a8bfe54b8c8fda070',
        'info_dict': {
            'id': '50011247',
            'ext': 'mp4',
            'title': 'When Girls Play - (Adriana Chechik, Abella Danger) - Betrayal - Twistys',
            'duration': 720,
            'age_limit': 18,
            'tags': ['lesbian', 'teen', 'hardcore', 'latina', 'rough', 'squirt', 'big-ass', 'cheater', 'twistys', 'cheat', 'ass-play', 'when-girls-play'],
            'creator': 'Twistys',
            'uploader': 'Twistys',
            'uploader_id': 'Twistys',
            'uploader_url': '/channels/twistys1',
            'actors': [{'given_name': 'Adriana Chechik', 'url': 'https://www.xvideos.com/pornstars/adriana-chechik'}, {'given_name': 'Abella Danger', 'url': 'https://www.xvideos.com/pornstars/abella-danger'}],
            'view_count': int,
        }
    }, {
        'url': 'https://flashservice.xvideos.com/embedframe/4588838',
        'only_matching': True,
    }, {
        'url': 'http://static-hw.xvideos.com/swf/xv-player.swf?id_video=4588838',
        'only_matching': True,
    }, {
        'url': 'http://xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://www.xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://www.xvideos.es/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://fr.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://fr.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://it.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://it.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'http://de.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }, {
        'url': 'https://de.xvideos.com/video4588838/biker_takes_his_girl',
        'only_matching': True
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.xvideos.com/video%s/0' % video_id, video_id)

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

        tags = self._search_regex(r'<meta name="keywords" content="xvideos,xvideos\.com, x videos,x video,porn,video,videos,(?P<tag>.+?)"', webpage, 'tags', group='tag', default='').split(',')

        creator_data = re.findall(r'<a href="(?P<creator_url>.+?)" class="btn btn-default label main uploader-tag hover-name"><span class="name">(?P<creator>.+?)<', webpage)
        creator = None
        uploader_url = None
        if creator_data != []:
            uploader_url, creator = creator_data[0][0:2]

        actors_data = re.findall(r'href="(?P<actor_url>/pornstars/.+?)" class="btn btn-default label profile hover-name"><span class="name">(?P<actor_name>.+?)</span>', webpage)
        actors = []
        if actors_data != []:
            for actor_tuple in actors_data:
                actors.append({
                    'given_name': actor_tuple[1],
                    'url': urljoin(url, actor_tuple[0]),
                })

        views = self._search_regex(r'<strong class="mobile-hide">(?P<views>.+?)<', webpage, 'views', group='views', default=None)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'duration': duration,
            'thumbnails': thumbnails,
            'age_limit': 18,
            'tags': tags,
            'creator': creator,
            'uploader': creator,
            'uploader_id': creator,
            'uploader_url': uploader_url,
            'actors': actors,
            'view_count': str_to_int(views),
        }
