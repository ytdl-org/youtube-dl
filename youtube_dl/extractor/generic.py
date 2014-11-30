# encoding: utf-8

from __future__ import unicode_literals

import os
import re

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..compat import (
    compat_urllib_parse,
    compat_urlparse,
    compat_xml_parse_error,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    HEADRequest,
    orderedSet,
    parse_xml,
    smuggle_url,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    url_basename,
)
from .brightcove import BrightcoveIE
from .ooyala import OoyalaIE
from .rutv import RUTVIE
from .smotri import SmotriIE
from .condenast import CondeNastIE


class GenericIE(InfoExtractor):
    IE_DESC = 'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = 'generic'
    _TESTS = [
        {
            'url': 'http://www.hodiho.fr/2013/02/regis-plante-sa-jeep.html',
            'md5': '85b90ccc9d73b4acd9138d3af4c27f89',
            'info_dict': {
                'id': '13601338388002',
                'ext': 'mp4',
                'uploader': 'www.hodiho.fr',
                'title': 'R\u00e9gis plante sa Jeep',
            }
        },
        # bandcamp page with custom domain
        {
            'add_ie': ['Bandcamp'],
            'url': 'http://bronyrock.com/track/the-pony-mash',
            'info_dict': {
                'id': '3235767654',
                'ext': 'mp3',
                'title': 'The Pony Mash',
                'uploader': 'M_Pallante',
            },
            'skip': 'There is a limit of 200 free downloads / month for the test song',
        },
        # embedded brightcove video
        # it also tests brightcove videos that need to set the 'Referer' in the
        # http requests
        {
            'add_ie': ['Brightcove'],
            'url': 'http://www.bfmtv.com/video/bfmbusiness/cours-bourse/cours-bourse-l-analyse-technique-154522/',
            'info_dict': {
                'id': '2765128793001',
                'ext': 'mp4',
                'title': 'Le cours de bourse : l’analyse technique',
                'description': 'md5:7e9ad046e968cb2d1114004aba466fd9',
                'uploader': 'BFM BUSINESS',
            },
            'params': {
                'skip_download': True,
            },
        },
        {
            # https://github.com/rg3/youtube-dl/issues/2253
            'url': 'http://bcove.me/i6nfkrc3',
            'md5': '0ba9446db037002366bab3b3eb30c88c',
            'info_dict': {
                'id': '3101154703001',
                'ext': 'mp4',
                'title': 'Still no power',
                'uploader': 'thestar.com',
                'description': 'Mississauga resident David Farmer is still out of power as a result of the ice storm a month ago. To keep the house warm, Farmer cuts wood from his property for a wood burning stove downstairs.',
            },
            'add_ie': ['Brightcove'],
        },
        {
            'url': 'http://www.championat.com/video/football/v/87/87499.html',
            'md5': 'fb973ecf6e4a78a67453647444222983',
            'info_dict': {
                'id': '3414141473001',
                'ext': 'mp4',
                'title': 'Видео. Удаление Дзагоева (ЦСКА)',
                'description': 'Онлайн-трансляция матча ЦСКА - "Волга"',
                'uploader': 'Championat',
            },
        },
        {
            # https://github.com/rg3/youtube-dl/issues/3541
            'add_ie': ['Brightcove'],
            'url': 'http://www.kijk.nl/sbs6/leermijvrouwenkennen/videos/jqMiXKAYan2S/aflevering-1',
            'info_dict': {
                'id': '3866516442001',
                'ext': 'mp4',
                'title': 'Leer mij vrouwen kennen: Aflevering 1',
                'description': 'Leer mij vrouwen kennen: Aflevering 1',
                'uploader': 'SBS Broadcasting',
            },
            'skip': 'Restricted to Netherlands',
            'params': {
                'skip_download': True,  # m3u8 download
            },
        },
        # Direct link to a video
        {
            'url': 'http://media.w3.org/2010/05/sintel/trailer.mp4',
            'md5': '67d406c2bcb6af27fa886f31aa934bbe',
            'info_dict': {
                'id': 'trailer',
                'ext': 'mp4',
                'title': 'trailer',
                'upload_date': '20100513',
            }
        },
        # ooyala video
        {
            'url': 'http://www.rollingstone.com/music/videos/norwegian-dj-cashmere-cat-goes-spartan-on-with-me-premiere-20131219',
            'md5': '5644c6ca5d5782c1d0d350dad9bd840c',
            'info_dict': {
                'id': 'BwY2RxaTrTkslxOfcan0UCf0YqyvWysJ',
                'ext': 'mp4',
                'title': '2cc213299525360.mov',  # that's what we get
            },
        },
        # google redirect
        {
            'url': 'http://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&ved=0CCUQtwIwAA&url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DcmQHVoWB5FY&ei=F-sNU-LLCaXk4QT52ICQBQ&usg=AFQjCNEw4hL29zgOohLXvpJ-Bdh2bils1Q&bvm=bv.61965928,d.bGE',
            'info_dict': {
                'id': 'cmQHVoWB5FY',
                'ext': 'mp4',
                'upload_date': '20130224',
                'uploader_id': 'TheVerge',
                'description': 'Chris Ziegler takes a look at the Alcatel OneTouch Fire and the ZTE Open; two of the first Firefox OS handsets to be officially announced.',
                'uploader': 'The Verge',
                'title': 'First Firefox OS phones side-by-side',
            },
            'params': {
                'skip_download': False,
            }
        },
        # embed.ly video
        {
            'url': 'http://www.tested.com/science/weird/460206-tested-grinding-coffee-2000-frames-second/',
            'info_dict': {
                'id': '9ODmcdjQcHQ',
                'ext': 'mp4',
                'title': 'Tested: Grinding Coffee at 2000 Frames Per Second',
                'upload_date': '20140225',
                'description': 'md5:06a40fbf30b220468f1e0957c0f558ff',
                'uploader': 'Tested',
                'uploader_id': 'testedcom',
            },
            # No need to test YoutubeIE here
            'params': {
                'skip_download': True,
            },
        },
        # funnyordie embed
        {
            'url': 'http://www.theguardian.com/world/2014/mar/11/obama-zach-galifianakis-between-two-ferns',
            'info_dict': {
                'id': '18e820ec3f',
                'ext': 'mp4',
                'title': 'Between Two Ferns with Zach Galifianakis: President Barack Obama',
                'description': 'Episode 18: President Barack Obama sits down with Zach Galifianakis for his most memorable interview yet.',
            },
        },
        # RUTV embed
        {
            'url': 'http://www.rg.ru/2014/03/15/reg-dfo/anklav-anons.html',
            'info_dict': {
                'id': '776940',
                'ext': 'mp4',
                'title': 'Охотское море стало целиком российским',
                'description': 'md5:5ed62483b14663e2a95ebbe115eb8f43',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        # Embedded TED video
        {
            'url': 'http://en.support.wordpress.com/videos/ted-talks/',
            'md5': '65fdff94098e4a607385a60c5177c638',
            'info_dict': {
                'id': '1969',
                'ext': 'mp4',
                'title': 'Hidden miracles of the natural world',
                'uploader': 'Louie Schwartzberg',
                'description': 'md5:8145d19d320ff3e52f28401f4c4283b9',
            }
        },
        # Embeded Ustream video
        {
            'url': 'http://www.american.edu/spa/pti/nsa-privacy-janus-2014.cfm',
            'md5': '27b99cdb639c9b12a79bca876a073417',
            'info_dict': {
                'id': '45734260',
                'ext': 'flv',
                'uploader': 'AU SPA:  The NSA and Privacy',
                'title': 'NSA and Privacy Forum Debate featuring General Hayden and Barton Gellman'
            }
        },
        # nowvideo embed hidden behind percent encoding
        {
            'url': 'http://www.waoanime.tv/the-super-dimension-fortress-macross-episode-1/',
            'md5': '2baf4ddd70f697d94b1c18cf796d5107',
            'info_dict': {
                'id': '06e53103ca9aa',
                'ext': 'flv',
                'title': 'Macross Episode 001  Watch Macross Episode 001 onl',
                'description': 'No description',
            },
        },
        # arte embed
        {
            'url': 'http://www.tv-replay.fr/redirection/20-03-14/x-enius-arte-10753389.html',
            'md5': '7653032cbb25bf6c80d80f217055fa43',
            'info_dict': {
                'id': '048195-004_PLUS7-F',
                'ext': 'flv',
                'title': 'X:enius',
                'description': 'md5:d5fdf32ef6613cdbfd516ae658abf168',
                'upload_date': '20140320',
            },
            'params': {
                'skip_download': 'Requires rtmpdump'
            }
        },
        # Condé Nast embed
        {
            'url': 'http://www.wired.com/2014/04/honda-asimo/',
            'md5': 'ba0dfe966fa007657bd1443ee672db0f',
            'info_dict': {
                'id': '53501be369702d3275860000',
                'ext': 'mp4',
                'title': 'Honda’s  New Asimo Robot Is More Human Than Ever',
            }
        },
        # Dailymotion embed
        {
            'url': 'http://www.spi0n.com/zap-spi0n-com-n216/',
            'md5': '441aeeb82eb72c422c7f14ec533999cd',
            'info_dict': {
                'id': 'k2mm4bCdJ6CQ2i7c8o2',
                'ext': 'mp4',
                'title': 'Le Zap de Spi0n n°216 - Zapping du Web',
                'uploader': 'Spi0n',
            },
            'add_ie': ['Dailymotion'],
        },
        # YouTube embed
        {
            'url': 'http://www.badzine.de/ansicht/datum/2014/06/09/so-funktioniert-die-neue-englische-badminton-liga.html',
            'info_dict': {
                'id': 'FXRb4ykk4S0',
                'ext': 'mp4',
                'title': 'The NBL Auction 2014',
                'uploader': 'BADMINTON England',
                'uploader_id': 'BADMINTONEvents',
                'upload_date': '20140603',
                'description': 'md5:9ef128a69f1e262a700ed83edb163a73',
            },
            'add_ie': ['Youtube'],
            'params': {
                'skip_download': True,
            }
        },
        # MTVSercices embed
        {
            'url': 'http://www.gametrailers.com/news-post/76093/north-america-europe-is-getting-that-mario-kart-8-mercedes-dlc-too',
            'md5': '35727f82f58c76d996fc188f9755b0d5',
            'info_dict': {
                'id': '0306a69b-8adf-4fb5-aace-75f8e8cbfca9',
                'ext': 'mp4',
                'title': 'Review',
                'description': 'Mario\'s life in the fast lane has never looked so good.',
            },
        },
        # YouTube embed via <data-embed-url="">
        {
            'url': 'https://play.google.com/store/apps/details?id=com.gameloft.android.ANMP.GloftA8HM',
            'info_dict': {
                'id': '4vAffPZIT44',
                'ext': 'mp4',
                'title': 'Asphalt 8: Airborne - Update - Welcome to Dubai!',
                'uploader': 'Gameloft',
                'uploader_id': 'gameloft',
                'upload_date': '20140828',
                'description': 'md5:c80da9ed3d83ae6d1876c834de03e1c4',
            },
            'params': {
                'skip_download': True,
            }
        },
        # Camtasia studio
        {
            'url': 'http://www.ll.mit.edu/workshops/education/videocourses/antennas/lecture1/video/',
            'playlist': [{
                'md5': '0c5e352edabf715d762b0ad4e6d9ee67',
                'info_dict': {
                    'id': 'Fenn-AA_PA_Radar_Course_Lecture_1c_Final',
                    'title': 'Fenn-AA_PA_Radar_Course_Lecture_1c_Final - video1',
                    'ext': 'flv',
                    'duration': 2235.90,
                }
            }, {
                'md5': '10e4bb3aaca9fd630e273ff92d9f3c63',
                'info_dict': {
                    'id': 'Fenn-AA_PA_Radar_Course_Lecture_1c_Final_PIP',
                    'title': 'Fenn-AA_PA_Radar_Course_Lecture_1c_Final - pip',
                    'ext': 'flv',
                    'duration': 2235.93,
                }
            }],
            'info_dict': {
                'title': 'Fenn-AA_PA_Radar_Course_Lecture_1c_Final',
            }
        },
        # Flowplayer
        {
            'url': 'http://www.handjobhub.com/video/busty-blonde-siri-tit-fuck-while-wank-6313.html',
            'md5': '9d65602bf31c6e20014319c7d07fba27',
            'info_dict': {
                'id': '5123ea6d5e5a7',
                'ext': 'mp4',
                'age_limit': 18,
                'uploader': 'www.handjobhub.com',
                'title': 'Busty Blonde Siri Tit Fuck While Wank at HandjobHub.com',
            }
        },
        # RSS feed
        {
            'url': 'http://phihag.de/2014/youtube-dl/rss2.xml',
            'info_dict': {
                'id': 'http://phihag.de/2014/youtube-dl/rss2.xml',
                'title': 'Zero Punctuation',
                'description': 're:'
            },
            'playlist_mincount': 11,
        },
        # Multiple brightcove videos
        # https://github.com/rg3/youtube-dl/issues/2283
        {
            'url': 'http://www.newyorker.com/online/blogs/newsdesk/2014/01/always-never-nuclear-command-and-control.html',
            'info_dict': {
                'id': 'always-never',
                'title': 'Always / Never - The New Yorker',
            },
            'playlist_count': 3,
            'params': {
                'extract_flat': False,
                'skip_download': True,
            }
        },
        # MLB embed
        {
            'url': 'http://umpire-empire.com/index.php/topic/58125-laz-decides-no-thats-low/',
            'md5': '96f09a37e44da40dd083e12d9a683327',
            'info_dict': {
                'id': '33322633',
                'ext': 'mp4',
                'title': 'Ump changes call to ball',
                'description': 'md5:71c11215384298a172a6dcb4c2e20685',
                'duration': 48,
                'timestamp': 1401537900,
                'upload_date': '20140531',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
        },
        # Wistia embed
        {
            'url': 'http://education-portal.com/academy/lesson/north-american-exploration-failed-colonies-of-spain-france-england.html#lesson',
            'md5': '8788b683c777a5cf25621eaf286d0c23',
            'info_dict': {
                'id': '1cfaf6b7ea',
                'ext': 'mov',
                'title': 'md5:51364a8d3d009997ba99656004b5e20d',
                'duration': 643.0,
                'filesize': 182808282,
                'uploader': 'education-portal.com',
            },
        },
        {
            'url': 'http://thoughtworks.wistia.com/medias/uxjb0lwrcz',
            'md5': 'baf49c2baa8a7de5f3fc145a8506dcd4',
            'info_dict': {
                'id': 'uxjb0lwrcz',
                'ext': 'mp4',
                'title': 'Conversation about Hexagonal Rails Part 1 - ThoughtWorks',
                'duration': 1715.0,
                'uploader': 'thoughtworks.wistia.com',
            },
        },
        # Direct download with broken HEAD
        {
            'url': 'http://ai-radio.org:8000/radio.opus',
            'info_dict': {
                'id': 'radio',
                'ext': 'opus',
                'title': 'radio',
            },
            'params': {
                'skip_download': True,  # infinite live stream
            },
            'expected_warnings': [
                r'501.*Not Implemented'
            ],
        },
        # Soundcloud embed
        {
            'url': 'http://nakedsecurity.sophos.com/2014/10/29/sscc-171-are-you-sure-that-1234-is-a-bad-password-podcast/',
            'info_dict': {
                'id': '174391317',
                'ext': 'mp3',
                'description': 'md5:ff867d6b555488ad3c52572bb33d432c',
                'uploader': 'Sophos Security',
                'title': 'Chet Chat 171 - Oct 29, 2014',
                'upload_date': '20141029',
            }
        },
        # Livestream embed
        {
            'url': 'http://www.esa.int/Our_Activities/Space_Science/Rosetta/Philae_comet_touch-down_webcast',
            'info_dict': {
                'id': '67864563',
                'ext': 'flv',
                'upload_date': '20141112',
                'title': 'Rosetta #CometLanding webcast HL 10',
            }
        },
        # LazyYT
        {
            'url': 'http://discourse.ubuntu.com/t/unity-8-desktop-mode-windows-on-mir/1986',
            'info_dict': {
                'title': 'Unity 8 desktop-mode windows on Mir! - Ubuntu Discourse',
            },
            'playlist_mincount': 2,
        },
        # Direct link with incorrect MIME type
        {
            'url': 'http://ftp.nluug.nl/video/nluug/2014-11-20_nj14/zaal-2/5_Lennart_Poettering_-_Systemd.webm',
            'md5': '4ccbebe5f36706d85221f204d7eb5913',
            'info_dict': {
                'url': 'http://ftp.nluug.nl/video/nluug/2014-11-20_nj14/zaal-2/5_Lennart_Poettering_-_Systemd.webm',
                'id': '5_Lennart_Poettering_-_Systemd',
                'ext': 'webm',
                'title': '5_Lennart_Poettering_-_Systemd',
                'upload_date': '20141120',
            },
            'expected_warnings': [
                'URL could be a direct video link, returning it as such.'
            ]
        }

    ]

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen('[redirect] Following redirect to %s' % new_url)

    def _extract_rss(self, url, video_id, doc):
        playlist_title = doc.find('./channel/title').text
        playlist_desc_el = doc.find('./channel/description')
        playlist_desc = None if playlist_desc_el is None else playlist_desc_el.text

        entries = [{
            '_type': 'url',
            'url': e.find('link').text,
            'title': e.find('title').text,
        } for e in doc.findall('./channel/item')]

        return {
            '_type': 'playlist',
            'id': url,
            'title': playlist_title,
            'description': playlist_desc,
            'entries': entries,
        }

    def _extract_camtasia(self, url, video_id, webpage):
        """ Returns None if no camtasia video can be found. """

        camtasia_cfg = self._search_regex(
            r'fo\.addVariable\(\s*"csConfigFile",\s*"([^"]+)"\s*\);',
            webpage, 'camtasia configuration file', default=None)
        if camtasia_cfg is None:
            return None

        title = self._html_search_meta('DC.title', webpage, fatal=True)

        camtasia_url = compat_urlparse.urljoin(url, camtasia_cfg)
        camtasia_cfg = self._download_xml(
            camtasia_url, video_id,
            note='Downloading camtasia configuration',
            errnote='Failed to download camtasia configuration')
        fileset_node = camtasia_cfg.find('./playlist/array/fileset')

        entries = []
        for n in fileset_node.getchildren():
            url_n = n.find('./uri')
            if url_n is None:
                continue

            entries.append({
                'id': os.path.splitext(url_n.text.rpartition('/')[2])[0],
                'title': '%s - %s' % (title, n.tag),
                'url': compat_urlparse.urljoin(url, url_n.text),
                'duration': float_or_none(n.find('./duration').text),
            })

        return {
            '_type': 'playlist',
            'entries': entries,
            'title': title,
        }

    def _real_extract(self, url):
        if url.startswith('//'):
            return {
                '_type': 'url',
                'url': self.http_scheme() + url,
            }

        parsed_url = compat_urlparse.urlparse(url)
        if not parsed_url.scheme:
            default_search = self._downloader.params.get('default_search')
            if default_search is None:
                default_search = 'fixup_error'

            if default_search in ('auto', 'auto_warning', 'fixup_error'):
                if '/' in url:
                    self._downloader.report_warning('The url doesn\'t specify the protocol, trying with http')
                    return self.url_result('http://' + url)
                elif default_search != 'fixup_error':
                    if default_search == 'auto_warning':
                        if re.match(r'^(?:url|URL)$', url):
                            raise ExtractorError(
                                'Invalid URL:  %r . Call youtube-dl like this:  youtube-dl -v "https://www.youtube.com/watch?v=BaW_jenozKc"  ' % url,
                                expected=True)
                        else:
                            self._downloader.report_warning(
                                'Falling back to youtube search for  %s . Set --default-search "auto" to suppress this warning.' % url)
                    return self.url_result('ytsearch:' + url)

            if default_search in ('error', 'fixup_error'):
                raise ExtractorError(
                    '%r is not a valid URL. '
                    'Set --default-search "ytsearch" (or run  youtube-dl "ytsearch:%s" ) to search YouTube'
                    % (url, url), expected=True)
            else:
                if ':' not in default_search:
                    default_search += ':'
                return self.url_result(default_search + url)

        url, smuggled_data = unsmuggle_url(url)
        force_videoid = None
        is_intentional = smuggled_data and smuggled_data.get('to_generic')
        if smuggled_data and 'force_videoid' in smuggled_data:
            force_videoid = smuggled_data['force_videoid']
            video_id = force_videoid
        else:
            video_id = os.path.splitext(url.rstrip('/').split('/')[-1])[0]

        self.to_screen('%s: Requesting header' % video_id)

        head_req = HEADRequest(url)
        head_response = self._request_webpage(
            head_req, video_id,
            note=False, errnote='Could not send HEAD request to %s' % url,
            fatal=False)

        if head_response is not False:
            # Check for redirect
            new_url = head_response.geturl()
            if url != new_url:
                self.report_following_redirect(new_url)
                if force_videoid:
                    new_url = smuggle_url(
                        new_url, {'force_videoid': force_videoid})
                return self.url_result(new_url)

        full_response = None
        if head_response is False:
            full_response = self._request_webpage(url, video_id)
            head_response = full_response

        # Check for direct link to a video
        content_type = head_response.headers.get('Content-Type', '')
        m = re.match(r'^(?P<type>audio|video|application(?=/ogg$))/(?P<format_id>.+)$', content_type)
        if m:
            upload_date = unified_strdate(
                head_response.headers.get('Last-Modified'))
            return {
                'id': video_id,
                'title': os.path.splitext(url_basename(url))[0],
                'direct': True,
                'formats': [{
                    'format_id': m.group('format_id'),
                    'url': url,
                    'vcodec': 'none' if m.group('type') == 'audio' else None
                }],
                'upload_date': upload_date,
            }

        if not self._downloader.params.get('test', False) and not is_intentional:
            self._downloader.report_warning('Falling back on generic information extractor.')

        if not full_response:
            full_response = self._request_webpage(url, video_id)

        # Maybe it's a direct link to a video?
        # Be careful not to download the whole thing!
        first_bytes = full_response.read(512)
        if not re.match(r'^\s*<', first_bytes.decode('utf-8', 'replace')):
            self._downloader.report_warning(
                'URL could be a direct video link, returning it as such.')
            upload_date = unified_strdate(
                head_response.headers.get('Last-Modified'))
            return {
                'id': video_id,
                'title': os.path.splitext(url_basename(url))[0],
                'direct': True,
                'url': url,
                'upload_date': upload_date,
            }

        webpage = self._webpage_read_content(
            full_response, url, video_id, prefix=first_bytes)

        self.report_extraction(video_id)

        # Is it an RSS feed?
        try:
            doc = parse_xml(webpage)
            if doc.tag == 'rss':
                return self._extract_rss(url, video_id, doc)
        except compat_xml_parse_error:
            pass

        # Is it a Camtasia project?
        camtasia_res = self._extract_camtasia(url, video_id, webpage)
        if camtasia_res is not None:
            return camtasia_res

        # Sometimes embedded video player is hidden behind percent encoding
        # (e.g. https://github.com/rg3/youtube-dl/issues/2448)
        # Unescaping the whole page allows to handle those cases in a generic way
        webpage = compat_urllib_parse.unquote(webpage)

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._html_search_regex(
            r'(?s)<title>(.*?)</title>', webpage, 'video title',
            default='video')

        # Try to detect age limit automatically
        age_limit = self._rta_search(webpage)
        # And then there are the jokers who advertise that they use RTA,
        # but actually don't.
        AGE_LIMIT_MARKERS = [
            r'Proudly Labeled <a href="http://www.rtalabel.org/" title="Restricted to Adults">RTA</a>',
        ]
        if any(re.search(marker, webpage) for marker in AGE_LIMIT_MARKERS):
            age_limit = 18

        # video uploader is domain name
        video_uploader = self._search_regex(
            r'^(?:https?://)?([^/]*)/.*', url, 'video uploader')

        # Helper method
        def _playlist_from_matches(matches, getter, ie=None):
            urlrs = orderedSet(
                self.url_result(self._proto_relative_url(getter(m)), ie)
                for m in matches)
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for BrightCove:
        bc_urls = BrightcoveIE._extract_brightcove_urls(webpage)
        if bc_urls:
            self.to_screen('Brightcove video detected.')
            entries = [{
                '_type': 'url',
                'url': smuggle_url(bc_url, {'Referer': url}),
                'ie_key': 'Brightcove'
            } for bc_url in bc_urls]

            return {
                '_type': 'playlist',
                'title': video_title,
                'id': video_id,
                'entries': entries,
            }

        # Look for embedded (iframe) Vimeo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//player\.vimeo\.com/video/.+?)\1', webpage)
        if mobj:
            player_url = unescapeHTML(mobj.group('url'))
            surl = smuggle_url(player_url, {'Referer': url})
            return self.url_result(surl)

        # Look for embedded (swf embed) Vimeo player
        mobj = re.search(
            r'<embed[^>]+?src="((?:https?:)?//(?:www\.)?vimeo\.com/moogaloop\.swf.+?)"', webpage)
        if mobj:
            return self.url_result(mobj.group(1))

        # Look for embedded YouTube player
        matches = re.findall(r'''(?x)
            (?:
                <iframe[^>]+?src=|
                data-video-url=|
                <embed[^>]+?src=|
                embedSWF\(?:\s*|
                new\s+SWFObject\(
            )
            (["\'])
                (?P<url>(?:https?:)?//(?:www\.)?youtube(?:-nocookie)?\.com/
                (?:embed|v|p)/.+?)
            \1''', webpage)
        if matches:
            return _playlist_from_matches(
                matches, lambda m: unescapeHTML(m[1]))

        # Look for lazyYT YouTube embed
        matches = re.findall(
            r'class="lazyYT" data-youtube-id="([^"]+)"', webpage)
        if matches:
            return _playlist_from_matches(matches, lambda m: unescapeHTML(m))

        # Look for embedded Dailymotion player
        matches = re.findall(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?dailymotion\.com/embed/video/.+?)\1', webpage)
        if matches:
            return _playlist_from_matches(
                matches, lambda m: unescapeHTML(m[1]))

        # Look for embedded Dailymotion playlist player (#3822)
        m = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?dailymotion\.[a-z]{2,3}/widget/jukebox\?.+?)\1', webpage)
        if m:
            playlists = re.findall(
                r'list\[\]=/playlist/([^/]+)/', unescapeHTML(m.group('url')))
            if playlists:
                return _playlist_from_matches(
                    playlists, lambda p: '//dailymotion.com/playlist/%s' % p)

        # Look for embedded Wistia player
        match = re.search(
            r'<(?:meta[^>]+?content|iframe[^>]+?src)=(["\'])(?P<url>(?:https?:)?//(?:fast\.)?wistia\.net/embed/iframe/.+?)\1', webpage)
        if match:
            embed_url = self._proto_relative_url(
                unescapeHTML(match.group('url')))
            return {
                '_type': 'url_transparent',
                'url': embed_url,
                'ie_key': 'Wistia',
                'uploader': video_uploader,
                'title': video_title,
                'id': video_id,
            }

        match = re.search(r'(?:id=["\']wistia_|data-wistia-?id=["\']|Wistia\.embed\(["\'])(?P<id>[^"\']+)', webpage)
        if match:
            return {
                '_type': 'url_transparent',
                'url': 'http://fast.wistia.net/embed/iframe/{0:}'.format(match.group('id')),
                'ie_key': 'Wistia',
                'uploader': video_uploader,
                'title': video_title,
                'id': match.group('id')
            }

        # Look for embedded blip.tv player
        mobj = re.search(r'<meta\s[^>]*https?://api\.blip\.tv/\w+/redirect/\w+/(\d+)', webpage)
        if mobj:
            return self.url_result('http://blip.tv/a/a-' + mobj.group(1), 'BlipTV')
        mobj = re.search(r'<(?:iframe|embed|object)\s[^>]*(https?://(?:\w+\.)?blip\.tv/(?:play/|api\.swf#)[a-zA-Z0-9_]+)', webpage)
        if mobj:
            return self.url_result(mobj.group(1), 'BlipTV')

        # Look for embedded condenast player
        matches = re.findall(
            r'<iframe\s+(?:[a-zA-Z-]+="[^"]+"\s+)*?src="(https?://player\.cnevids\.com/embed/[^"]+")',
            webpage)
        if matches:
            return {
                '_type': 'playlist',
                'entries': [{
                    '_type': 'url',
                    'ie_key': 'CondeNast',
                    'url': ma,
                } for ma in matches],
                'title': video_title,
                'id': video_id,
            }

        # Look for Bandcamp pages with custom domain
        mobj = re.search(r'<meta property="og:url"[^>]*?content="(.*?bandcamp\.com.*?)"', webpage)
        if mobj is not None:
            burl = unescapeHTML(mobj.group(1))
            # Don't set the extractor because it can be a track url or an album
            return self.url_result(burl)

        # Look for embedded Vevo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:cache\.)?vevo\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Ooyala videos
        mobj = (re.search(r'player.ooyala.com/[^"?]+\?[^"]*?(?:embedCode|ec)=(?P<ec>[^"&]+)', webpage) or
                re.search(r'OO.Player.create\([\'"].*?[\'"],\s*[\'"](?P<ec>.{32})[\'"]', webpage))
        if mobj is not None:
            return OoyalaIE._build_url_result(mobj.group('ec'))

        # Look for Aparat videos
        mobj = re.search(r'<iframe .*?src="(http://www\.aparat\.com/video/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Aparat')

        # Look for MPORA videos
        mobj = re.search(r'<iframe .*?src="(http://mpora\.(?:com|de)/videos/[^"]+)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group(1), 'Mpora')

        # Look for embedded NovaMov-based player
        mobj = re.search(
            r'''(?x)<(?:pagespeed_)?iframe[^>]+?src=(["\'])
                    (?P<url>http://(?:(?:embed|www)\.)?
                        (?:novamov\.com|
                           nowvideo\.(?:ch|sx|eu|at|ag|co)|
                           videoweed\.(?:es|com)|
                           movshare\.(?:net|sx|ag)|
                           divxstage\.(?:eu|net|ch|co|at|ag))
                        /embed\.php.+?)\1''', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for embedded Facebook player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https://www\.facebook\.com/video/embed.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Facebook')

        # Look for embedded VK player
        mobj = re.search(r'<iframe[^>]+?src=(["\'])(?P<url>https?://vk\.com/video_ext\.php.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'VK')

        # Look for embedded ivi player
        mobj = re.search(r'<embed[^>]+?src=(["\'])(?P<url>https?://(?:www\.)?ivi\.ru/video/player.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Ivi')

        # Look for embedded Huffington Post player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://embed\.live\.huffingtonpost\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'HuffPost')

        # Look for embed.ly
        mobj = re.search(r'class=["\']embedly-card["\'][^>]href=["\'](?P<url>[^"\']+)', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))
        mobj = re.search(r'class=["\']embedly-embed["\'][^>]src=["\'][^"\']*url=(?P<url>[^&]+)', webpage)
        if mobj is not None:
            return self.url_result(compat_urllib_parse.unquote(mobj.group('url')))

        # Look for funnyordie embed
        matches = re.findall(r'<iframe[^>]+?src="(https?://(?:www\.)?funnyordie\.com/embed/[^"]+)"', webpage)
        if matches:
            return _playlist_from_matches(
                matches, getter=unescapeHTML, ie='FunnyOrDie')

        # Look for embedded RUTV player
        rutv_url = RUTVIE._extract_url(webpage)
        if rutv_url:
            return self.url_result(rutv_url, 'RUTV')

        # Look for embedded TED player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>http://embed\.ted\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'TED')

        # Look for embedded Ustream videos
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>http://www\.ustream\.tv/embed/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Ustream')

        # Look for embedded arte.tv player
        mobj = re.search(
            r'<script [^>]*?src="(?P<url>http://www\.arte\.tv/playerv2/embed[^"]+)"',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'ArteTVEmbed')

        # Look for embedded smotri.com player
        smotri_url = SmotriIE._extract_url(webpage)
        if smotri_url:
            return self.url_result(smotri_url, 'Smotri')

        # Look for embeded soundcloud player
        mobj = re.search(
            r'<iframe\s+(?:[a-zA-Z0-9_-]+="[^"]+"\s+)*src="(?P<url>https?://(?:w\.)?soundcloud\.com/player[^"]+)"',
            webpage)
        if mobj is not None:
            url = unescapeHTML(mobj.group('url'))
            return self.url_result(url)

        # Look for embedded vulture.com player
        mobj = re.search(
            r'<iframe src="(?P<url>https?://video\.vulture\.com/[^"]+)"',
            webpage)
        if mobj is not None:
            url = unescapeHTML(mobj.group('url'))
            return self.url_result(url, ie='Vulture')

        # Look for embedded mtvservices player
        mobj = re.search(
            r'<iframe src="(?P<url>https?://media\.mtvnservices\.com/embed/[^"]+)"',
            webpage)
        if mobj is not None:
            url = unescapeHTML(mobj.group('url'))
            return self.url_result(url, ie='MTVServicesEmbedded')

        # Look for embedded yahoo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://(?:screen|movies)\.yahoo\.com/.+?\.html\?format=embed)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Yahoo')

        # Look for embedded sbs.com.au player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://(?:www\.)sbs\.com\.au/ondemand/video/single/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'SBS')

        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://m(?:lb)?\.mlb\.com/shared/video/embed/embed\.html\?.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'MLB')

        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>%s)\1' % CondeNastIE.EMBED_URL,
            webpage)
        if mobj is not None:
            return self.url_result(self._proto_relative_url(mobj.group('url'), scheme='http:'), 'CondeNast')

        mobj = re.search(
            r'<iframe[^>]+src="(?P<url>https?://new\.livestream\.com/[^"]+/player[^"]+)"',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Livestream')

        def check_video(vurl):
            vpath = compat_urlparse.urlparse(vurl).path
            vext = determine_ext(vpath)
            return '.' in vpath and vext not in ('swf', 'png', 'jpg', 'srt', 'sbv', 'sub', 'vtt', 'ttml')

        def filter_video(urls):
            return list(filter(check_video, urls))

        # Start with something easy: JW Player in SWFObject
        found = filter_video(re.findall(r'flashvars: [\'"](?:.*&)?file=(http[^\'"&]*)', webpage))
        if not found:
            # Look for gorilla-vid style embedding
            found = filter_video(re.findall(r'''(?sx)
                (?:
                    jw_plugins|
                    JWPlayerOptions|
                    jwplayer\s*\(\s*["'][^'"]+["']\s*\)\s*\.setup
                )
                .*?file\s*:\s*["\'](.*?)["\']''', webpage))
        if not found:
            # Broaden the search a little bit
            found = filter_video(re.findall(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage))
        if not found:
            # Broaden the findall a little bit: JWPlayer JS loader
            found = filter_video(re.findall(
                r'[^A-Za-z0-9]?file["\']?:\s*["\'](http(?![^\'"]+\.[0-9]+[\'"])[^\'"]+)["\']', webpage))
        if not found:
            # Flow player
            found = filter_video(re.findall(r'''(?xs)
                flowplayer\("[^"]+",\s*
                    \{[^}]+?\}\s*,
                    \s*{[^}]+? ["']?clip["']?\s*:\s*\{\s*
                        ["']?url["']?\s*:\s*["']([^"']+)["']
            ''', webpage))
        if not found:
            # Try to find twitter cards info
            found = filter_video(re.findall(
                r'<meta (?:property|name)="twitter:player:stream" (?:content|value)="(.+?)"', webpage))
        if not found:
            # We look for Open Graph info:
            # We have to match any number spaces between elements, some sites try to align them (eg.: statigr.am)
            m_video_type = re.findall(r'<meta.*?property="og:video:type".*?content="video/(.*?)"', webpage)
            # We only look in og:video if the MIME type is a video, don't try if it's a Flash player:
            if m_video_type is not None:
                found = filter_video(re.findall(r'<meta.*?property="og:video".*?content="(.*?)"', webpage))
        if not found:
            # HTML5 video
            found = re.findall(r'(?s)<video[^<]*(?:>.*?<source[^>]*)?\s+src=["\'](.*?)["\']', webpage)
        if not found:
            found = re.search(
                r'(?i)<meta\s+(?=(?:[a-z-]+="[^"]+"\s+)*http-equiv="refresh")'
                r'(?:[a-z-]+="[^"]+"\s+)*?content="[0-9]{,2};url=\'?([^\'"]+)',
                webpage)
            if found:
                new_url = found.group(1)
                self.report_following_redirect(new_url)
                return {
                    '_type': 'url',
                    'url': new_url,
                }
        if not found:
            raise ExtractorError('Unsupported URL: %s' % url)

        entries = []
        for video_url in found:
            video_url = compat_urlparse.urljoin(url, video_url)
            video_id = compat_urllib_parse.unquote(os.path.basename(video_url))

            # Sometimes, jwplayer extraction will result in a YouTube URL
            if YoutubeIE.suitable(video_url):
                entries.append(self.url_result(video_url, 'Youtube'))
                continue

            # here's a fun little line of code for you:
            video_id = os.path.splitext(video_id)[0]

            entries.append({
                'id': video_id,
                'url': video_url,
                'uploader': video_uploader,
                'title': video_title,
                'age_limit': age_limit,
            })

        if len(entries) == 1:
            return entries[0]
        else:
            for num, e in enumerate(entries, start=1):
                e['title'] = '%s (%d)' % (e['title'], num)
            return {
                '_type': 'playlist',
                'entries': entries,
            }
