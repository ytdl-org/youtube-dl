# coding: utf-8
from __future__ import unicode_literals

import re
import itertools

from math import isinf

from .common import (
    InfoExtractor,
    SearchInfoExtractor,
)
from ..compat import (
    compat_kwargs,
    compat_str,
    compat_urlparse,
    compat_urllib_parse_unquote,
    compat_urllib_request,
)
from ..utils import (
    clean_html,
    determine_ext,
    extract_attributes,
    ExtractorError,
    get_element_by_class,
    get_element_by_id,
    get_elements_by_class,
    int_or_none,
    join_nonempty,
    LazyList,
    merge_dicts,
    parse_count,
    parse_duration,
    remove_end,
    remove_start,
    T,
    traverse_obj,
    try_call,
    txt_or_none,
    url_basename,
    urljoin,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    (?:
                        https?://
                            (?:
                                # xvideos\d+\.com redirects to xvideos.com
                                # (?P<country>[a-z]{2})\.xvideos.com too: catch it anyway
                                (?:[^/]+\.)?xvideos\.com/(?:video|prof-video-click/model/[^/]+/)|
                                (?:www\.)?xvideos\.es/video|
                                (?:www|flashservice)\.xvideos\.com/embedframe/|
                                static-hw\.xvideos\.com/swf/xv-player\.swf\?.*?\bid_video=
                            )|
                        xvideos:
                    )(?P<id>\d+)
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
        },
        'skip': 'Sorry, this video has been deleted',
    }, {
        'url': 'https://www.xvideos.com/video78250973/hot_blonde_gets_excited_in_the_middle_of_the_club.',
        'md5': '0bc6e46ef55907533ffa0542e45958b6',
        'info_dict': {
            'id': '78250973',
            'ext': 'mp4',
            'title': 'Hot blonde gets excited in the middle of the club.',
            'uploader': 'Deny Barbie Official',
            'age_limit': 18,
            'duration': 302,
        },
    }, {
        # Broken HLS formats
        'url': 'https://www.xvideos.com/video65982001/what_s_her_name',
        'md5': '18ff7d57d4edc3c908fc5b06166dd63d',
        'info_dict': {
            'id': '65982001',
            'ext': 'mp4',
            'title': 'what\'s her name?',
            'uploader': 'Skakdjskdk',
            'age_limit': 18,
            'duration': 120,
            'thumbnail': r're:^https://img-[a-z]+.xvideos-cdn.com/.+\.jpg',
        }
    }, {
        # from PR #30689
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
            'uploader_url': 'https://www.xvideos.com/channels/twistys1',
            'cast': [{'given_name': 'Adriana Chechik', 'url': 'https://www.xvideos.com/pornstars/adriana-chechik'}, {'given_name': 'Abella Danger', 'url': 'https://www.xvideos.com/pornstars/abella-danger'}],
            'view_count': 'lambda c: c >= 4038715',
            'like_count': 'lambda c: c >= 8800',
            'dislike_count': 'lambda c: c >= 3100',
        },
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

    @classmethod
    def suitable(cls, url):
        EXCLUDE_IE = (XVideosRelatedIE, )
        return (False if any(ie.suitable(url) for ie in EXCLUDE_IE)
                else super(XVideosIE, cls).suitable(url))

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
                r'''<span [^>]*\bclass\s*=\s*["']duration\b[^>]+>.*?(\d[^<]+)''',
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
                hls_formats = self._extract_m3u8_formats(
                    format_url, video_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False)
                self._check_formats(hls_formats, video_id)
                formats.extend(hls_formats)
            elif format_id in ('urllow', 'urlhigh'):
                formats.append({
                    'url': format_url,
                    'format_id': '%s-%s' % (determine_ext(format_url, 'mp4'), format_id[3:]),
                    'quality': -2 if format_id.endswith('low') else None,
                })

        self._sort_formats(formats)

        # adapted from PR #30689
        ignore_tags = set(('xvideos', 'xvideos.com', 'x videos', 'x video', 'porn', 'video', 'videos'))
        tags = self._html_search_meta('keywords', webpage) or ''
        tags = [t for t in re.split(r'\s*,\s*', tags) if t not in ignore_tags]

        mobj = re.search(
            r'''(?sx)
                (?P<ul><a\b[^>]+\bclass\s*=\s*["'](?:[\w-]+\s+)*uploader-tag(?:\s+[\w-]+)*[^>]+>)
                \s*<span\s+class\s*=\s*["']name\b[^>]+>\s*(?P<name>.+?)\s*<
            ''', webpage)
        creator = None
        uploader_url = None
        if mobj:
            uploader_url = urljoin(url, extract_attributes(mobj.group('ul')).get('href'))
            creator = mobj.group('name')

        def get_actor_data(mobj):
            ul_url = extract_attributes(mobj.group('ul')).get('href')
            if '/pornstars/' in ul_url:
                return {
                    'given_name': mobj.group('name'),
                    'url': urljoin(url, ul_url),
                }

        actors = traverse_obj(re.finditer(
            r'''(?sx)
                (?P<ul><a\b[^>]+\bclass\s*=\s*["'](?:[\w-]+\s+)*profile(?:\s+[\w-]+)*[^>]+>)
                \s*<span\s+class\s*=\s*["']name\b[^>]+>\s*(?P<name>.+?)\s*<
            ''', webpage), (Ellipsis, T(get_actor_data)))

        return merge_dicts({
            'id': video_id,
            'formats': formats,
            'title': title,
            'age_limit': 18,
        }, {
            'duration': duration,
            'thumbnails': thumbnails or None,
            'tags': tags or None,
            'creator': creator,
            'uploader': creator,
            'uploader_url': uploader_url,
            'cast': actors or None,
            'view_count': parse_count(get_element_by_class(
                'mobile-hide', get_element_by_id('v-views', webpage))),
            'like_count': parse_count(get_element_by_class('rating-good-nbr', webpage)),
            'dislike_count': parse_count(get_element_by_class('rating-bad-nbr', webpage)),
        }, {
            'channel': creator,
            'channel_url': uploader_url,
        } if '/channels/' in (uploader_url or '') else {})


