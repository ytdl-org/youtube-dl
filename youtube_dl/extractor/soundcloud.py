# coding: utf-8
from __future__ import unicode_literals

import itertools
import re
import time
import random

from .common import (
    InfoExtractor,
    SearchInfoExtractor
)
from ..compat import (
    compat_HTTPError,
    compat_kwargs,
    compat_str,
    compat_urlparse,
)
from ..utils import (
    error_to_compat_str,
    ExtractorError,
    float_or_none,
    HEADRequest,
    int_or_none,
    KNOWN_EXTENSIONS,
    mimetype2ext,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
    urlhandle_detect_ext,
)


class SoundcloudEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:w|player|p)\.soundcloud\.com/player/?.*?\burl=(?P<id>.+)'
    _TEST = {
        # from https://www.soundi.fi/uutiset/ennakkokuuntelussa-timo-kaukolammen-station-to-station-to-station-julkaisua-juhlitaan-tanaan-g-livelabissa/
        'url': 'https://w.soundcloud.com/player/?visual=true&url=https%3A%2F%2Fapi.soundcloud.com%2Fplaylists%2F922213810&show_artwork=true&maxwidth=640&maxheight=960&dnt=1&secret_token=s-ziYey',
        'only_matching': True,
    }

    @staticmethod
    def _extract_urls(webpage):
        return [m.group('url') for m in re.finditer(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?://)?(?:w\.)?soundcloud\.com/player.+?)\1',
            webpage)]

    def _real_extract(self, url):
        query = compat_urlparse.parse_qs(
            compat_urlparse.urlparse(url).query)
        api_url = query['url'][0]
        secret_token = query.get('secret_token')
        if secret_token:
            api_url = update_url_query(api_url, {'secret_token': secret_token[0]})
        return self.url_result(api_url)


