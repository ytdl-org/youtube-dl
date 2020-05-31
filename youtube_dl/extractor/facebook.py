# coding: utf-8
from __future__ import unicode_literals
import re
import socket

from .common import InfoExtractor
from ..compat import (
    compat_etree_fromstring,
    compat_http_client,
    compat_urllib_error,
    compat_urllib_parse_unquote,
    compat_urllib_parse_unquote_plus
)
from ..utils import (
    clean_html,
    error_to_compat_str,
    ExtractorError,
    get_element_by_id,
    int_or_none,
    js_to_json,
    limit_length,
    parse_count,
    sanitized_Request,
    try_get,
    urlencode_postdata,
    update_url_query,
    lowercase_escape,
    parse_iso8601,
    unescapeHTML,
)

class FacebookIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                (?:
                    https?://
                        (?:[\w-]+\.)?(?:facebook\.com|facebookcorewwwi\.onion)/
                        (?:[^#]*?\#!/)?
                        (?:
                            (?:
                                video/video\.php|
                                photo\.php|
                                video\.php|
                                video/embed|
                                story\.php|
                                watch
                            )\?(?:.*?)(?:v|video_id|story_fbid)=|
                            [^/]+/videos/(?:[^/]+/)?|
                            [^/]+/posts/|
                            groups/[^/]+/permalink/
                        )|
                    facebook:
                )
                (?P<id>[0-9]+)
                '''
    _LOGIN_URL = 'https://www.facebook.com/login.php?next=http%3A%2F%2Ffacebook.com%2Fhome.php&login_attempt=1'
    _CHECKPOINT_URL = 'https://www.facebook.com/checkpoint/?next=http%3A%2F%2Ffacebook.com%2Fhome.php&_fb_noscript=1'
    _NETRC_MACHINE = 'facebook'
    IE_NAME = 'facebook'

    _CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'

    _VIDEO_PAGE_TEMPLATE = 'https://www.facebook.com/video/video.php?v=%s'
    _VIDEO_PAGE_TAHOE_TEMPLATE = 'https://www.facebook.com/video/tahoe/async/%s/?chain=true&isvideo=true&payloadtype=%s'

    _TESTS = [{
        'url': 'https://www.facebook.com/video.php?v=637842556329505&fref=nf',
        'md5': '6a40d33c0eccbb1af76cf0485a052659',
        'info_dict': {
            'id': '637842556329505',
            'ext': 'mp4',
            'title': 're:Did you know Kei Nishikori is the first Asian man to ever reach a Grand Slam',
            'uploader': 'Tennis on Facebook',
            'upload_date': '20140908',
            'timestamp': 1410199200,
        },
        'skip': 'Requires logging in',
    }, {
        'url': 'https://www.facebook.com/video.php?v=274175099429670',
        'info_dict': {
            'id': '274175099429670',
            'ext': 'mp4',
            'title': 're:^Asif Nawab Butt posted a video',
            'uploader': 'Asif Nawab Butt',
            'upload_date': '20140506',
            'timestamp': 1399398998,
            'thumbnail': r're:^https?://.*',
        },
        'expected_warnings': [
            'title'
        ]
    }, {
        'note': 'Video with DASH manifest',
        'url': 'https://www.facebook.com/video.php?v=957955867617029',
        'md5': 'b2c28d528273b323abe5c6ab59f0f030',
        'info_dict': {
            'id': '957955867617029',
            'ext': 'mp4',
            'title': 'When you post epic content on instagram.com/433 8 million followers, this is ...',
            'uploader': 'Demy de Zeeuw',
            'upload_date': '20160110',
            'timestamp': 1452431627,
        },
        'skip': 'Requires logging in',
    }, {
        'url': 'https://www.facebook.com/maxlayn/posts/10153807558977570',
        'md5': '037b1fa7f3c2d02b7a0d7bc16031ecc6',
        'info_dict': {
            'id': '544765982287235',
            'ext': 'mp4',
            'title': '"What are you doing running in the snow?"',
            'uploader': 'FailArmy',
        },
        'skip': 'Video gone',
    }, {
        'url': 'https://m.facebook.com/story.php?story_fbid=1035862816472149&id=116132035111903',
        'md5': '1deb90b6ac27f7efcf6d747c8a27f5e3',
        'info_dict': {
            'id': '1035862816472149',
            'ext': 'mp4',
            'title': 'What the Flock Is Going On In New Zealand  Credit: ViralHog',
            'uploader': 'S. Saint',
        },
        'skip': 'Video gone',
    }, {
        'note': 'swf params escaped',
        'url': 'https://www.facebook.com/barackobama/posts/10153664894881749',
        'md5': '97ba073838964d12c70566e0085c2b91',
        'info_dict': {
            'id': '10153664894881749',
            'ext': 'mp4',
            'title': 'Average time to confirm recent Supreme Court nominees: 67 days Longest it\'s t...',
            'thumbnail': r're:^https?://.*',
            'timestamp': 1456259628,
            'upload_date': '20160223',
            'uploader': 'Barack Obama',
        },
    }, {
        # have 1080P, but only up to 720p in swf params
        'url': 'https://www.facebook.com/cnn/videos/10155529876156509/',
        'md5': '9571fae53d4165bbbadb17a94651dcdc',
        'info_dict': {
            'id': '10155529876156509',
            'ext': 'mp4',
            'title': 'She survived the holocaust — and years later, she’s getting her citizenship s...',
            'timestamp': 1477818095,
            'upload_date': '20161030',
            'uploader': 'CNN',
            'thumbnail': r're:^https?://.*',
            'view_count': int,
        },
    }, {
        # bigPipe.onPageletArrive ... onPageletArrive pagelet_group_mall
        'url': 'https://www.facebook.com/yaroslav.korpan/videos/1417995061575415/',
        'info_dict': {
            'id': '1417995061575415',
            'ext': 'mp4',
            'title': 'md5:1db063d6a8c13faa8da727817339c857',
            'timestamp': 1486648217,
            'upload_date': '20170209',
            'uploader': 'Yaroslav Korpan',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.facebook.com/LaGuiaDelVaron/posts/1072691702860471',
        'info_dict': {
            'id': '1072691702860471',
            'ext': 'mp4',
            'title': 'md5:ae2d22a93fbb12dad20dc393a869739d',
            'timestamp': 1477305000,
            'upload_date': '20161024',
            'uploader': 'La Guía Del Varón',
            'thumbnail': r're:^https?://.*',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.facebook.com/groups/1024490957622648/permalink/1396382447100162/',
        'info_dict': {
            'id': '1396382447100162',
            'ext': 'mp4',
            'title': 'md5:19a428bbde91364e3de815383b54a235',
            'timestamp': 1486035494,
            'upload_date': '20170202',
            'uploader': 'Elisabeth Ahtn',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.facebook.com/video.php?v=10204634152394104',
        'only_matching': True,
    }, {
        'url': 'https://www.facebook.com/amogood/videos/1618742068337349/?fref=nf',
        'only_matching': True,
    }, {
        'url': 'https://www.facebook.com/ChristyClarkForBC/videos/vb.22819070941/10153870694020942/?type=2&theater',
        'only_matching': True,
    }, {
        'url': 'facebook:544765982287235',
        'only_matching': True,
    }, {
        'url': 'https://www.facebook.com/groups/164828000315060/permalink/764967300301124/',
        'only_matching': True,
    }, {
        'url': 'https://zh-hk.facebook.com/peoplespower/videos/1135894589806027/',
        'only_matching': True,
    }, {
        'url': 'https://www.facebookcorewwwi.onion/video.php?v=274175099429670',
        'only_matching': True,
    }, {
        # no title
        'url': 'https://www.facebook.com/onlycleverentertainment/videos/1947995502095005/',
        'only_matching': True,
    }, {
        'url': 'https://www.facebook.com/WatchESLOne/videos/359649331226507/',
        'info_dict': {
            'id': '359649331226507',
            'ext': 'mp4',
            'title': '#ESLOne VoD - Birmingham Finals Day#1 Fnatic vs. @Evil Geniuses',
            'uploader': 'ESL One Dota 2',
            'timestamp': 1527084179,
            'upload_date': '20180523',
            'uploader_id': '234218833769558',
            'is_live': False
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # no timestamp
        'url': 'https://www.facebook.com/SuperNewsGames/videos/642255722780473/',
        'info_dict': {
            'timestamp': 1521221400,
            'uploader': 'Super News Games',
            'uploader_id': '229550157384367',
            'id': '642255722780473',
            'ext': 'mp4',
            'upload_date': '20180316',
            'title': 'The Voice of Nick is trying Fortnite after 100 hours of PLAYERUNKNOWN\'S BATTL...',
        },
        'params': {
            'skip_download': True,
        },
    }]

    @staticmethod
    def _extract_urls(webpage):
        urls = []
        for mobj in re.finditer(
                r'<iframe[^>]+?src=(["\'])(?P<url>https?://www\.facebook\.com/(?:video/embed|plugins/video\.php).+?)\1',
                webpage):
            urls.append(mobj.group('url'))
        # Facebook API embed
        # see https://developers.facebook.com/docs/plugins/embedded-video-player
        for mobj in re.finditer(r'''(?x)<div[^>]+
                class=(?P<q1>[\'"])[^\'"]*\bfb-(?:video|post)\b[^\'"]*(?P=q1)[^>]+
                data-href=(?P<q2>[\'"])(?P<url>(?:https?:)?//(?:www\.)?facebook.com/.+?)(?P=q2)''', webpage):
            urls.append(mobj.group('url'))
        return urls

    def _login(self):
        useremail, password = self._get_login_info()
        if useremail is None:
            return

        login_page_req = sanitized_Request(self._LOGIN_URL)
        self._set_cookie('facebook.com', 'locale', 'en_US')
        login_page = self._download_webpage(login_page_req, None,
                                            note='Downloading login page',
                                            errnote='Unable to download login page')
        lsd = self._search_regex(
            r'<input type="hidden" name="lsd" value="([^"]*)"',
            login_page, 'lsd')
        lgnrnd = self._search_regex(r'name="lgnrnd" value="([^"]*?)"', login_page, 'lgnrnd')

        login_form = {
            'email': useremail,
            'pass': password,
            'lsd': lsd,
            'lgnrnd': lgnrnd,
            'next': 'http://facebook.com/home.php',
            'default_persistent': '0',
            'legacy_return': '1',
            'timezone': '-60',
            'trynum': '1',
        }
        request = sanitized_Request(self._LOGIN_URL, urlencode_postdata(login_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        try:
            login_results = self._download_webpage(request, None,
                                                   note='Logging in', errnote='unable to fetch login page')
            if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
                error = self._html_search_regex(
                    r'(?s)<div[^>]+class=(["\']).*?login_error_box.*?\1[^>]*><div[^>]*>.*?</div><div[^>]*>(?P<error>.+?)</div>',
                    login_results, 'login error', default=None, group='error')
                if error:
                    raise ExtractorError('Unable to login: %s' % error, expected=True)
                self._downloader.report_warning('unable to log in: bad username/password, or exceeded login rate limit (~3/min). Check credentials or wait.')
                return

            fb_dtsg = self._search_regex(
                r'name="fb_dtsg" value="(.+?)"', login_results, 'fb_dtsg', default=None)
            h = self._search_regex(
                r'name="h"\s+(?:\w+="[^"]+"\s+)*?value="([^"]+)"', login_results, 'h', default=None)

            if not fb_dtsg or not h:
                return

            check_form = {
                'fb_dtsg': fb_dtsg,
                'h': h,
                'name_action_selected': 'dont_save',
            }
            check_req = sanitized_Request(self._CHECKPOINT_URL, urlencode_postdata(check_form))
            check_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            check_response = self._download_webpage(check_req, None,
                                                    note='Confirming login')
            if re.search(r'id="checkpointSubmitButton"', check_response) is not None:
                self._downloader.report_warning('Unable to confirm login, you have to login in your browser and authorize the login.')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning('unable to log in: %s' % error_to_compat_str(err))
            return

    def _real_initialize(self):
        self._login()

    def _extract_from_url(self, url, video_id, fatal_if_no_video=True):
        req = sanitized_Request(url)
        req.add_header('User-Agent', self._CHROME_USER_AGENT)
        webpage = self._download_webpage(req, video_id)

        video_data = None

        def extract_video_data(instances):
            for item in instances:
                if item[1][0] == 'VideoConfig':
                    video_item = item[2][0]
                    if video_item.get('video_id'):
                        return video_item['videoData']

        server_js_data = self._parse_json(self._search_regex(
            r'handleServerJS\(({.+})(?:\);|,")', webpage,
            'server js data', default='{}'), video_id, fatal=False)

        if server_js_data:
            video_data = extract_video_data(server_js_data.get('instances', []))

        def extract_from_jsmods_instances(js_data):
            if js_data:
                return extract_video_data(try_get(
                    js_data, lambda x: x['jsmods']['instances'], list) or [])

        if not video_data:
            server_js_data = self._parse_json(
                self._search_regex(
                    r'bigPipe\.onPageletArrive\(({.+?})\)\s*;\s*}\s*\)\s*,\s*["\']onPageletArrive\s+(?:pagelet_group_mall|permalink_video_pagelet|hyperfeed_story_id_\d+)',
                    webpage, 'js data', default='{}'),
                video_id, transform_source=js_to_json, fatal=False)
            video_data = extract_from_jsmods_instances(server_js_data)

        tahoe_data = FacebookTahoeData(self, webpage, video_id)
        if not video_data:
            tahoe_js_data = self._parse_json(
                self._search_regex(
                    r'for\s+\(\s*;\s*;\s*\)\s*;(.+)', tahoe_data.primary,
                    'tahoe js data', default='{}'),
                video_id, fatal=False)

            video_data = extract_from_jsmods_instances(tahoe_js_data)

        if not video_data:
            if not fatal_if_no_video:
                return webpage, False
            m_msg = re.search(r'class="[^"]*uiInterstitialContent[^"]*"><div>(.*?)</div>', webpage)
            if m_msg is not None:
                raise ExtractorError(
                    'The video is not available, Facebook said: "%s"' % m_msg.group(1),
                    expected=True)
            elif '>You must log in to continue' in webpage:
                self.raise_login_required()

        if not video_data:
            info_dict = self.get_from_new_ui(webpage, tahoe_data, url)
            if info_dict:
                return webpage, info_dict

        if not video_data:
            if self._search_regex(r'newsFeedStream.*?<h1><span class.*?>(.*?)<\/span><\/h1>', webpage, "video_title") is not None:
                self.raise_login_required()
            raise ExtractorError('Cannot parse data')

        is_scheduled = '"isScheduledLive":true' in tahoe_data.secondary
        is_live_stream = video_data[0].get('is_live_stream', False)
        is_broadcast = video_data[0].get('is_broadcast', False)

        is_live, live_status = self.extract_live_info(is_scheduled, is_live_stream, is_broadcast)


        subtitles = {}
        formats = []
        for f in video_data:
            format_id = f['stream_type']
            if f and isinstance(f, dict):
                f = [f]
            if not f or not isinstance(f, list):
                continue
            for quality in ('sd', 'hd'):
                for src_type in ('src', 'src_no_ratelimit'):
                    src = f[0].get('%s_%s' % (quality, src_type))
                    if src:
                        preference = -10 if format_id == 'progressive' else 0
                        if quality == 'hd':
                            preference += 5
                        formats.append({
                            'format_id': '%s_%s_%s' % (format_id, quality, src_type),
                            'url': src,
                            'preference': preference,
                        })
            dash_manifest = f[0].get('dash_manifest')
            if dash_manifest:
                formats.extend(self._parse_mpd_formats(
                    compat_etree_fromstring(compat_urllib_parse_unquote_plus(dash_manifest))))
            subtitles_src = f[0].get('subtitles_src')
            if subtitles_src:
                subtitles.setdefault('en', []).append({'url': subtitles_src})
        if not formats:
            raise ExtractorError('Cannot find video formats')

        # Downloads with browser's User-Agent are rate limited. Working around
        # with non-browser User-Agent.
        for f in formats:
            f.setdefault('http_headers', {})['User-Agent'] = 'facebookexternalhit/1.1'

        self._sort_formats(formats)

        video_title = self._extract_video_title(webpage, tahoe_data, video_id)

        def _lowercase_escape(s):
            if s:
                return lowercase_escape(s)


        uploader = clean_html(get_element_by_id('fbPhotoPageAuthorName', webpage)) or \
                   self._search_regex(r'ownerName\s*:\s*"([^"]+)"', webpage, 'uploader',default=None) or \
                   _lowercase_escape(self._search_regex(r'\"ownerName\":"(.+?)"', tahoe_data.secondary, 'uploader_id', fatal=False)) or \
                   self._search_regex(r'ownerName"\s*:\s*"([^"]+)"', webpage, 'uploader', default=None) or \
                   self._og_search_title(webpage, default=None)

        timestamp = self._search_regex(
                r'datePublished":"(.+?)"', webpage,'timestamp', default=None)\
                 or self._search_regex(r'datePublished":"(.+?)"', tahoe_data.secondary, 'timestamp', default=None)\
                 or self._search_regex(r'datePublished":"(.+?)"', tahoe_data.primary, 'timestamp', default=None)
        timestamp = parse_iso8601(timestamp)

        if timestamp == None and webpage.find('Paid Partnership') == -1 or\
                (timestamp == None and webpage.find('Paid Partnership') > -1 and
                 'cookiefile' in self._downloader.params):

            regex_search_result_date_time = self._search_regex(r'data-utime=\\\"(\d+)\\\"', tahoe_data.secondary, 'timestamp', default=None)\
                or self._search_regex(r'data-utime=\\\"(\d+)\\\"', tahoe_data.primary, 'timestamp', default=None)\
                or self._search_regex(r'data-utime=\\\"(\d+)\\\"', webpage,'timestamp', default=None)\
                or self._search_regex(r'<abbr[^>]+data-utime=["\'](\d+)', webpage, 'timestamp', default=None)\
                or self._search_regex(r'<abbr[^>]+data-utime=["\'](\d+)', tahoe_data.secondary, 'timestamp', default=None)\
                or self._search_regex(r'<abbr[^>]+data-utime=["\'](\d+)', tahoe_data.primary, 'timestamp', default=None)

            regex_search_result_publish_time = self._search_regex(r'publish_time&quot;:([\d]+)', webpage, 'timestamp', default=None)\
                             or self._search_regex(r'publish_time&quot;:([\d]+)', tahoe_data.primary, 'timestamp', default=None)\
                             or self._search_regex(r'publish_time&quot;:([\d]+)', tahoe_data.secondary, 'timestamp', default=None)

            timestamp = int_or_none(regex_search_result_date_time) or int_or_none(regex_search_result_publish_time)


        uploader_id = self._search_regex(
            r'ownerid:"([\d]+)', webpage,
            'uploader_id', default=None) or self._search_regex(
            r'[\'\"]ownerid[\'\"]\s*:\s*[\'\"](\d+)[\'\"]',tahoe_data.secondary,
            'uploader_id', default=None) or \
            self._search_regex(r'\\\"page_id\\\"\s*:\s*\\\"(\d+)\\\"', tahoe_data.secondary, 'uploader_id', fatal=False) or \
            self._search_regex(r'content_owner_id_new\\":\\"(\d+)\\"', tahoe_data.secondary, 'uploader_id', fatal=False)

        thumbnail = self._html_search_meta(['og:image', 'twitter:image'], webpage)
        if is_live:
            view_count = parse_count(
                self._search_regex(r'viewerCount:([\d]+)', webpage, 'views', fatal=False) or \
                self._search_regex(r'[\'\"]viewerCount[\'\"]\s*:\s*(\d+)', tahoe_data.primary, 'views', fatal=False)
            )
        else:
            view_count = parse_count(self._extract_views(webpage, tahoe_data))

        other_posts_view_count = parse_count(self._extract_meta_count(['otherPostsViewCount'], webpage, tahoe_data, 'other_post_views'))
        likes_count = parse_count(self._extract_likes(webpage, tahoe_data))
        shares_count = parse_count(self._extract_shares(webpage, tahoe_data))
        comment_count = parse_count(self._extract_comments_count(webpage, tahoe_data))

        uploader_handle = self._resolve_uploader_handle(tahoe_data, uploader_id)

        info_dict = self.build_info_dict(webpage, tahoe_data, video_id, video_title, formats, uploader, timestamp,
                                         thumbnail, view_count, uploader_id, is_live, live_status, likes_count,
                                         shares_count, subtitles, comment_count, other_posts_view_count, uploader_handle)

        return webpage, info_dict



    def get_from_new_ui(self, webpage, tahoe_data, url):

        video_title = self._search_regex(r'"headline":"(.+?")', webpage, 'title')
        comments_count = parse_count(self._search_regex(r'"commentCount":(.+?,)', webpage, 'comments_count'))
        subtitles = self._search_regex(r'"about":"(.+?")', webpage, 'subtitles')
        likes = parse_count(self._extract_likes(webpage, tahoe_data))

        timestamp = self._search_regex(r'"datePublished":"(.+?)"', webpage, 'timestamp')
        timestamp = parse_iso8601(timestamp)

        uploader_json = self._search_regex(r'"author":{(.+?)}', webpage, 'uploader')
        uploader_handle, uploader = self._extract_uploader_info_new_ui(uploader_json)

        ids_json = self._search_regex(r'data-video-channel-id="(.+?)"', webpage, 'ids')
        channel_id, video_id = self._extract_ids_info_new_ui(ids_json)

        post_view_counts = parse_count(self._search_regex(r'"postViewCount":(.+?),', tahoe_data.secondary, 'views'))
        other_post_view_counts = parse_count(self._search_regex(r'"otherPostsViewCount":(.+?),', tahoe_data.secondary, 'other_views'))

        share_counts = parse_count(self._search_regex(r'"sharecount":(.+?),', tahoe_data.secondary, 'other_views'))
        thumbnail = self._search_regex(r'"thumbnailUrl":"(.+?)"', webpage, 'thumbnail')
        is_live, live_status = self.resolve_new_ui_live_info(webpage, tahoe_data)

        formats = self.resolve_new_ui_format(webpage)
        info_dict = self.build_info_dict(webpage, tahoe_data, video_id, video_title, formats, uploader, timestamp,
                                         thumbnail, post_view_counts, channel_id, is_live, live_status, likes,
                                         share_counts, {}, comments_count, other_post_view_counts,
                                         uploader_handle)

        return info_dict

    def build_info_dict(self,webpage, tahoe_data, video_id, video_title=None, formats=None, uploader=None,
                        timestamp=None, thumbnail=None, view_count=None, uploader_id=None, is_live=None, live_status=None,
                        likes_count=None, shares_count=None, subtitles=None, comment_count=None, other_posts_view_count=None,
                        uploader_handle=None):
        info_dict = {
            'id': video_id,
            'title': video_title,
            'formats': formats,
            'uploader': uploader,
            'timestamp': timestamp,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'uploader_id': uploader_id,
            'is_live': is_live,
            'live_status': live_status,
            'like_count': likes_count,
            'share_count': shares_count,
            'subtitles': subtitles,
            'comment_count': comment_count,
            'other_posts_view_count': other_posts_view_count,
            'uploader_handle': uploader_handle,
            '_internal_data': {
                'page': webpage,
                'api_response_list': [tahoe_data.primary, tahoe_data.secondary]
            }
        }
        if uploader_id:
            info_dict['uploader_like_count'] = FacebookAjax(self, webpage, uploader_id).page_likes

        return info_dict

    def _resolve_uploader_handle(self, tahoe_data, uploader_id):
        uploader_handle = self._search_regex(r'"video_path":"\\\/([^\/]+)\\\/', tahoe_data.primary, 'uploader_handle',
                                             fatal=False)
        if uploader_handle == uploader_id:
            uploader_handle = self._search_regex(r'href=\\"https:\\\/\\\/www.facebook.com\\\/(.+?)\\\/\\', tahoe_data.secondary,
                                               'uploader_handle',
                                                 fatal=False)

        return uploader_handle

    def _extract_meta_count(self, fields, webpage, tahoe_data, name, ):
        value = None

        for f in fields:
            if value:
                break
            value = self._search_regex(
                    r'\b%s\s*:\s*["\']([\d,.]+)' % f, webpage, name,
                    default=None
            )
            if value:
                break

            value = self._search_regex(
                r'[\'\"]%s[\'\"]\s*:\s*(\d+)' % f, tahoe_data.secondary, name,
                default=None)

        return value

    def _extract_likes(self, webpage, tahoe_data):
        values = re.findall(r'\blikecount\s*:\s*["\']([\d,.]+)', webpage)
        if values:
            return values[-1]

        values = re.findall(r'[\'\"]\blikecount[\'\"]\s*:\s*(\d+)', tahoe_data.secondary)
        if values:
            return values[-1]

        values = re.findall(r'"reaction_count"\s*:\s*{\s*"count"\s*:\s*(\d+)', tahoe_data.secondary)
        if values:
            return values[-1]

    def _extract_shares(self, webpage, tahoe_data):
        value = self._extract_meta_count(['sharecount'], webpage, tahoe_data, 'shares')
        if value:
            return value
        a = r'(\d+\w) Views'
        values = re.findall(r'"share_count"\s*:\s*{\s*"count"\s*:\s*(\d+)', tahoe_data.secondary)
        if values:
            return values[-1]

    def _extract_comments_count(self, webpage, tahoe_data):
        value = self._extract_meta_count(['commentCount'], webpage, tahoe_data, 'comment_count')
        if value:
            return value

        values = re.findall(r'Comments\s\((\d+)', tahoe_data.secondary)
        if values:
            return values[-1]

    def _extract_views(self, webpage, tahoe_data):
        value = self._extract_meta_count(['postViewCount', 'viewCount'], webpage, tahoe_data, 'likes')
        if value:
            return value

        values = re.findall(r'(\d.\d+\w?) Views', tahoe_data.secondary)
        if values:
            return values[-1]

        values = re.findall(r'(\d+\w?) Views', tahoe_data.secondary)
        if values:
            return values[-1]

        values = re.findall(r'seen_by_count":\"(\d+)\"', tahoe_data.secondary)
        if values:
            return values[-1]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        real_url = self._VIDEO_PAGE_TEMPLATE % video_id if url.startswith('facebook:') else url
        webpage, info_dict = self._extract_from_url(real_url, video_id, fatal_if_no_video=False)

        if info_dict:
            return info_dict

        if '/posts/' in url:
            entries = [
                self.url_result('facebook:%s' % vid, FacebookIE.ie_key())
                for vid in self._parse_json(
                    self._search_regex(
                        r'(["\'])video_ids\1\s*:\s*(?P<ids>\[.+?\])',
                        webpage, 'video ids', group='ids'),
                    video_id)]

            return self.playlist_result(entries, video_id)
        else:
            _, info_dict = self._extract_from_url(
                self._VIDEO_PAGE_TEMPLATE % video_id,
                video_id, fatal_if_no_video=True)
            return info_dict

    def _extract_video_title(self, webpage, tahoe_data, video_id):
        video_title = self._html_search_regex(
            r'<h2\s+[^>]*class="uiHeaderTitle"[^>]*>([^<]*)</h2>', webpage,
            'title', default=None)
        if not video_title:
            video_title = self._html_search_regex(
                r'(?s)<span class="fbPhotosPhotoCaption".*?id="fbPhotoPageCaption"><span class="hasCaption">(.*?)</span>',
                webpage, 'alternative title', default=None)
        if not video_title:
            video_title = self._og_search_title(webpage, default=None)
        if not video_title:
            video_title = self._html_search_meta(
                'description', webpage, 'title', default=None)
        if not video_title:
            values = re.findall(r'videoTitle"\s*:\s*"(.*?)"', tahoe_data.secondary)
            if values:
                video_title = values[-1]
        if video_title:
            video_title = limit_length(video_title, 80)
        else:
            video_title = 'Facebook video #%s' % video_id
        return video_title

    def _extract_uploader_info_new_ui(self, uploader_json):
        uploader_handle = self._search_regex(r'"name":"(.+?")', uploader_json, 'uploader')
        uploader_url = self._search_regex(r'"url":"(.+?")', uploader_json, 'uploader_url')
        uploader_url_str = uploader_url.decode("utf-8")
        uploader = uploader_url_str.split('\\/')[-2]
        return uploader_handle, uploader

    def _extract_ids_info_new_ui(self, ids_json):
        ids_json_str = ids_json.decode("utf-8")
        ids = ids_json_str.split(':')
        channel_id = ids[0]
        video_id = ids[1]
        return channel_id, video_id

    def resolve_new_ui_live_info(self, webpage, tahoe_data):

        is_scheduled = '"isScheduledLive":true' in tahoe_data.secondary
        is_live_stream = self._search_regex(r'"isLiveVOD":(.+?),', tahoe_data.secondary, "vod_live")
        is_broadcast = '"isLiveBroadcast":true' in webpage

        return self.extract_live_info(is_scheduled, is_live_stream, is_broadcast)


    def extract_live_info(self, is_scheduled, is_live_stream, is_broadcast):
        live_status = 'not_live'
        if is_broadcast:
            live_status = 'completed'
            if is_live_stream:
                live_status = 'live'
                if is_scheduled:
                    live_status = 'upcoming'

        is_live = live_status == 'live'

        return is_live, live_status


    def resolve_new_ui_format(self, webpage):
        format_url = self.build_format_url(webpage)
        width = parse_count(self._search_regex(r'<meta property="og:video:width" content="(.+?)"', webpage, 'width'))
        height = parse_count(self._search_regex(r'<meta property="og:video:height" content="(.+?)"', webpage, 'height'))

        formats = []
        formats.append({
            'url': format_url,
            'height': width,
            'width': height,
            'ext': 'mp4',
        })
        return formats

    def build_format_url(self, webpage):
        content_url = self._search_regex(r' content="https(.+?)"', webpage, 'url', fatal=False)
        format_url = 'https%s' % content_url
        format_url = unescapeHTML(format_url)
        return format_url


class FacebookTahoeData:
    def __init__(self, extractor, page, video_id):
        self._page = page
        self._video_id = video_id
        self._extractor = extractor
        self._data = {}

    def _get_data(self, data_type):
        if data_type in self._data:
            data = self._data[data_type]
        else:
            req_data, headers = self._get_request_data_and_headers()
            data = self._extractor._download_webpage(
                self._extractor._VIDEO_PAGE_TAHOE_TEMPLATE % (self._video_id, data_type), self._video_id,
                data=req_data,
                headers=headers
            )
            self._data[data_type] = data
        return '' if not data else data

    @property
    def primary(self):
        return self._get_data('primary')

    @property
    def secondary(self):
        return self._get_data('secondary')

    def _get_request_data_and_headers(self):
        tahoe_request_data = urlencode_postdata(
            {
                '__a': 1,
                '__pc': self._extractor._search_regex(
                    r'pkg_cohort["\']\s*:\s*["\'](.+?)["\']', self._page,
                    'pkg cohort', default='PHASED:DEFAULT'),
                '__rev': self._extractor._search_regex(
                    r'client_revision["\']\s*:\s*(\d+),', self._page,
                    'client revision', default='3944515'),
                'fb_dtsg': self._extractor._search_regex(
                    r'"DTSGInitialData"\s*,\s*\[\]\s*,\s*{\s*"token"\s*:\s*"([^"]+)"',
                    self._page, 'dtsg token', default=''),
            })
        tahoe_request_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        return tahoe_request_data, tahoe_request_headers


class FacebookAjax:
    HOVER_URL_TEMPLATE = 'https://www.facebook.com/ajax/hovercard/user.php?id=111&fb_dtsg_ag=x&endpoint=%2Fajax%2Fhovercard%2Fuser.php%3Fid%3D111&__a=1'

    def __init__(self, extractor, page, page_id):
        self._page = page
        self._page_id = page_id
        self._extractor = extractor
        self._hover_data = None

    def _get_hover_data(self):
        if self._hover_data:
            data = self._hover_data
        else:
            data = self._extractor._download_webpage(
                self._get_request_url(self._page_id), self._page_id
            )
        return '' if not data else data

    @property
    def hover(self):
        return self._get_hover_data()

    @property
    def page_likes(self):
        try:
            return parse_count(
                self._extractor._search_regex(r'\/span>([\d,]+) likes', self.hover, 'uploader_likes', default=None)
            )
        except Exception as e:
            self._extractor.report_warning(self._page_id + str(e))

    def _get_request_url(self, page_id):
        return update_url_query(self.HOVER_URL_TEMPLATE,
            {

                'id': page_id,
                'endpoint': '/ajax/hovercard/user.php?id=%s' % page_id,
                '__a': 1,
                '__pc': self._extractor._search_regex(
                    r'pkg_cohort["\']\s*:\s*["\'](.+?)["\']', self._page,
                    'pkg cohort', default='PHASED:DEFAULT'),
                '__rev': self._extractor._search_regex(
                    r'client_revision["\']\s*:\s*(\d+),', self._page,
                    'client revision', default='3944515'),
                'fb_dtsg': self._extractor._search_regex(
                    r'"DTSGInitialData"\s*,\s*\[\]\s*,\s*{\s*"token"\s*:\s*"([^"]+)"',
                    self._page, 'dtsg token', default=''),
            })


class FacebookPluginsVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[\w-]+\.)?facebook\.com/plugins/video\.php\?.*?\bhref=(?P<id>https.+)'

    _TESTS = [{
        'url': 'https://www.facebook.com/plugins/video.php?href=https%3A%2F%2Fwww.facebook.com%2Fgov.sg%2Fvideos%2F10154383743583686%2F&show_text=0&width=560',
        'md5': '5954e92cdfe51fe5782ae9bda7058a07',
        'info_dict': {
            'id': '10154383743583686',
            'ext': 'mp4',
            'title': 'What to do during the haze?',
            'uploader': 'Gov.sg',
            'upload_date': '20160826',
            'timestamp': 1472184808,
        },
        'add_ie': [FacebookIE.ie_key()],
    }, {
        'url': 'https://www.facebook.com/plugins/video.php?href=https%3A%2F%2Fwww.facebook.com%2Fvideo.php%3Fv%3D10204634152394104',
        'only_matching': True,
    }, {
        'url': 'https://www.facebook.com/plugins/video.php?href=https://www.facebook.com/gov.sg/videos/10154383743583686/&show_text=0&width=560',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        return self.url_result(
            compat_urllib_parse_unquote(self._match_id(url)),
            FacebookIE.ie_key())