class XVideosPlaylistBaseIE(InfoExtractor):
    def _extract_videos_from_json_list(self, json_list, path='video'):
        return traverse_obj(json_list, (
            Ellipsis, 'id', T(int_or_none),
            T(lambda x: self.url_result('https://www.xvideos.com/%s%d' % (path, x)))))

    def _get_playlist_url(self, url, playlist_id):
        """URL of first playlist page"""
        return url

    def _get_playlist_id(self, playlist_id, **kwargs):
        pnum = kwargs.get('pnum')
        return join_nonempty(playlist_id, pnum, delim='/')

    def _can_be_paginated(self, playlist_id):
        return False

    def _get_title(self, page, playlist_id, **kwargs):
        """title of playlist"""
        title = (
            self._og_search_title(page, default=None)
            or self._html_search_regex(
                r'<title\b[^>]*>([^<]+?)(?:\s+-\s+XVIDEOS\.COM)?</title>',
                page, 'title', default=None)
            or 'XVideos playlist %s' % playlist_id)
        pnum = kwargs.get('pnum')
        pnum = ('p%s' % pnum) if pnum is not None else (
            'all' if self._can_be_paginated(playlist_id) else None)
        if pnum:
            title = '%s (%s)' % (title, pnum)
        return title

    def _get_description(self, page, playlist_id):
        return None

    def _get_next_page(self, url, num, page):
        '''URL of num'th continuation page of url'''
        if page.startswith('{'):
            url, sub = re.subn(r'(/)(\d{1,7})($|[#?/])', r'\g<1>%d\3' % (num, ), url)
            if sub == 0:
                url += '/%d' % num
            return url
        return traverse_obj(
            self._search_regex(
                r'''(?s)(<a\s[^>]*?\bclass\s*=\s*(?P<q>'|")[^>]*?\bnext-page\b.*?(?P=q)[^>]*>)''',
                page, 'next page', default=None),
            (T(extract_attributes), 'href', T(lambda u: urljoin(url, u)))) or False

    def _extract_videos(self, url, playlist_id, num, page):
        """Get iterable video entries plus stop flag"""
        return (
            traverse_obj(
                re.finditer(
                    r'''<div\s[^>]*?id\s*=\s*(\'|")video_(?P<video_id>[0-9]+)\1''', page),
                (Ellipsis, 'video_id', T(lambda x: self.url_result('xvideos:' + x, ie=XVideosIE.ie_key())))),
            None)

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        playlist_id = mobj.group('id')
        pnum = mobj.groupdict().get('pnum')
        webpage = self._download_webpage(url, playlist_id, fatal=False) or ''
        next_page = self._get_playlist_url(url, playlist_id)
        playlist_id = self._get_playlist_id(playlist_id, pnum=pnum, url=url)

        def entries(url, webpage):
            next_page = url
            ids = set()
            for count in itertools.count(0):
                if not webpage:
                    webpage = self._download_webpage(
                        next_page,
                        '%s (+%d)' % (playlist_id, count) if count > 0 else playlist_id)

                vids, stop = self._extract_videos(next_page, playlist_id, count, webpage)

                for from_ in vids:
                    h_id = hash(from_['url'])
                    if h_id not in ids:
                        yield from_
                        ids.add(h_id)

                if stop or pnum is not None:
                    break
                next_page = self._get_next_page(next_page, count + 1, webpage)
                if not next_page:
                    break
                webpage = None

        playlist_title = self._get_title(webpage, playlist_id, pnum=pnum)
        # text may have a final + as an expand widget
        description = remove_end(self._get_description(webpage, playlist_id), '+')

        return merge_dicts(self.playlist_result(
            LazyList(entries(next_page, webpage if next_page == url else None)),
            playlist_id, playlist_title), {
                'description': description,
        })