class SoundcloudIE(InfoExtractor):
    """Information extractor for soundcloud.com
       To access the media, the uid of the song and a stream token
       must be extracted from the page source and the script must make
       a request to media.soundcloud.com/crossdomain.xml. Then
       the media can be grabbed by requesting from an url composed
       of the stream token and uid
     """

    _VALID_URL = r'''(?x)^(?:https?://)?
                    (?:(?:(?:www\.|m\.)?soundcloud\.com/
                            (?!stations/track)
                            (?P<uploader>[\w\d-]+)/
                            (?!(?:tracks|albums|sets(?:/.+?)?|reposts|likes|spotlight)/?(?:$|[?#]))
                            (?P<title>[\w\d-]+)/?
                            (?P<token>[^?]+?)?(?:[?].*)?$)
                       |(?:api(?:-v2)?\.soundcloud\.com/tracks/(?P<track_id>\d+)
                          (?:/?\?secret_token=(?P<secret_token>[^&]+))?)
                    )
                    '''
    IE_NAME = 'soundcloud'
    _TESTS = [
        {
            'url': 'http://soundcloud.com/ethmusic/lostin-powers-she-so-heavy',
            'md5': 'ebef0a451b909710ed1d7787dddbf0d7',
            'info_dict': {
                'id': '62986583',
                'ext': 'mp3',
                'title': 'Lostin Powers - She so Heavy (SneakPreview) Adrian Ackers Blueprint 1',
                'description': 'No Downloads untill we record the finished version this weekend, i was too pumped n i had to post it , earl is prolly gonna b hella p.o\'d',
                'uploader': 'E.T. ExTerrestrial Music',
                'uploader_id': '1571244',
                'timestamp': 1349920598,
                'upload_date': '20121011',
                'duration': 143.216,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            }
        },
        # geo-restricted
        {
            'url': 'https://soundcloud.com/the-concept-band/goldrushed-mastered?in=the-concept-band/sets/the-royal-concept-ep',
            'info_dict': {
                'id': '47127627',
                'ext': 'mp3',
                'title': 'Goldrushed',
                'description': 'From Stockholm Sweden\r\nPovel / Magnus / Filip / David\r\nwww.theroyalconcept.com',
                'uploader': 'The Royal Concept',
                'uploader_id': '9615865',
                'timestamp': 1337635207,
                'upload_date': '20120521',
                'duration': 227.155,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # private link
        {
            'url': 'https://soundcloud.com/jaimemf/youtube-dl-test-video-a-y-baw/s-8Pjrp',
            'md5': 'aa0dd32bfea9b0c5ef4f02aacd080604',
            'info_dict': {
                'id': '123998367',
                'ext': 'mp3',
                'title': 'Youtube - Dl Test Video \'\' Ä↭',
                'description': 'test chars:  \"\'/\\ä↭',
                'uploader': 'jaimeMF',
                'uploader_id': '69767071',
                'timestamp': 1386604920,
                'upload_date': '20131209',
                'duration': 9.927,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # private link (alt format)
        {
            'url': 'https://api.soundcloud.com/tracks/123998367?secret_token=s-8Pjrp',
            'md5': 'aa0dd32bfea9b0c5ef4f02aacd080604',
            'info_dict': {
                'id': '123998367',
                'ext': 'mp3',
                'title': 'Youtube - Dl Test Video \'\' Ä↭',
                'description': 'test chars:  \"\'/\\ä↭',
                'uploader': 'jaimeMF',
                'uploader_id': '69767071',
                'timestamp': 1386604920,
                'upload_date': '20131209',
                'duration': 9.927,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # downloadable song
        {
            'url': 'https://soundcloud.com/oddsamples/bus-brakes',
            'md5': '7624f2351f8a3b2e7cd51522496e7631',
            'info_dict': {
                'id': '128590877',
                'ext': 'mp3',
                'title': 'Bus Brakes',
                'description': 'md5:0053ca6396e8d2fd7b7e1595ef12ab66',
                'uploader': 'oddsamples',
                'uploader_id': '73680509',
                'timestamp': 1389232924,
                'upload_date': '20140109',
                'duration': 17.346,
                'license': 'cc-by-sa',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # private link, downloadable format
        {
            'url': 'https://soundcloud.com/oriuplift/uponly-238-no-talking-wav/s-AyZUd',
            'md5': '64a60b16e617d41d0bef032b7f55441e',
            'info_dict': {
                'id': '340344461',
                'ext': 'wav',
                'title': 'Uplifting Only 238 [No Talking] (incl. Alex Feed Guestmix) (Aug 31, 2017) [wav]',
                'description': 'md5:fa20ee0fca76a3d6df8c7e57f3715366',
                'uploader': 'Ori Uplift Music',
                'uploader_id': '12563093',
                'timestamp': 1504206263,
                'upload_date': '20170831',
                'duration': 7449.096,
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        # no album art, use avatar pic for thumbnail
        {
            'url': 'https://soundcloud.com/garyvee/sideways-prod-mad-real',
            'md5': '59c7872bc44e5d99b7211891664760c2',
            'info_dict': {
                'id': '309699954',
                'ext': 'mp3',
                'title': 'Sideways (Prod. Mad Real)',
                'description': 'md5:d41d8cd98f00b204e9800998ecf8427e',
                'uploader': 'garyvee',
                'uploader_id': '2366352',
                'timestamp': 1488152409,
                'upload_date': '20170226',
                'duration': 207.012,
                'thumbnail': r're:https?://.*\.jpg',
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://soundcloud.com/giovannisarani/mezzo-valzer',
            'md5': 'e22aecd2bc88e0e4e432d7dcc0a1abf7',
            'info_dict': {
                'id': '583011102',
                'ext': 'mp3',
                'title': 'Mezzo Valzer',
                'description': 'md5:4138d582f81866a530317bae316e8b61',
                'uploader': 'Micronie',
                'uploader_id': '3352531',
                'timestamp': 1551394171,
                'upload_date': '20190228',
                'duration': 180.157,
                'thumbnail': r're:https?://.*\.jpg',
                'license': 'all-rights-reserved',
                'view_count': int,
                'like_count': int,
                'comment_count': int,
                'repost_count': int,
            },
        },
        {
            # with AAC HQ format available via OAuth token
            'url': 'https://soundcloud.com/wandw/the-chainsmokers-ft-daya-dont-let-me-down-ww-remix-1',
            'only_matching': True,
        },
    ]

    _API_V2_BASE = 'https://api-v2.soundcloud.com/'
    _BASE_URL = 'https://soundcloud.com/'
    _IMAGE_REPL_RE = r'-([0-9a-z]+)\.jpg'

    _ARTWORK_MAP = {
        'mini': 16,
        'tiny': 20,
        'small': 32,
        'badge': 47,
        't67x67': 67,
        'large': 100,
        't300x300': 300,
        'crop': 400,
        't500x500': 500,
        'original': 0,
    }

    def _store_client_id(self, client_id):
        self._downloader.cache.store('soundcloud', 'client_id', client_id)

    def _update_client_id(self):
        webpage = self._download_webpage('https://soundcloud.com/', None)
        for src in reversed(re.findall(r'<script[^>]+src="([^"]+)"', webpage)):
            script = self._download_webpage(src, None, fatal=False)
            if script:
                client_id = self._search_regex(
                    r'client_id\s*:\s*"([0-9a-zA-Z]{32})"',
                    script, 'client id', default=None)
                if client_id:
                    self._CLIENT_ID = client_id
                    self._store_client_id(client_id)
                    return
        raise ExtractorError('Unable to extract client id')

    def _download_json(self, *args, **kwargs):
        non_fatal = kwargs.get('fatal') is False
        if non_fatal:
            del kwargs['fatal']
        query = kwargs.get('query', {}).copy()
        for _ in range(2):
            query['client_id'] = self._CLIENT_ID
            kwargs['query'] = query
            try:
                return super(SoundcloudIE, self)._download_json(*args, **compat_kwargs(kwargs))
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                    self._store_client_id(None)
                    self._update_client_id()
                    continue
                elif non_fatal:
                    self._downloader.report_warning(error_to_compat_str(e))
                    return False
                raise

    _CLIENT_ID = 'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'
    _USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.50' #MS EDGE CHROME-BASED
    _USERNAME = ''
    _PASSWORD = ''
    _KEY = '0763ed7314c69015fd4a0dc16bbf4b90'

    def _real_initialize(self):
        self._CLIENT_ID, _CLIENT_ID = self._downloader.cache.load('soundcloud', 'client_id') or 'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd' #'YUKXoArFcqrlQn9tfNHvvyfnDISj04zk'
        self._USERNAME, self._PASSWORD = self._get_login_info()
        _USERNAME = self._USERNAME
        _PASSWORD = self._PASSWORD
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        '''
        EXAMPLE
        {"client_id":"EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd","recaptcha_pubkey":"6Ld72JcUAAAAAItDloUGqg6H38KK5j08VuQlegV1","recaptcha_response":null,"credentials":{"identifier":user,"password":password},"signature":"8:33-1-53791-767-2073600-1028-25-25:3b9024:4","device_id":"71542-609622-728970-275967","user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36 Edg/84.0.522.50"}
        

        call_payload = {
                client_id: u.clientId,
                recaptcha_pubkey: p,
                recaptcha_response: 0 < n.length ? n : null,
                credentials: {
                    identifier: e,
                    password: t
                },
                signature: l.sign(e, u.clientId, c),
                device_id: u.deviceId,
                user_agent: h
                }
        '''

        '''
        var t, n, o = ["touchmove", "webdriver", "__webdriver_script_fn", "Chromium PDF Viewer", "$cdc_asdjflasutopfhvcZLmcfl_", "keydown", "typeof process", "encodeURIComponent", "getAttribute", "document", "unescape", "256", "call", "Chrome PDF Viewer", "_Selenium_IDE_Recorder", "width", "TestUA", "location", "name", "forEach", "length", "Chrome PDF Plugin", "512", "mozInnerScreenY", "Date", "addEventListener", "Native Client", "424242", "exports", "height", "Widevine Content Decryption Module", "mousemove", "keyup", "1024", "420", "https:", "128", "plugins", "charCodeAt", "4096", "typeof global", "undefined", "now", "msLaunchUri", "screen", "eval", "safari", "navigator", "WebKit built-in PDF", "isTrusted"];
        t = o,
        n = 219,
        function(e) {
            for (; --e; )
                t.push(t.shift())
        }(++n);
        var g = function(e, t) {
            return o[e -= 0]
        };
        e[g("0x9")] = {
            initialize: function() {
                v = window[g("0x5")].now();
                var e = function(e) {
                    try {
                        if (!1 === e[g("0x1e")])
                            return
                    } catch (e) {}
                    w += 1
                };
                window[g("0x6")](g("0xc"), e),
                window[g("0x6")](g("0x1f"), e),
                window[g("0x6")](g("0x24"), function() {
                    b += 1
                }),
                window.addEventListener(g("0xd"), function() {
                    k += 1
                }),
                window[g("0x6")]("click", function() {
                    _ += 1
                })
            }
        '''

        '''
        sign: function(e, t, n, o) {e = "tom_heidel@web.de", t = "EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd", n = "0763ed7314c69015fd4a0dc16bbf4b90", o = undefined
            r = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
            }

        ## ignore
        #var g = function(e, t) {
        #    return o[e -= 0]
        #};
        #Return value: "$cdc_asdjflasutopfhvcZLmcfl_"

        var s = window[g("0x5")][g("0x17")]() - v #v was created earlier in initialize
        g("0x5") = Date
        g("0x17") = now
        v = Timestamp in milliseconds e.g. 1596580552126
        Return value s: 725321

        u = 0;
                try {
                    u = window.screen[g("0x2e")] * window[g("0x19")][g("0xa")]
        g("0x2e") = width
        g("0x19") = screen
        g("0xa") = height
        Return value u: 2073600

        var l = +g("0xe");
        l = 1024

        try {
                    [][g("0x0")][g("0x2b")](window[g("0x1c")][g("0x12")], function(e) {
                        var t = e[g("0x31")];
                        t === g("0x22") && (l += 1),
                        t === g("0x2c") && (l += 2),
                        t === g("0x7") && (l += 4),
                        t === g("0xb") && (l += 8),
                        t === g("0x2") && (l += 16),
                        "Java Appvar Plug-in" === t && (l += 32),
                        "Shockwave Flash" === t && (l += 64),
                        "Edge PDF Viewer" === t && (l += +g("0x11")),
                        t === g("0x1d") && (l += +g("0x2a"))
                    })
                }
        g("0x0") = forEach
        g("0x2b") = call
        g("0x1c") = navigator
        g("0x12") = plugins

        } catch (e) {}
                o && (r = g("0x2f"));
                o && (i = +g("0x14"));
                o && (a = +g("0x14"));
                o && (w = 42);
                o && (s = +g("0x8"));
                o && (u = 420 * +g("0xf"));
                o && (l = +g("0xe"));
                o && (b = 7);
                o && (k = 9);
                o && (_ = 0);

        e = "tom_heidel@web.de"
        o = undefined, r = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        a = 33
        i = 1
        a = 33
        s = 725321
        u = 2073600
        l = 1046
        b = 2
        k = 2
        _ = 5
        w = 1049
        y = "8"
        n = "0763ed7314c69015fd4a0dc16bbf4b90" #same as c in l.sign

        for (var d = [a, i, s, w, u, l, b, k].join("-"), c = _, p = n + y + d + r + e + t + d + n, h = window[g("0x29")](window[g("0x26")](p)), m = 8011470, f = 0; f < h[g("0x1")]; f += 1)
                    m = (m >> 1) + ((1 & m) << 23),
                    m += h[g("0x13")](f),
                    m &= 16777215;
                return y + ":" + d + ":" + m.toString(16) + ":" + c
            }

        d = "33-1-725321-1049-2073600-1046-2-2"
        c = 5
        p = "0763ed7314c69015fd4a0dc16bbf4b90833-1-725321-1049-2073600-1046-2-2Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36tom_heidel@web.deEXLwg5lHTO2dslU5EePe3xkw0m1h86Cd33-1-725321-1049-2073600-1046-2-20763ed7314c69015fd4a0dc16bbf4b90"

        g("0x29") = unescape
        g("0x26") = encodeURIComponent

        h = "0763ed7314c69015fd4a0dc16bbf4b90833-1-725321-1049-2073600-1046-2-2Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36tom_heidel@web.deEXLwg5lHTO2dslU5EePe3xkw0m1h86Cd33-1-725321-1049-2073600-1046-2-20763ed7314c69015fd4a0dc16bbf4b90"
        m = 8011470
        f = 0

        g("0x1") = length
        m = 4005735 #calculated m = (m >> 1) + ((1 & m) << 23)
        g("0x13") = charCodeAt
        m = 4005783 #calculated m += h[g("0x13")](f)
        .-.-.-. after all h.length iterations
        m = 245670

        Return value: "8:33-1-725321-1049-2073600-1046-2-2:3bfa6:5" #signature

        # user-agent string is processed in signature calculating
        # this probably means if a signature with user-agent A is given you cannot change it to B when logging in 

        '''

        login_form = {
            'client_id': self._CLIENT_ID,
            'recaptcha_pubkey': 'null',
            'recaptcha_response': 'null',
            'credentials': {
                    'identifier': username,
                    'password': password
                },
            'signature': '',#l.sign(username, self._CLIENT_ID, c='0763ed7314c69015fd4a0dc16bbf4b90'), #c is extracted from web_auth js around (reading upwards from) function api.callEndpoint("verifyIdentifier"
            'device_id': '00000-000000-000000-000000',
            'user_agent': self._USER_AGENT
        }

        '''
        login = self._call_api(
            'sessions.json', None,
            'Logging in', post_data=login_form)
        '''

    # signature generation
    def sign(self):#, username=_USERNAME, client_id=_CLIENT_ID, key=_KEY):
        zero = 0
        i = a = 1
        u = 0 #u is actually screenWidth * screenHeight for 1920*1080 = 2073600
        mU = 2073600
        l = 1024 #1046?
        timestamp = millis = int(round(time.time() * 1000))
        mTimestamp = timestamp - (timestamp - random.randint(50000, 850000)) #hacky timestamp difference
        uTimestamp = random.randint(50000, 850000)
        w = 42 #1049?
        b = k = 2 #25?
        underscore = 0 #4, 5?


        #d = '-'.join([str(mInt) for mInt in [a, i, s, w, u, l, b, k]])
        d = '-'.join([str(mInt) for mInt in [a, i, zero, w, u, l, b, k]])
        print(d)

        c = underscore

        n = _KEY = '0763ed7314c69015fd4a0dc16bbf4b90'
        y = '8' #some kind of version??
        r = _USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
        e = _USERNAME = "tom_heidel@web.de"
        t = _CLIENT_ID = 'EXLwg5lHTO2dslU5EePe3xkw0m1h86Cd'


        p = n + y + d + r + e + t + d + n

        h = p

        m = 8011470
        f = 0 

        for f in range(f, len(h)):
            m = (m >> 1) + ((1 & m) << 23)
            m += ord(h[f])
            m &= 16777215

        # c is not even needed
        out = str(y) + ':' + str(d) + ':' + format(m, 'x') + ':' + str(c)

        return out

    ###

    @classmethod
    def _resolv_url(cls, url):
        return SoundcloudIE._API_V2_BASE + 'resolve?url=' + url

    def _extract_info_dict(self, info, full_title=None, secret_token=None):
        track_id = compat_str(info['id'])
        title = info['title']

        format_urls = set()
        formats = []
        query = {'client_id': self._CLIENT_ID}
        if secret_token:
            query['secret_token'] = secret_token

        if info.get('downloadable') and info.get('has_downloads_left'):
            download_url = update_url_query(
                self._API_V2_BASE + 'tracks/' + track_id + '/download', query)
            redirect_url = (self._download_json(download_url, track_id, fatal=False) or {}).get('redirectUri')
            if redirect_url:
                urlh = self._request_webpage(
                    HEADRequest(redirect_url), track_id, fatal=False)
                if urlh:
                    format_url = urlh.geturl()
                    format_urls.add(format_url)
                    formats.append({
                        'format_id': 'download',
                        'ext': urlhandle_detect_ext(urlh) or 'mp3',
                        'filesize': int_or_none(urlh.headers.get('Content-Length')),
                        'url': format_url,
                        'preference': 10,
                    })

        def invalid_url(url):
            return not url or url in format_urls

        def add_format(f, protocol, is_preview=False):
            mobj = re.search(r'\.(?P<abr>\d+)\.(?P<ext>[0-9a-z]{3,4})(?=[/?])', stream_url)
            if mobj:
                for k, v in mobj.groupdict().items():
                    if not f.get(k):
                        f[k] = v
            format_id_list = []
            if protocol:
                format_id_list.append(protocol)
            ext = f.get('ext')
            if ext == 'aac':
                f['abr'] = '256'
            for k in ('ext', 'abr'):
                v = f.get(k)
                if v:
                    format_id_list.append(v)
            preview = is_preview or re.search(r'/(?:preview|playlist)/0/30/', f['url'])
            if preview:
                format_id_list.append('preview')
            abr = f.get('abr')
            if abr:
                f['abr'] = int(abr)
            if protocol == 'hls':
                protocol = 'm3u8' if ext == 'aac' else 'm3u8_native'
            else:
                protocol = 'http'
            f.update({
                'format_id': '_'.join(format_id_list),
                'protocol': protocol,
                'preference': -10 if preview else None,
            })
            formats.append(f)

        # New API
        transcodings = try_get(
            info, lambda x: x['media']['transcodings'], list) or []
        for t in transcodings:
            if not isinstance(t, dict):
                continue
            format_url = url_or_none(t.get('url'))
            if not format_url:
                continue
            stream = self._download_json(
                format_url, track_id, query=query, fatal=False)
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('url'))
            if invalid_url(stream_url):
                continue
            format_urls.add(stream_url)
            stream_format = t.get('format') or {}
            protocol = stream_format.get('protocol')
            if protocol != 'hls' and '/hls' in format_url:
                protocol = 'hls'
            ext = None
            preset = str_or_none(t.get('preset'))
            if preset:
                ext = preset.split('_')[0]
            if ext not in KNOWN_EXTENSIONS:
                ext = mimetype2ext(stream_format.get('mime_type'))
            add_format({
                'url': stream_url,
                'ext': ext,
            }, 'http' if protocol == 'progressive' else protocol,
                t.get('snipped') or '/preview/' in format_url)

        for f in formats:
            f['vcodec'] = 'none'

        if not formats and info.get('policy') == 'BLOCK':
            self.raise_geo_restricted()
        self._sort_formats(formats)

        user = info.get('user') or {}

        thumbnails = []
        artwork_url = info.get('artwork_url')
        thumbnail = artwork_url or user.get('avatar_url')
        if isinstance(thumbnail, compat_str):
            if re.search(self._IMAGE_REPL_RE, thumbnail):
                for image_id, size in self._ARTWORK_MAP.items():
                    i = {
                        'id': image_id,
                        'url': re.sub(self._IMAGE_REPL_RE, '-%s.jpg' % image_id, thumbnail),
                    }
                    if image_id == 'tiny' and not artwork_url:
                        size = 18
                    elif image_id == 'original':
                        i['preference'] = 10
                    if size:
                        i.update({
                            'width': size,
                            'height': size,
                        })
                    thumbnails.append(i)
            else:
                thumbnails = [{'url': thumbnail}]

        def extract_count(key):
            return int_or_none(info.get('%s_count' % key))

        return {
            'id': track_id,
            'uploader': user.get('username'),
            'uploader_id': str_or_none(user.get('id')) or user.get('permalink'),
            'uploader_url': user.get('permalink_url'),
            'timestamp': unified_timestamp(info.get('created_at')),
            'title': title,
            'description': info.get('description'),
            'thumbnails': thumbnails,
            'duration': float_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
            'view_count': extract_count('playback'),
            'like_count': extract_count('favoritings') or extract_count('likes'),
            'comment_count': extract_count('comment'),
            'repost_count': extract_count('reposts'),
            'genre': info.get('genre'),
            'formats': formats
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        track_id = mobj.group('track_id')

        query = {}
        if track_id:
            info_json_url = self._API_V2_BASE + 'tracks/' + track_id
            full_title = track_id
            token = mobj.group('secret_token')
            if token:
                query['secret_token'] = token
        else:
            full_title = resolve_title = '%s/%s' % mobj.group('uploader', 'title')
            token = mobj.group('token')
            if token:
                resolve_title += '/%s' % token
            info_json_url = self._resolv_url(self._BASE_URL + resolve_title)

        info = self._download_json(
            info_json_url, full_title, 'Downloading info JSON', query=query)

        return self._extract_info_dict(info, full_title, token)


class SoundcloudPlaylistBaseIE(SoundcloudIE):
    def _extract_set(self, playlist, token=None):
        playlist_id = compat_str(playlist['id'])
        tracks = playlist.get('tracks') or []
        if not all([t.get('permalink_url') for t in tracks]) and token:
            tracks = self._download_json(
                self._API_V2_BASE + 'tracks', playlist_id,
                'Downloading tracks', query={
                    'ids': ','.join([compat_str(t['id']) for t in tracks]),
                    'playlistId': playlist_id,
                    'playlistSecretToken': token,
                })
        entries = []
        for track in tracks:
            track_id = str_or_none(track.get('id'))
            url = track.get('permalink_url')
            if not url:
                if not track_id:
                    continue
                url = self._API_V2_BASE + 'tracks/' + track_id
                if token:
                    url += '?secret_token=' + token
            entries.append(self.url_result(
                url, SoundcloudIE.ie_key(), track_id))
        return self.playlist_result(
            entries, playlist_id,
            playlist.get('title'),
            playlist.get('description'))


class SoundcloudSetIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?soundcloud\.com/(?P<uploader>[\w\d-]+)/sets/(?P<slug_title>[\w\d-]+)(?:/(?P<token>[^?/]+))?'
    IE_NAME = 'soundcloud:set'
    _TESTS = [{
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep',
        'info_dict': {
            'id': '2284613',
            'title': 'The Royal Concept EP',
            'description': 'md5:71d07087c7a449e8941a70a29e34671e',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep/token',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        full_title = '%s/sets/%s' % mobj.group('uploader', 'slug_title')
        token = mobj.group('token')
        if token:
            full_title += '/' + token

        info = self._download_json(self._resolv_url(
            self._BASE_URL + full_title), full_title)

        if 'errors' in info:
            msgs = (compat_str(err['error_message']) for err in info['errors'])
            raise ExtractorError('unable to download video webpage: %s' % ','.join(msgs))

        return self._extract_set(info, token)


class SoundcloudPagedPlaylistBaseIE(SoundcloudIE):
    def _extract_playlist(self, base_url, playlist_id, playlist_title):
        COMMON_QUERY = {
            'limit': 80000,
            'linked_partitioning': '1',
        }

        query = COMMON_QUERY.copy()
        query['offset'] = 0

        next_href = base_url

        entries = []
        for i in itertools.count():
            response = self._download_json(
                next_href, playlist_id,
                'Downloading track page %s' % (i + 1), query=query)

            collection = response['collection']

            if not isinstance(collection, list):
                collection = []

            # Empty collection may be returned, in this case we proceed
            # straight to next_href

            def resolve_entry(candidates):
                for cand in candidates:
                    if not isinstance(cand, dict):
                        continue
                    permalink_url = url_or_none(cand.get('permalink_url'))
                    if not permalink_url:
                        continue
                    return self.url_result(
                        permalink_url,
                        SoundcloudIE.ie_key() if SoundcloudIE.suitable(permalink_url) else None,
                        str_or_none(cand.get('id')), cand.get('title'))

            for e in collection:
                entry = resolve_entry((e, e.get('track'), e.get('playlist')))
                if entry:
                    entries.append(entry)

            next_href = response.get('next_href')
            if not next_href:
                break

            next_href = response['next_href']
            parsed_next_href = compat_urlparse.urlparse(next_href)
            query = compat_urlparse.parse_qs(parsed_next_href.query)
            query.update(COMMON_QUERY)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': playlist_title,
            'entries': entries,
        }


class SoundcloudUserIE(SoundcloudPagedPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:(?:www|m)\.)?soundcloud\.com/
                            (?P<user>[^/]+)
                            (?:/
                                (?P<rsrc>tracks|albums|sets|reposts|likes|spotlight)
                            )?
                            /?(?:[?#].*)?$
                    '''
    IE_NAME = 'soundcloud:user'
    _TESTS = [{
        'url': 'https://soundcloud.com/soft-cell-official',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (All)',
        },
        'playlist_mincount': 28,
    }, {
        'url': 'https://soundcloud.com/soft-cell-official/tracks',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (Tracks)',
        },
        'playlist_mincount': 27,
    }, {
        'url': 'https://soundcloud.com/soft-cell-official/albums',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (Albums)',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://soundcloud.com/jcv246/sets',
        'info_dict': {
            'id': '12982173',
            'title': 'Jordi / cv (Sets)',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://soundcloud.com/jcv246/reposts',
        'info_dict': {
            'id': '12982173',
            'title': 'Jordi / cv (Reposts)',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://soundcloud.com/clalberg/likes',
        'info_dict': {
            'id': '11817582',
            'title': 'clalberg (Likes)',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://soundcloud.com/grynpyret/spotlight',
        'info_dict': {
            'id': '7098329',
            'title': 'Grynpyret (Spotlight)',
        },
        'playlist_mincount': 1,
    }]

    _BASE_URL_MAP = {
        'all': 'stream/users/%s',
        'tracks': 'users/%s/tracks',
        'albums': 'users/%s/albums',
        'sets': 'users/%s/playlists',
        'reposts': 'stream/users/%s/reposts',
        'likes': 'users/%s/likes',
        'spotlight': 'users/%s/spotlight',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')

        user = self._download_json(
            self._resolv_url(self._BASE_URL + uploader),
            uploader, 'Downloading user info')

        resource = mobj.group('rsrc') or 'all'

        return self._extract_playlist(
            self._API_V2_BASE + self._BASE_URL_MAP[resource] % user['id'],
            str_or_none(user.get('id')),
            '%s (%s)' % (user['username'], resource.capitalize()))


class SoundcloudTrackStationIE(SoundcloudPagedPlaylistBaseIE):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?soundcloud\.com/stations/track/[^/]+/(?P<id>[^/?#&]+)'
    IE_NAME = 'soundcloud:trackstation'
    _TESTS = [{
        'url': 'https://soundcloud.com/stations/track/officialsundial/your-text',
        'info_dict': {
            'id': '286017854',
            'title': 'Track station: your text',
        },
        'playlist_mincount': 47,
    }]

    def _real_extract(self, url):
        track_name = self._match_id(url)

        track = self._download_json(self._resolv_url(url), track_name)
        track_id = self._search_regex(
            r'soundcloud:track-stations:(\d+)', track['id'], 'track id')

        return self._extract_playlist(
            self._API_V2_BASE + 'stations/%s/tracks' % track['id'],
            track_id, 'Track station: %s' % track['title'])


class SoundcloudPlaylistIE(SoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://api(?:-v2)?\.soundcloud\.com/playlists/(?P<id>[0-9]+)(?:/?\?secret_token=(?P<token>[^&]+?))?$'
    IE_NAME = 'soundcloud:playlist'
    _TESTS = [{
        'url': 'https://api.soundcloud.com/playlists/4110309',
        'info_dict': {
            'id': '4110309',
            'title': 'TILT Brass - Bowery Poetry Club, August \'03 [Non-Site SCR 02]',
            'description': 're:.*?TILT Brass - Bowery Poetry Club',
        },
        'playlist_count': 6,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

        query = {}
        token = mobj.group('token')
        if token:
            query['secret_token'] = token

        data = self._download_json(
            self._API_V2_BASE + 'playlists/' + playlist_id,
            playlist_id, 'Downloading playlist', query=query)

        return self._extract_set(data, token)


class SoundcloudSearchIE(SearchInfoExtractor, SoundcloudIE):
    IE_NAME = 'soundcloud:search'
    IE_DESC = 'Soundcloud search'
    _MAX_RESULTS = float('inf')
    _TESTS = [{
        'url': 'scsearch15:post-avant jazzcore',
        'info_dict': {
            'title': 'post-avant jazzcore',
        },
        'playlist_count': 15,
    }]

    _SEARCH_KEY = 'scsearch'
    _MAX_RESULTS_PER_PAGE = 200
    _DEFAULT_RESULTS_PER_PAGE = 50

    def _get_collection(self, endpoint, collection_id, **query):
        limit = min(
            query.get('limit', self._DEFAULT_RESULTS_PER_PAGE),
            self._MAX_RESULTS_PER_PAGE)
        query.update({
            'limit': limit,
            'linked_partitioning': 1,
            'offset': 0,
        })
        next_url = update_url_query(self._API_V2_BASE + endpoint, query)

        collected_results = 0

        for i in itertools.count(1):
            response = self._download_json(
                next_url, collection_id, 'Downloading page {0}'.format(i),
                'Unable to download API page')

            collection = response.get('collection', [])
            if not collection:
                break

            collection = list(filter(bool, collection))
            collected_results += len(collection)

            for item in collection:
                yield self.url_result(item['uri'], SoundcloudIE.ie_key())

            if not collection or collected_results >= limit:
                break

            next_url = response.get('next_href')
            if not next_url:
                break

    def _get_n_results(self, query, n):
        tracks = self._get_collection('search/tracks', query, limit=n, q=query)
        return self.playlist_result(tracks, playlist_title=query)
