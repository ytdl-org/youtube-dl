# coding: utf-8
from __future__ import unicode_literals

import functools
import itertools
import operator
import re

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..compat import compat_str
from ..utils import ExtractorError
from ..utils import NO_DEFAULT
from ..utils import determine_ext
from ..utils import get_element_by_id
from ..utils import int_or_none
from ..utils import orderedSet
from ..utils import remove_quotes
from ..utils import str_to_int
from ..utils import url_or_none
from ..utils import urlencode_postdata


def _get_page(url, default=1):
    """Returns the value of 'page' from the query string, or default."""
    mobj = re.search(r'page=(\\d+)', url)
    return int_or_none(mobj.group(1), default=default) if mobj else default


def _get_pkey(url, default=None):
    """Returns the value of 'pkey' from the query string, or default."""
    mobj = re.search(r'pkey=(\\d+)', url)
    return mobj.group(1) if mobj else default


def _has_more(webpage):
    """Returns True if webpage is a paged result and has more pages."""
    if 'page_next' in webpage:
        return True
    if 'moreDataBtn' in webpage:
        return True
    if 'scrollLazyload' in webpage:
        return True
    return False


class PornHubBaseIE(InfoExtractor):
    """
    PornHubBaseIE is the base class responsible for extracting videos from PornHub sites
    like PornHub and PornHub Premium.
    """

    _HOST = None  # Must be redefined in subclasses.
    _VALID_URL = None  # Must be redefined in subclasses.

    def _login(self):
        """Must be redefined in subclasses."""
        raise NotImplementedError()

    def _set_cookies(self):
        self._set_cookie(self._HOST, 'age_verified', '1')
        self._set_cookie(self._HOST, 'platform', 'pc')

    def _real_initialize(self):
        self._set_cookies()
        self._login()

    def _extract_playlist_title(self, url, playlist_id=None):
        """Return the playlist title extracted from url, or None."""
        webpage = self._download_webpage(url, playlist_id, 'Metadata', fatal=False)
        if not webpage:
            return None
        patterns = [r'(?s)<a id="watchPlaylist"[^>]*>([^<]+)<\/a>', r'(?s)<h1>([^<]+)</h1>']
        return self._html_search_regex(patterns, webpage, 'playlistTitle', fatal=False)

    def _extract_entries(self, webpage, host):
        """Extract playlist entries from webpage."""

        # Many pages, like profiles, contain multiple video feeds. Here we attempt to drill
        # down to a specific feed before extracting entries.
        if 'id="videoPlaylist"' in webpage:
            container = get_element_by_id('videoPlaylist', webpage)
        elif 'id="videoCategory"' in webpage:
            container = get_element_by_id('videoCategory', webpage)
        elif 'id="mostRecentVideosSection"' in webpage:
            container = get_element_by_id('mostRecentVideosSection', webpage)
        elif 'id="showAllChanelVideos"' in webpage:
            container = get_element_by_id('showAllChanelVideos', webpage)
        elif 'id="showAllChannelVideos"' in webpage:
            container = get_element_by_id('showAllChannelVideos', webpage)
        elif 'id="moreData"' in webpage:
            container = get_element_by_id('moreData', webpage)
        elif 'id="profileContent"' in webpage:
            container = get_element_by_id('profileContent', webpage)
        else:
            container = webpage

        entries = []
        pattern = r'href="/?(view_video\.php\?.*\bviewkey=([\da-z]+[^"]*))"[^>]*\s+title="([^"]+)"'
        for video_url, video_id, video_title in orderedSet(re.findall(pattern, container)):
            video_url = re.sub(r'&?pkey=(\\d+)', '', video_url)  # strip 'pkey' value from video_url, if present
            entries.append(self.url_result(
                'http://%s/%s' % (host, video_url), video_id=video_id, video_title=video_title))
        return entries

    def _extract_paged_entries(self, url, host, playlist_id):
        """Extract playlist entries from a paged url."""
        entries = []
        start_page = _get_page(url)
        for page in itertools.count(start_page):
            try:
                webpage = self._download_webpage(
                    url, playlist_id, 'Page %d' % page, query={'page': page})
                page_entries = self._extract_entries(webpage, host)
                if not page_entries:
                    break
                entries.extend(page_entries)
                if not _has_more(webpage):
                    break
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 404:
                    break
                else:
                    raise
        return entries

    def _real_extract(self, url):
        """Extract individual videos."""
        self._set_cookies()
        host, video_id = re.match(self._VALID_URL, url).groups()

        pkey = _get_pkey(url)
        if pkey is not None:
            if self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading just video because of --no-playlist')
            else:
                self.to_screen('Downloading playlist - add --no-playlist to just download video')
                return self.url_result('https://%s/playlist/%s' % (host, pkey))

        return self._extract_video(host, video_id)

    def _extract_video(self, host, video_id):
        """Extract the video info."""

        # Fetch the video page
        webpage = self._download_webpage(
            'https://%s/view_video.php?viewkey=%s' % (host, video_id), video_id)

        # Check for common issues
        self.assert_not_removed(webpage)
        self.assert_not_private(webpage)
        self.assert_not_paid(webpage)
        self.assert_not_fan_only(webpage)
        self.assert_not_geo_restricted(webpage)

        # Video title
        title = self._extract_title(webpage)
        self.to_screen("Extracting %s" % title)

        # Get video info
        flashvars = self._extract_flash_vars(webpage, video_id)
        video_urls = self._extract_video_urls(webpage, flashvars, video_id)

        # Get counts
        view_count = self._extract_count(
            r'<span class="count">([\d,\.\s]+)</span> views', webpage, 'view')
        like_count = self._extract_count(
            r'<span class="votesUp">([\d,\.\s]+)</span>', webpage, 'like')
        dislike_count = self._extract_count(
            r'<span class="votesDown">([\d,\.\s]+)</span>', webpage, 'dislike')
        comment_count = self._extract_count(
            r'(?s)<div id=\"cmtWrapper\">(:?.*?)\((?P<count>\d+)\)(?:.*?)</div>',
            webpage, 'comment', group='count')

        return {
            'id': video_id,
            'title': title,
            'age_limit': 18,
            'uploader': self._extract_uploader(webpage),
            'upload_date': self._extract_upload_date(video_urls),
            'duration': self._extract_duration(flashvars),
            'thumbnail': self._extract_thumbnail(flashvars),
            'subtitles': self._extract_subtitles(flashvars),
            'tags': self._extract_list(webpage, 'tags'),
            'categories': self._extract_list(webpage, 'categories'),
            'formats': self._extract_formats(video_urls, video_id),
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
        }

    def _extract_flash_vars(self, webpage, video_id):
        """Returns video info from flashvars or an empty dict."""
        return self._parse_json(self._search_regex(
            r'var\s+flashvars_\d+\s*=\s*({.+?});', webpage, 'flashvars', default='{}'), video_id)

    def _extract_js_vars(self, webpage, pattern):
        """Returns video info from js or an empty dict."""
        assignments = self._search_regex(
            pattern, webpage, 'encoded url', default=NO_DEFAULT)
        if not assignments:
            return {}

        assignments = assignments.split(';')

        js_vars = {}

        def parse_js_value(inp):
            inp = re.sub(r'/\*(?:(?!\*/).)*?\*/', '', inp)
            if '+' in inp:
                inps = inp.split('+')
                return functools.reduce(
                    operator.concat, map(parse_js_value, inps))
            inp = inp.strip()
            if inp in js_vars:
                return js_vars[inp]
            return remove_quotes(inp)

        for assn in assignments:
            assn = assn.strip()
            if not assn:
                continue
            assn = re.sub(r'var\s+', '', assn)
            vname, value = assn.split('=', 1)
            js_vars[vname] = parse_js_value(value)

        return js_vars

    def _extract_duration(self, flashvars):
        """Returns the video duration extracted from flashvars."""
        return int_or_none(flashvars.get('video_duration'))

    def _extract_thumbnail(self, flashvars):
        """Returns the video thumbnail extracted from flashvars."""
        return flashvars.get('image_url')

    def _extract_subtitles(self, flashvars):
        """Returns the subtitles extracted from flashvars or an empty list."""
        subtitles = {}
        subtitle_url = url_or_none(flashvars.get('closedCaptionsFile'))
        if subtitle_url:
            subtitles.setdefault('en', []).append({
                'url': subtitle_url,
                'ext': 'srt',
            })
        return subtitles

    def _extract_title(self, webpage):
        """Returns the video title extracted from webpage."""
        return self._html_search_meta('twitter:title', webpage, default=None)

    def _extract_uploader(self, webpage):
        """Returns the uploader extracted from webpage."""
        return self._html_search_regex(
            r'(?s)<div class=\"video-info-row\">.+?<(?:a\b[^>]+\bhref=["\']/(?:(?:user|channel)s|model|pornstar)/|span\b[^>]+\bclass=["\']username)[^>]+>(.+?)<',
            webpage, 'uploader', fatal=False)

    def _extract_upload_date(self, video_urls):
        """Returns the upload date extracted from video_urls."""
        upload_date = None

        for (url, _) in video_urls:
            if upload_date:
                break
            upload_date = self._search_regex(r'/(\d{6}/\d{2})/', url, 'upload data', default=None)

        # Strip
        if upload_date:
            upload_date = upload_date.replace('/', '')
        return upload_date

    def _extract_count(self, pattern, webpage, name, **kwargs):
        """Returns the count extracted from webpage using pattern."""
        return str_to_int(self._search_regex(
            pattern, webpage, '%s count' % name, fatal=False, **kwargs))

    def _extract_list(self, webpage, meta_key):
        """Returns a list of items extracted from webpage (e.g. tags or categories)."""
        div = self._search_regex(
            r'(?s)<div[^>]+\bclass=["\'].*?\b%sWrapper[^>]*>(.+?)</div>'
            % meta_key, webpage, meta_key, default=None)
        if not div:
            return None
        return re.findall(r'<a[^>]+\bhref=[^>]+>([^<]+)', div)

    def _extract_video_urls(self, webpage, flashvars, video_id):
        """Returns video urls extracted from webpage and flashvars or an empty list."""
        video_urls = []
        video_urls_set = set()

        # Get video info
        media_definitions = flashvars.get('mediaDefinitions')
        if isinstance(media_definitions, list):
            for definition in media_definitions:
                if not isinstance(definition, dict):
                    continue
                video_url = definition.get('videoUrl')
                if not video_url or not isinstance(video_url, compat_str):
                    continue
                if video_url in video_urls_set:
                    continue
                video_urls_set.add(video_url)
                video_urls.append((video_url, int_or_none(definition.get('quality'))))

        def add_video_url(video_url):
            v_url = url_or_none(video_url)
            if not v_url:
                return
            if v_url in video_urls_set:
                return
            video_urls.append((v_url, None))
            video_urls_set.add(v_url)

        if not video_urls:
            prefixes = ('media', 'quality')
            js_vars = self._extract_js_vars(
                webpage, r'(var\s+(?:%s)_.+)' % '|'.join(prefixes))

            if js_vars:
                for key, format_url in js_vars.items():
                    if any(key.startswith(p) for p in prefixes):
                        add_video_url(format_url)
            if not video_urls and re.search(
                    r'<[^>]+\bid=["\']lockedPlayer', webpage):
                raise ExtractorError(
                    'Video %s is locked' % video_id, expected=True)

        for mobj in re.finditer(
                r'<a[^>]+\bclass=["\']downloadBtn\b[^>]+\bhref=(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage):
            video_url = mobj.group('url')
            if video_url not in video_urls_set:
                video_urls.append((video_url, None))
                video_urls_set.add(video_url)

        return video_urls

    def _extract_formats(self, video_urls, video_id):
        """Returns formats extracted from video urls or an empty list."""
        formats = []

        for url, height in video_urls:
            ext = determine_ext(url)
            if ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    url, video_id, mpd_id='dash', fatal=False))
                continue
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
                continue

            tbr = None
            mobj = re.search(r'(?P<height>\d+)[pP]?_(?P<tbr>\d+)[kK]', url)
            if mobj:
                tbr = int(mobj.group('tbr'))
                if not height:
                    height = int(mobj.group('height'))

            formats.append({
                'url': url,
                'format_id': '%dp' % height if height else None,
                'height': height,
                'tbr': tbr,
            })

        # Sort
        self._sort_formats(formats)

        return formats

    def assert_not_removed(self, webpage):
        """Check for removed video error."""
        if 'notice video-notice' in webpage and 'removed' in webpage:
            raise ExtractorError(
                'This video has been removed.', expected=True)

    def assert_not_private(self, webpage):
        """Check for private video error."""
        if 'imgPrivateContainer' in webpage:
            raise ExtractorError('This is a private video.', expected=True)

    def assert_not_paid(self, webpage):
        """Check for paid video error."""
        if 'Buy on video player' in webpage:
            raise ExtractorError('This is a paid video.', expected=True)

    def assert_not_fan_only(self, webpage):
        """Check for paid video error."""
        if 'lockedFanText' in webpage:
            raise ExtractorError('This is a fan only video.', expected=True)

    def assert_not_geo_restricted(self, webpage):
        """Check for geo restricted error."""
        if 'videoGeoUnavailable' in webpage:
            self.raise_geo_restricted()