class XVideosRelatedIE(XVideosPlaylistBaseIE):
    IE_DESC = 'Related videos/playlists in the respective tabs of a video page'
    _VALID_URL = XVideosIE._VALID_URL + r'(?:/[^/]+)*?\#_related-(?P<related>videos|playlists)'

    _TESTS = [{
        'url': 'https://www.xvideos.com/video46474569/solo_girl#_related-videos',
        'info_dict': {
            'id': '46474569/related/videos',
            'title': 'solo girl (related videos)',
        },
        'playlist_mincount': 40,
    }, {
        'url': 'https://www.xvideos.com/video46474569/solo_girl#_related-playlists',
        'info_dict': {
            'id': '46474569/related/playlists',
            'title': 'solo girl (related playlists)',
        },
        'playlist_mincount': 20,
    }]

    def _get_playlist_id(self, playlist_id, **kwargs):
        url = kwargs.get('url')
        return '/related/'.join((
            playlist_id,
            self._match_valid_url(url).group('related')))

    def _get_title(self, page, playlist_id, **kwargs):
        return '%s (%s)' % (
            super(XVideosRelatedIE, self)._get_title(page, playlist_id),
            playlist_id.split('/', 1)[-1].replace('/', ' '))

    def _extract_videos(self, url, playlist_id, num, page):
        related = playlist_id.rsplit('/', 1)[-1]
        if not related:
            return super(XVideosRelatedIE, self)._extract_videos(url, playlist_id, num, page)

        if related == 'videos':
            related_json = self._search_regex(
                r'(?s)videos?_related\s*=\s*(\[.*?])\s*;',
                page, 'related', default='[]')
            related_json = self._parse_json(related_json, playlist_id, fatal=False) or []
            return (self._extract_videos_from_json_list(related_json), True)
        # playlists
        related_json = self._download_json(
            'https://www.xvideos.com/video-playlists/' + playlist_id.split('/', 1)[0], playlist_id, fatal=False)
        return (
            self._extract_videos_from_json_list(
                traverse_obj(related_json, ('playlists', Ellipsis)),
                path='favorite/'),
            True)


class XVideosPlaylistIE(XVideosPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[^/]+\.)?xvideos\d*\.com/
                          (?P<id>gay|shemale|best(?:/\d{4}-\d{2})|(?P<fav>favorite)/\d+)(?:(?(fav)[\w-]+/|)/(?P<pnum>\d+))?
                  '''
    _TESTS = [{
        'url': 'https://www.xvideos.com/best/2023-08/4',
        'info_dict': {
            'id': 'best/2023-08/4',
            'title': 'Playlist best (2023-08, p4)',
        },
        'playlist_count': 27,
    }, {
        'url': 'https://www.xvideos.com/favorite/84800989/mental_health',
        'info_dict': {
            'id': 'favorite/84800989',
            'title': 'Playlist favorite/84800989',
        },
        'playlist_count': 5,
    }]

    def _can_be_paginated(self, playlist_id):
        return True

    def _get_playlist_url(self, url, playlist_id):
        if url.endswith(playlist_id):
            url += '/0'
        return super(XVideosPlaylistIE, self)._get_playlist_url(url, playlist_id)

    def _get_title(self, page, playlist_id, **kwargs):
        pl_id = playlist_id.split('/')
        if pl_id[0] == 'favorite':
            pl_id[0] = '/'.join(pl_id[:2])
            del pl_id[1]
        pnum = int_or_none(pl_id[-1])
        if pnum is not None:
            pl_id[-1] = ' p%d' % pnum
        title = 'Playlist ' + pl_id[0]
        if len(pl_id) > 1:
            title = '%s (%s)' % (title, ','.join(pl_id[1:]))
        return title


class XVideosCategoryIE(XVideosPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                     https?://
                         (?:[^/]+\.)?xvideos\d*\.com/
                         (?P<type>(?P<c>c)|tags)
                         (?P<sub>(?:/[dmqs]:[\w-]+)*)/(?P<id>\w+(?(c)-\d+))
                         (?:/(?P<pnum>\d+))?
                 '''
    _TESTS = [{
        'note': 'videos in category for this month',
        'url': 'https://www.xvideos.com/c/m:month/ASMR-229',
        'info_dict': {
            'id': 'c/ASMR-229/m:month',
            'title': 'Category:ASMR (m=month)',
        },
        'playlist_mincount': 100,
    }, {
        'note': 'page 3 of videos in category for this month',
        'url': 'https://www.xvideos.com/c/m:month/ASMR-229/2',
        'info_dict': {
            'id': 'c/ASMR-229/m:month/2',
            'title': 'Category:ASMR (m=month,p3)',
        },
        'playlist_count': 27,
    }, {
        'note': 'videos tagged yiff',
        'url': 'https://www.xvideos.com/tags/yiff',
        'info_dict': {
            'id': 'tags/yiff',
            'title': 'Tag:yiff',
        },
        'playlist_mincount': 80,
    }, {
        'note': 'page 3 of videos tagged yiff',
        'url': 'https://www.xvideos.com/tags/yiff/2',
        'info_dict': {
            'id': 'tags/yiff/2',
            'title': 'Tag:yiff (p3)',
        },
        'playlist_count': 27,
    }, {
        'note': 'long videos tagged yiff',
        'url': 'https://www.xvideos.com/tags/d:10-20min/yiff',
        'info_dict': {
            'id': 'tags/yiff/d:10-20min',
            'title': 'Tag:yiff (d=10-20min)',
        },
        'playlist_mincount': 20,
        'playlist_maxcount': 40,
    }, {
        'note': 'videos tagged yiff, longest first',
        'url': 'https://www.xvideos.com/tags/s:length/yiff',
        'info_dict': {
            'id': 'tags/yiff/s:length',
            'title': 'Tag:yiff (s=length)',
        },
        'playlist': [{
            'info_dict': {
                'id': r're:\d+',
                'ext': 'mp4',
                'title': r're:\w+',
                'uploader': r're:\w+',
                'age_limit': int,
                'duration': 'lambda c: c >= 1321'  # for video 38266161
            },
        }],
    }]

    def _get_playlist_id(self, playlist_id, **kwargs):
        url = kwargs['url']
        c_type, sub = self._match_valid_url(url).group('type', 'sub')
        sub = sub.split('/')
        sub.append(kwargs.get('pnum'))
        return join_nonempty(c_type, playlist_id, *sub, delim='/')

    def _get_title(self, page, playlist_id, **kwargs):
        pl_id = playlist_id.split('/')
        title = '%s:%s' % ((
            'Category', pl_id[1].rsplit('-', 1)[0]) if pl_id[0] == 'c'
            else ('Tag', pl_id[1]))
        pnum = int_or_none(pl_id[-1])
        if pnum:
            pl_id[-1] = 'p%d' % (pnum + 1)
        subs = ','.join(x.replace(':', '=', 1) for x in pl_id[2:])
        if subs:
            title = '%s (%s)' % (title, subs)
        return title