class PornHubIE(PornHubBaseIE):
    """
    PornHubIE handles videos exclusively from pornhub.com.
    """
    IE_NAME = 'pornhub'
    IE_DESC = 'PornHub'

    _NETRC_MACHINE = 'pornhub'

    _HOST = 'pornhub.com'
    _LOGIN_FORM_URL = 'https://%s/login' % _HOST
    _LOGIN_POST_URL = 'https://www.%s/front/authenticate' % _HOST

    _VALID_URL = r'https?://(?P<host>(?:\w+?.)?pornhub\.com)/(?:(?:view_video\.php\?viewkey=)|embed/)(?P<id>[\da-z]+)'

    _TESTS = [{
        'url': 'https://www.pornhub.com/view_video.php?viewkey=ph5dc5ae506c839',
        'md5': '8c05bfb86ded92e266a7df53bc737cd5',
        'info_dict': {
            'id': 'ph5dc5ae506c839',
            'title': 'Моя милая девушка делает минет.  Глубокая глотка подростка.  Лицо ебать.',
            'age_limit': 18,
            'upload_date': '20191108',
            'uploader': 'SladkiSlivki',
            'ext': 'mp4',
        }
    }, {
        'url': 'https://www.pornhub.com/view_video.php?viewkey=ph59fbbbd8c9987',
        'md5': '97dc74166ca00218486fc1538a67ecaf',
        'info_dict': {
            'id': 'ph59fbbbd8c9987',
            'title': 'Asian girl gives dedicated sloopy blowjob',
            'age_limit': 18,
            'upload_date': '20171103',
            'uploader': 'Rae Lil Black',
            'ext': 'mp4',
        }
    }, {
        'url': 'https://fr.pornhub.com/view_video.php?viewkey=ph59fbbbd8c9987',
        'md5': '97dc74166ca00218486fc1538a67ecaf',
        'info_dict': {
            'id': 'ph59fbbbd8c9987',
            'title': 'Asian girl gives dedicated sloopy blowjob',
            'age_limit': 18,
            'upload_date': '20171103',
            'uploader': 'Rae Lil Black',
            'ext': 'mp4',
        }
    }]

    @staticmethod
    def _extract_urls(webpage):
        """Finds urls from the embedded pornhub player; supports the generic extractor."""
        return re.findall(
            r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//(?:www\.)?pornhub\.(?:com|net)/embed/[\da-z]+)',
            webpage)

    @staticmethod
    def _is_authenticated(webpage):
        return '/user/logout' in webpage

    def _login(self):
        username, password = self._get_login_info()

        # Return if no credentials, auth is optional
        if not username or not password:
            return

        # Fetch login page
        login_page = self._download_webpage(
            self._LOGIN_FORM_URL, video_id=None, note='Verifying login', tries=3, fatal=True)

        # Already logged in
        if self._is_authenticated(login_page):
            return self.to_screen("Already authenticated")

        # Fetch login form
        login_form = self._hidden_inputs(login_page)
        login_form.update({
            'username': username,
            'password': password,
        })

        # Submit sign-in request
        response = self._download_json(
            self._LOGIN_POST_URL, video_id=None, note='Sending credentials', fatal=True,
            data=urlencode_postdata(login_form), headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self._LOGIN_POST_URL,
            })

        # Success
        if response.get('success') == '1':
            return self.to_screen("Successfully authenticated")

        # Error
        login_error = response.get('message')
        if login_error:
            raise ExtractorError('Unable to login: %s' % login_error, expected=True)
        self.report_warning('Login has probably failed')