class XVideosChannelIE(XVideosPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[^/]+\.)?xvideos2?\.com/
                          (?:
                             (?:amateur-|pornstar-|model-)?channel|
                             pornstar|model|profile
                          )s/
                            (?P<id>[^#?/]+)
                              (?:\#(?:
                                (?P<qky>quickies)(?:/a/(?P<vid>\d+))?|
                                _tab(?P<tab>Videos|Favorites|Playlists|AboutMe)
                                    (?:,(?P<sort>new|rating|comments))?
                                    (?:,page-(?P<pnum>\d+))?))?
                 '''
    _TESTS = [{
        'note': 'pornstar-channels',
        'url': 'https://www.xvideos.com/pornstar-channels/sienna-west',
        'info_dict': {
            'id': 'sienna-west',
            'title': 'Sienna West - Pornstar / Channel page',
            'description': r're:Welcome to my official website SiennaWest\.com[\s\S]+!$',
        },
        'playlist_mincount': 5,
    }, {
        'note': 'amateur-channels, no explicit activity',
        'url': 'https://www.xvideos.com/amateur-channels/linamigurtt',
        'info_dict': {
            'id': 'linamigurtt',
            'title': 'Linamigurtt - Amateur / Channel page',
            'description': 'Couple, Amateur, 22y',
        },
        'playlist_mincount': 30,
    }, {
        'note': 'amateur-channels, video tab explicitly selected',
        'url': 'https://www.xvideos.com/amateur-channels/linamigurtt#_tabVideos',
        'info_dict': {
            'id': 'linamigurtt/videos',
            'title': 'Linamigurtt - Amateur / Channel page (videos,all)',
            'description': 'Couple, Amateur, 22y',
        },
        'playlist_mincount': 30,
    },
        # tests from https://github.com/yt-dlp/yt-dlp/pull/2515
        {
        'note': 'channels profile, video tab explicitly selected',
        # not seen in  the wild? 'https://www.xvideos.com/channels/college_girls_gone_bad#_tabVideos,videos-best',
        'url': 'https://www.xvideos.com/channels/college_girls_gone_bad#_tabVideos',
        'info_dict': {
            'id': 'college_girls_gone_bad/videos',
            'title': 'College Girls Gone Bad - Channel page (videos,all)',
            'description': 'Hot college girls in real sorority hazing acts!',
        },
        'playlist_mincount': 100,  # 9 fewer now
    }, {
        'note': 'model-channels profile, video tab explicitly selected',
        # not seen in  the wild? 'https://www.xvideos.com/model-channels/shonariver#_tabVideos,videos-best',
        'url': 'https://www.xvideos.com/model-channels/shonariver#_tabVideos',
        'info_dict': {
            'id': 'shonariver/videos',
            'title': 'Shona River - Model / Channel page (videos,all)',
            'description': r're:Thanks for taking an interest in me\. [\s\S]+filming all over the world\.',
        },
        'playlist_mincount': 183,  # fewer now
    }, {
        'note': 'amateur-channels, default tab',
        'url': 'https://www.xvideos.com/amateur-channels/queanfuckingcucking',
        'info_dict': {
            'id': 'queanfuckingcucking',
            'title': 'Queanfuckingcucking - Amateur / Channel page',
            'description': r're:I’m a cuckquean (?:\w+\s+)+please me by pleasing other women',
        },
        'playlist_mincount': 8,
    }, {
        'note': 'profiles, default tab',
        'url': 'https://www.xvideos.com/profiles/jacobsy',
        'info_dict': {
            'id': 'jacobsy',
            'title': 'Jacobsy - Profile page',
            'description': 'fetishist and bdsm lover...',
        },
        'playlist_mincount': 84,
    }, {
        'note': 'profiles, no description',  # and now, no videos
        'url': 'https://www.xvideos.com/profiles/espoder',
        'info_dict': {
            'id': 'espoder',
            'title': 'Espoder - Profile page',
            'description': 'Man',
        },
        'playlist_count': 0,
    },
        # from https://github.com/yt-dlp/yt-dlp/pull/6414
        {
        'note': 'quickie video',
        'add_ie': ['XVideos'],
        'url': 'https://www.xvideos.com/amateur-channels/wifeluna#quickies/a/47258683',
        'md5': '132e6303f32c051d7461223303ae6730',
        'info_dict': {
            'id': '47258683',
            'ext': 'mp4',
            'title': 'Verification video',
            'uploader': 'My Wife Luna',
            'age_limit': 18,
            'duration': 16,
            'thumbnail': r're:^https://img-\w+\.xvideos-cdn\.com/.+\.jpg',
        }
    },
        # additional tests for coverage
        {
        'note': 'quickie playlist',  # all items, any screen orientation
        'url': 'https://www.xvideos.com/amateur-channels/wifeluna#quickies',
        'info_dict': {
            'id': 'wifeluna/quickies',
            'title': 'My Wife Luna - Amateur / Channel page (quickies)',
            'description': r're:Subscribe to our channel to stay updated on new videos\b',
        },
        'playlist_mincount': 9,
    }, {
        'note': 'model-channels',  # no pagination here: get all videos from tab including premium
        'url': 'https://www.xvideos.com/model-channels/carlacute1',
        'info_dict': {
            'id': 'carlacute1',
            'title': 'Carlacute1 - Model / Channel page',
            'description': r're:Hey, I\'m Carla\.Every single one of my videos is made with a lot of love, passion and joy\.',
        },
        'playlist_mincount': 60,
    }, {
        'note': 'pornstars',
        'url': 'https://www.xvideos.com/pornstars/foxy-di',
        'info_dict': {
            'id': 'foxy-di',
            'title': 'Foxy Di - Pornstar page',
            # AKAs (automatically generated?) may be in any order
            'description': r're:AKA(?: (?:Nensi B Medina|Foxi Di|Kleine Punci)(?:,|$)){3}',
        },
        # When checked, 161 in activities with 19 duplicates
        # check may be a bit wobbly :-)
        'playlist_mincount': 142,
    }, {
        'note': 'pornstars',
        'url': 'https://www.xvideos.com/pornstars/foxy-di#_tabVideos',
        'info_dict': {
            'id': 'foxy-di/videos',
            'title': 'Foxy Di - Pornstar page (videos,all)',
            'description': r're:AKA(?: (?:Nensi B Medina|Foxi Di|Kleine Punci)(?:,|$)){3}',
        },
        # When checked, 9 pages with 36*4, 35*2, 2*36, 34 videos
        # Site says 324, possibly just 9*36
        'playlist_mincount': 320,
    }, {
        'note': 'models',
        'url': 'https://www.xvideos.com/models/mihanika-1',
        'info_dict': {
            'id': 'mihanika-1',
            'title': 'Mihanika - Model page',
            'description': 'AKA Mihanika69',
        },
        # When checked, 90 videos + 2*6 Red promo videos
        'playlist_mincount': 102,
    }, {
        'note': 'models with About Me tab selected',
        'url': 'https://www.xvideos.com/models/mihanika-1#_tabAboutMe',
        'info_dict': {
            'id': 'mihanika-1/aboutme',
            'title': 'Mihanika - Model page (aboutme)',
            'description': 'AKA Mihanika69',
        },
        'playlist_mincount': 8,
    }, {
        'note': 'channel with several playlists',
        'url': 'https://www.xvideos.com/amateur-channels/haitianhershydred#_tabFavorites',
        'info_dict': {
            'id': 'haitianhershydred/favorites',
            'title': 'Haitianhershydred - Amateur / Channel page (favorites,all)',
            'description': r're:I am a bisexual, BDSM, vampire, Hentai lover\b',
        },
        'playlist_mincount': 5,
    }, {
        'note': 'one page',
        'url': 'https://www.xvideos.com/models/mihanika-1#_tabVideos,page-1',
        'info_dict': {
            'id': 'mihanika-1/videos/1',
            'title': 'Mihanika - Model page (videos,p1)',
            'description': 'AKA Mihanika69',
        },
        'playlist_count': 36,
    }, {
        'note': 'sort by rating, first page',
        'url': 'https://www.xvideos.com/models/mihanika-1#_tabVideos,rating,page-1',
        'info_dict': {
            'id': 'mihanika-1/videos/rating/1',
            'title': 'Mihanika - Model page (videos,rating,p1)',
            'description': 'AKA Mihanika69',
        },
        'playlist': [{
            'info_dict': {
                'id': r're:\d+',
                'ext': 'mp4',
                'title': r're:\w+',
                'uploader': r're:\w+',
                'age_limit': int,
                'view_count': 'lambda c: c >= 6798143'  # for video 53924863
            },
        }],
    },

    ]

    @staticmethod
    def _is_quickies_api_url(url_or_req):
        url = url_or_req.get_full_url() if isinstance(url_or_req, compat_urllib_request.Request) else url_or_req
        return '/quickies-api/' in url

    def _get_playlist_id(self, playlist_id, **kwargs):
        url = kwargs['url']
        sub = list(self._match_valid_url(url).group('qky', 'tab', 'sort'))
        qky = sub.pop(0)
        if qky:
            sub = ('quickies',)
        else:
            if sub[0]:
                sub[0] = sub[0].lower()
            sub.append(kwargs.get('pnum'))
        return join_nonempty(playlist_id, *sub, delim='/')

    def _get_title(self, page, playlist_id, **kwargs):
        pnum = kwargs.pop('pnum', None)
        title = super(XVideosChannelIE, self)._get_title(page, playlist_id, **kwargs)
        sub = playlist_id.split('/')[1:]
        id_pnum = traverse_obj(sub, (-1, T(int_or_none)))
        if id_pnum is not None:
            del sub[-1]
            if pnum is None:
                pnum = id_pnum + 1
        sub.append(('p%s' % pnum) if pnum is not None else (
            'all' if len(sub) > 0 and sub[0] in ('videos', 'favorites')
            else None))
        sub = join_nonempty(*sub, delim=',')
        if sub:
            title = '%s (%s)' % (title, sub)
        return title

    def _get_description(self, page, playlist_id):
        return (
            clean_html(get_element_by_id('header-about-me', page))
            or ''.join([
                txt for txt in map(clean_html, get_elements_by_class('mobile-hide', page))
                if txt][1:2])
            or super(XVideosChannelIE, self)._get_description(page, playlist_id))

    # specialisation to get 50 quickie items instead of 20
    def _download_webpage(self, url_or_req, video_id, *args, **kwargs):
        # note, errnote, fatal, tries, timeout, encoding, data=None,
        # headers, query, expected_status
        if self._is_quickies_api_url(url_or_req):
            data = args[6] if len(args) > 6 else kwargs.get('data')
            ndata = data or ''
            ndata = remove_start(ndata + '&nb_videos=50', '&')
            if len(args) <= 6:
                kwargs['data'] = ndata.encode('utf-8')
                kwargs = compat_kwargs(kwargs)
            elif len(args) > 6 and not data:
                args = args[:6] + (ndata,) + args[7:]

        return super(XVideosChannelIE, self)._download_webpage(url_or_req, video_id, *args, **kwargs)

    def _get_playlist_url(self, url, playlist_id):

        def get_url_for_tab(tab, url):
            if tab in ('videos', 'favorites'):
                new_url, frag = compat_urlparse.urldefrag(url)
                if not url.endswith('/'):
                    new_url += '/'
                frag = frag.split(',')[1:]
                pnum = traverse_obj(frag, (-1, T(lambda s: s.replace('page-', '')), T(int_or_none)))
                if pnum is None or pnum < 1:
                    pnum = '0'
                else:
                    pnum = compat_str(pnum - 1)
                    del frag[-1]
                if tab == 'videos':
                    if not frag:
                        frag = ['best']
                else:
                    frag = []
                return new_url + '/'.join([tab] + frag + [pnum])
            return url

        tab = traverse_obj(self._match_valid_url(url), (
            'tab', T(compat_str.lower)))
        if tab:
            return get_url_for_tab(tab, url)

        # no explicit tab: default to activity, or quickies if specified
        webpage = self._download_webpage(url, playlist_id, note='Getting activity details')
        quickies = self._match_valid_url(url).group('qky')
        if not (quickies or get_element_by_id('tab-activity', webpage)):
            # page has no activity tab: videos is populated instead
            return get_url_for_tab('videos', url)
        conf = self._search_regex(
            r'(?s)\.\s*xv\s*\.\s*conf\s*=\s*(\{.*?})[\s;]*</script',
            webpage, 'XV conf')
        conf = self._parse_json(conf, playlist_id)
        act = traverse_obj(conf, (
            'dyn', ('page_main_cat', 'user_main_cat'), T(txt_or_none)), get_all=False) or 'straight'
        url, _ = compat_urlparse.urldefrag(url)
        if quickies:
            user_id = traverse_obj(conf, ('data', 'user', 'id_user', T(txt_or_none)))
            return urljoin(
                # .../N/... seems to be the same as .../B/...
                url, '/quickies-api/profilevideos/all/%s/B/%s/0' % (act, user_id))
        if url.endswith('/'):
            url = url[:-1]

        return '%s/activity/%s' % (url, act, )

    def _get_next_page(self, url, num, page):
        if page.startswith('{') or '#_tab' in url:
            return super(XVideosChannelIE, self)._get_next_page(url, num, page)

        if '/favorites/' in url:
            if get_element_by_class('next-page', page):
                return re.sub(r'(/)\d+($|[#?/])', r'\g<1>%d\2' % (num, ), url)
            return None

        act_time = int_or_none(url_basename(url)) or 0
        last_act = int(self._search_regex(
            r'(?s)id\s*=\s*"?activity-event-(\d{10})(?!.*id\s*=\s*"?activity-event-\d+.*).+$',
            page, 'last activity', default=act_time))
        if last_act == act_time:
            return False
        return (
            url.replace('/%d' % (act_time, ), '/%d' % (last_act, ))
            if act_time
            else url + ('/%d' % (last_act, )))

    def _extract_videos(self, url, playlist_id, num, page):
        if self._is_quickies_api_url(url):
            tab_json = self._parse_json(page, playlist_id, fatal=False) or {}
            return (
                self._extract_videos_from_json_list(
                    traverse_obj(tab_json, ('videos', Ellipsis))),
                not traverse_obj(tab_json, ('hasMoreVideos', T(lambda h: h is True))))

        tab = traverse_obj(re.search(r'/(videos|favorites)/', url), 1)
        if tab == 'videos':
            tab_json = self._parse_json(page, playlist_id, fatal=False) or {}
            more = try_call(
                lambda cp, nv, np: nv - (cp + 1) * np,
                args=(traverse_obj(tab_json, x) for x in (
                    'current_page', 'nb_videos', 'nb_per_page')))

            return (
                self._extract_videos_from_json_list(
                    traverse_obj(tab_json, ('videos', Ellipsis))),
                True if more is None else more <= 0)

        if tab == 'favorites':
            return ((
                self.url_result('https://www.xvideos.com' + x.group('playlist'))
                for x in re.finditer(r'''<a\s[^>]*?href\s*=\s*('|")(?P<playlist>/favorite/\d+/[^#?]+?)\1''', page)),
                None)

        return super(XVideosChannelIE, self)._extract_videos(url, playlist_id, num, page)

    # specialisation to resolve Quickie video URLs
    def _real_extract(self, url):
        video_id = self._match_valid_url(url).group('vid')
        if video_id:
            return self.url_result('xvideos:' + video_id)
        return super(XVideosChannelIE, self)._real_extract(url)