class PornHubProfileIE(PornHubIE):
    """Extract videos from a model, pornstar, user, or channel profile."""

    IE_NAME = 'pornhub:profile'

    _VALID_URL_PARTS = [
        r'https?://(?P<host>(?:\w+?.)?pornhub\.com)/',
        r'(?:model|pornstar|users|channels)/(?P<username>[\w-]+)$'
    ]
    _VALID_URL = re.compile(''.join(_VALID_URL_PARTS))

    _TESTS = [{
        'url': 'https://www.pornhub.com/model/projektmelody',
        'info_dict': {
            'id': 'projektmelody-videos',
        },
        'playlist_mincount': 4,
    }, {
        'url': 'https://www.pornhub.com/pornstar/rae-lil-black',
        'info_dict': {
            'id': 'rae-lil-black-videos',
        },
        'playlist_mincount': 140,
    }, {
        'url': 'https://www.pornhub.com/channels/nubilefilms',
        'info_dict': {
            'id': 'nubilefilms-videos',
        },
        'playlist_mincount': 500,
    }]

    def _real_extract(self, url):
        self._set_cookies()
        return self.url_result('%s/videos' % url)


class PornHubProfileVideosIE(PornHubIE):
    """Extract videos from a model, pornstar, user, or channel profile."""

    IE_NAME = 'pornhub:profile:videos'

    _VALID_URL_PARTS = [
        r'https?://(?P<host>(?:\w+?.)?pornhub\.com)/',
        r'(?:model|pornstar|users|channels)/(?P<username>[\w-]+)/videos(?:/(?P<category>[\w-]+))?'
    ]
    _VALID_URL = re.compile(''.join(_VALID_URL_PARTS))

    _TESTS = [{
        'url': 'https://www.pornhub.com/model/projektmelody/videos',
        'info_dict': {
            'id': 'projektmelody-videos',
        },
        'playlist_mincount': 4,
    }, {
        'url': 'https://www.pornhub.com/pornstar/rae-lil-black/videos',
        'info_dict': {
            'id': 'rae-lil-black-videos',
        },
        'playlist_mincount': 140,
    }, {
        'url': 'https://www.pornhub.com/pornstar/rae-lil-black/videos/paid',
        'info_dict': {
            'id': 'rae-lil-black-paid',
        },
        'playlist_mincount': 40,
    }, {
        'url': 'https://www.pornhub.com/model/sladkislivki/videos',
        'info_dict': {
            'id': 'sladkislivki-videos',
        },
        'playlist_mincount': 60,
    }, {
        'url': 'https://www.pornhub.com/model/sladkislivki/videos/paid',
        'info_dict': {
            'id': 'sladkislivki-paid',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://www.pornhub.com/model/sladkislivki/videos/fanonly',
        'info_dict': {
            'id': 'sladkislivki-fanonly',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://www.pornhub.com/users/lilafair/videos/favorites',
        'info_dict': {
            'id': 'lilafair-favorites',
        },
        'playlist_mincount': 10,
    }, {
        'url': 'https://www.pornhub.com/channels/nubilefilms/videos?o=ra',
        'info_dict': {
            'id': 'nubilefilms-videos',
        },
        'playlist_mincount': 500,
    }]

    def _real_extract(self, url):
        self._set_cookies()
        host, username, category = re.match(self._VALID_URL, url).groups()

        playlist_id = '%s-%s' % (username, category if category else 'videos')
        entries = self._extract_paged_entries(url, host, playlist_id)

        return self.playlist_result(entries, playlist_id)


class PornHubPlaylistIE(PornHubIE):
    """Extract videos from a playlist."""

    IE_NAME = 'pornhub:playlist'
    _VALID_URL = r'https?://(?P<host>(?:\w+?.)?pornhub\.com)/playlist/(?P<playlist_id>[\d]+)'

    _TESTS = [{
        'url': 'https://www.pornhub.com/playlist/58595671',
        'info_dict': {
            'id': '58595671',
            'title': 'Me',
        },
        'playlist_mincount': 30,
    }, {
        'url': 'https://www.pornhub.com/playlist/87244411',
        'info_dict': {
            'id': '87244411',
            'title': 'Friends Of Little Oral Andie',
        },
        'playlist_mincount': 100,
    }]

    def _real_extract(self, url):
        self._set_cookies()
        host, playlist_id = re.match(self._VALID_URL, url).groups()

        entries = self._extract_paged_entries(url, host, playlist_id)

        return self.playlist_result(
            entries, playlist_id, self._extract_playlist_title(url, playlist_id))