class XVideosSearchIE(XVideosPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[^/]+\.)?xvideos2?\.com/
                          \?k=(?P<id>[^#?/&]+)
                          (?:&[^&]+)*?(?:&p=(?P<pnum>\d+))?
                 '''
    _TESTS = [{
        'note': 'paginated search result',
        'url': 'http://www.xvideos.com/?k=lithuania',
        'info_dict': {
            'id': 'lithuania',
            'title': 'lithuania (all)',
        },
        'playlist_mincount': 75,
    }, {
        'note': 'second page of paginated search result',
        'url': 'http://www.xvideos.com/?k=lithuania&p=1',
        'info_dict': {
            'id': 'lithuania/1',
            'title': 'lithuania (p2)',
        },
        'playlist_count': 27,
    }, {
        'note': 'search with sort',
        'url': 'http://www.xvideos.com/?k=lithuania&sort=length',
        'info_dict': {
            'id': 'lithuania/sort=length',
            'title': 'lithuania (sort=length,all)',
        },
        'playlist': [{
            'info_dict': {
                'id': r're:\d+',
                'ext': 'mp4',
                'title': r're:\w+',
                'uploader': r're:\w+',
                'age_limit': int,
                'duration': 'lambda d: d >= 4954',  # for video 56455303:
            },
        }],
    }]

    def _get_playlist_id(self, playlist_id, **kwargs):
        url = kwargs['url']
        sub = compat_urlparse.urlsplit(url).query
        sub = re.sub(r'(^|&)k=[^&]+(?:&|$)', r'\1', sub)
        sub = re.sub(r'(^|&)p=', r'\1', sub)
        return join_nonempty(
            playlist_id, sub.replace('&', '/') or None, delim='/')

    def _get_title(self, page, playlist_id, **kwargs):
        pnum = int_or_none(kwargs.pop('pnum', None))
        title = super(XVideosSearchIE, self)._get_title(page, playlist_id, **kwargs)
        title, t_pnum = (title.split(', page ') + [None])[:2]
        # actually, let's ignore the page title
        title = playlist_id.split('/')
        sub = title[1:]
        title = title[0]
        id_pnum = traverse_obj(sub, (
            -1, T(lambda s: s.split('=')), -1, T(int_or_none)))
        if id_pnum is not None:
            del sub[-1]
            if pnum is None:
                pnum = id_pnum
        if pnum is None:
            t_pnum = int_or_none(t_pnum)
            if t_pnum is not None:
                pnum = t_pnum
        sub.append(('p%s' % (pnum + 1)) if pnum is not None else 'all')

        sub = join_nonempty(*sub, delim=',')
        if sub:
            title = '%s (%s)' % (title, sub)
        return title


class XVideosSearchKeyIE(SearchInfoExtractor, XVideosSearchIE):
    _SEARCH_KEY = 'xvsearch'
    _MAX_RESULTS = float('inf')
    _TESTS = [{
        'note': 'full search',
        'url': 'xvsearchall:lithuania',
        'info_dict': {
            'id': 'lithuania',
            'title': 'lithuania (all)',
        },
        'playlist_mincount': 75,
    }, {
        'note': 'Subset of paginated result',
        'url': 'xvsearch50:lithuania',
        'info_dict': {
            'id': 'lithuania',
            'title': 'lithuania (first 50)',
        },
        'playlist_count': 50,
    }]

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""

        result = XVideosSearchIE._real_extract(
            self, 'https://www.xvideos.com/?k=' + query.replace(' ', '+'))

        if not isinf(n):
            result['entries'] = itertools.islice(result['entries'], n)
            if result.get('title') is not None:
                result['title'] = result['title'].replace('(all)', '(first %d)' % n)

        return result
