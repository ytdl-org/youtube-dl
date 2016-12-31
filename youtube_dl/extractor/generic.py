# coding: utf-8

from __future__ import unicode_literals

import os
import re
import sys

from .common import InfoExtractor
from .youtube import YoutubeIE
from ..compat import (
    compat_etree_fromstring,
    compat_urllib_parse_unquote,
    compat_urlparse,
    compat_xml_parse_error,
)
from ..utils import (
    determine_ext,
    ExtractorError,
    float_or_none,
    HEADRequest,
    is_html,
    orderedSet,
    sanitized_Request,
    smuggle_url,
    unescapeHTML,
    unified_strdate,
    unsmuggle_url,
    UnsupportedError,
    xpath_text,
)
from .brightcove import (
    BrightcoveLegacyIE,
    BrightcoveNewIE,
)
from .nbc import NBCSportsVPlayerIE
from .ooyala import OoyalaIE
from .rutv import RUTVIE
from .tvc import TVCIE
from .sportbox import SportBoxEmbedIE
from .smotri import SmotriIE
from .myvi import MyviIE
from .condenast import CondeNastIE
from .udn import UDNEmbedIE
from .senateisvp import SenateISVPIE
from .svt import SVTIE
from .pornhub import PornHubIE
from .xhamster import XHamsterEmbedIE
from .tnaflix import TNAFlixNetworkEmbedIE
from .drtuber import DrTuberIE
from .redtube import RedTubeIE
from .vimeo import VimeoIE
from .dailymotion import (
    DailymotionIE,
    DailymotionCloudIE,
)
from .onionstudios import OnionStudiosIE
from .viewlift import ViewLiftEmbedIE
from .mtv import MTVServicesEmbeddedIE
from .pladform import PladformIE
from .videomore import VideomoreIE
from .webcaster import WebcasterFeedIE
from .googledrive import GoogleDriveIE
from .jwplatform import JWPlatformIE
from .digiteka import DigitekaIE
from .arkena import ArkenaIE
from .instagram import InstagramIE
from .liveleak import LiveLeakIE
from .threeqsdn import ThreeQSDNIE
from .theplatform import ThePlatformIE
from .vessel import VesselIE
from .kaltura import KalturaIE
from .eagleplatform import EaglePlatformIE
from .facebook import FacebookIE
from .soundcloud import SoundcloudIE
from .vbox7 import Vbox7IE
from .dbtv import DBTVIE
from .piksel import PikselIE
from .videa import VideaIE


class GenericIE(InfoExtractor):
    IE_DESC = 'Generic downloader that works on some sites'
    _VALID_URL = r'.*'
    IE_NAME = 'generic'
    _TESTS = [
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
        # Direct link to media delivered compressed (until Accept-Encoding is *)
        {
            'url': 'http://calimero.tk/muzik/FictionJunction-Parallel_Hearts.flac',
            'md5': '128c42e68b13950268b648275386fc74',
            'info_dict': {
                'id': 'FictionJunction-Parallel_Hearts',
                'ext': 'flac',
                'title': 'FictionJunction-Parallel_Hearts',
                'upload_date': '20140522',
            },
            'expected_warnings': [
                'URL could be a direct video link, returning it as such.'
            ],
            'skip': 'URL invalid',
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
                r'501.*Not Implemented',
                r'400.*Bad Request',
            ],
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
        },
        # RSS feed
        {
            'url': 'http://phihag.de/2014/youtube-dl/rss2.xml',
            'info_dict': {
                'id': 'http://phihag.de/2014/youtube-dl/rss2.xml',
                'title': 'Zero Punctuation',
                'description': 're:.*groundbreaking video review series.*'
            },
            'playlist_mincount': 11,
        },
        # RSS feed with enclosure
        {
            'url': 'http://podcastfeeds.nbcnews.com/audio/podcast/MSNBC-MADDOW-NETCAST-M4V.xml',
            'info_dict': {
                'id': 'pdv_maddow_netcast_m4v-02-27-2015-201624',
                'ext': 'm4v',
                'upload_date': '20150228',
                'title': 'pdv_maddow_netcast_m4v-02-27-2015-201624',
            }
        },
        # SMIL from http://videolectures.net/promogram_igor_mekjavic_eng
        {
            'url': 'http://videolectures.net/promogram_igor_mekjavic_eng/video/1/smil.xml',
            'info_dict': {
                'id': 'smil',
                'ext': 'mp4',
                'title': 'Automatics, robotics and biocybernetics',
                'description': 'md5:815fc1deb6b3a2bff99de2d5325be482',
                'upload_date': '20130627',
                'formats': 'mincount:16',
                'subtitles': 'mincount:1',
            },
            'params': {
                'force_generic_extractor': True,
                'skip_download': True,
            },
        },
        # SMIL from http://www1.wdr.de/mediathek/video/livestream/index.html
        {
            'url': 'http://metafilegenerator.de/WDR/WDR_FS/hds/hds.smil',
            'info_dict': {
                'id': 'hds',
                'ext': 'flv',
                'title': 'hds',
                'formats': 'mincount:1',
            },
            'params': {
                'skip_download': True,
            },
        },
        # SMIL from https://www.restudy.dk/video/play/id/1637
        {
            'url': 'https://www.restudy.dk/awsmedia/SmilDirectory/video_1637.xml',
            'info_dict': {
                'id': 'video_1637',
                'ext': 'flv',
                'title': 'video_1637',
                'formats': 'mincount:3',
            },
            'params': {
                'skip_download': True,
            },
        },
        # SMIL from http://adventure.howstuffworks.com/5266-cool-jobs-iditarod-musher-video.htm
        {
            'url': 'http://services.media.howstuffworks.com/videos/450221/smil-service.smil',
            'info_dict': {
                'id': 'smil-service',
                'ext': 'flv',
                'title': 'smil-service',
                'formats': 'mincount:1',
            },
            'params': {
                'skip_download': True,
            },
        },
        # SMIL from http://new.livestream.com/CoheedandCambria/WebsterHall/videos/4719370
        {
            'url': 'http://api.new.livestream.com/accounts/1570303/events/1585861/videos/4719370.smil',
            'info_dict': {
                'id': '4719370',
                'ext': 'mp4',
                'title': '571de1fd-47bc-48db-abf9-238872a58d1f',
                'formats': 'mincount:3',
            },
            'params': {
                'skip_download': True,
            },
        },
        # XSPF playlist from http://www.telegraaf.nl/tv/nieuws/binnenland/24353229/__Tikibad_ontruimd_wegens_brand__.html
        {
            'url': 'http://www.telegraaf.nl/xml/playlist/2015/8/7/mZlp2ctYIUEB.xspf',
            'info_dict': {
                'id': 'mZlp2ctYIUEB',
                'ext': 'mp4',
                'title': 'Tikibad ontruimd wegens brand',
                'description': 'md5:05ca046ff47b931f9b04855015e163a4',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 33,
            },
            'params': {
                'skip_download': True,
            },
        },
        # MPD from http://dash-mse-test.appspot.com/media.html
        {
            'url': 'http://yt-dash-mse-test.commondatastorage.googleapis.com/media/car-20120827-manifest.mpd',
            'md5': '4b57baab2e30d6eb3a6a09f0ba57ef53',
            'info_dict': {
                'id': 'car-20120827-manifest',
                'ext': 'mp4',
                'title': 'car-20120827-manifest',
                'formats': 'mincount:9',
                'upload_date': '20130904',
            },
            'params': {
                'format': 'bestvideo',
            },
        },
        # m3u8 served with Content-Type: audio/x-mpegURL; charset=utf-8
        {
            'url': 'http://once.unicornmedia.com/now/master/playlist/bb0b18ba-64f5-4b1b-a29f-0ac252f06b68/77a785f3-5188-4806-b788-0893a61634ed/93677179-2d99-4ef4-9e17-fe70d49abfbf/content.m3u8',
            'info_dict': {
                'id': 'content',
                'ext': 'mp4',
                'title': 'content',
                'formats': 'mincount:8',
            },
            'params': {
                # m3u8 downloads
                'skip_download': True,
            },
            'skip': 'video gone',
        },
        # m3u8 served with Content-Type: text/plain
        {
            'url': 'http://www.nacentapps.com/m3u8/index.m3u8',
            'info_dict': {
                'id': 'index',
                'ext': 'mp4',
                'title': 'index',
                'upload_date': '20140720',
                'formats': 'mincount:11',
            },
            'params': {
                # m3u8 downloads
                'skip_download': True,
            },
            'skip': 'video gone',
        },
        # google redirect
        {
            'url': 'http://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&ved=0CCUQtwIwAA&url=http%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DcmQHVoWB5FY&ei=F-sNU-LLCaXk4QT52ICQBQ&usg=AFQjCNEw4hL29zgOohLXvpJ-Bdh2bils1Q&bvm=bv.61965928,d.bGE',
            'info_dict': {
                'id': 'cmQHVoWB5FY',
                'ext': 'mp4',
                'upload_date': '20130224',
                'uploader_id': 'TheVerge',
                'description': 're:^Chris Ziegler takes a look at the\.*',
                'uploader': 'The Verge',
                'title': 'First Firefox OS phones side-by-side',
            },
            'params': {
                'skip_download': False,
            }
        },
        {
            # redirect in Refresh HTTP header
            'url': 'https://www.facebook.com/l.php?u=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3DpO8h3EaFRdo&h=TAQHsoToz&enc=AZN16h-b6o4Zq9pZkCCdOLNKMN96BbGMNtcFwHSaazus4JHT_MFYkAA-WARTX2kvsCIdlAIyHZjl6d33ILIJU7Jzwk_K3mcenAXoAzBNoZDI_Q7EXGDJnIhrGkLXo_LJ_pAa2Jzbx17UHMd3jAs--6j2zaeto5w9RTn8T_1kKg3fdC5WPX9Dbb18vzH7YFX0eSJmoa6SP114rvlkw6pkS1-T&s=1',
            'info_dict': {
                'id': 'pO8h3EaFRdo',
                'ext': 'mp4',
                'title': 'Tripeo Boiler Room x Dekmantel Festival DJ Set',
                'description': 'md5:6294cc1af09c4049e0652b51a2df10d5',
                'upload_date': '20150917',
                'uploader_id': 'brtvofficial',
                'uploader': 'Boiler Room',
            },
            'params': {
                'skip_download': False,
            },
        },
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
        {
            # embedded brightcove video
            # it also tests brightcove videos that need to set the 'Referer'
            # in the http requests
            'add_ie': ['BrightcoveLegacy'],
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
            # embedded with itemprop embedURL and video id spelled as `idVideo`
            'add_id': ['BrightcoveLegacy'],
            'url': 'http://bfmbusiness.bfmtv.com/mediaplayer/chroniques/olivier-delamarche/',
            'info_dict': {
                'id': '5255628253001',
                'ext': 'mp4',
                'title': 'md5:37c519b1128915607601e75a87995fc0',
                'description': 'md5:37f7f888b434bb8f8cc8dbd4f7a4cf26',
                'uploader': 'BFM BUSINESS',
                'uploader_id': '876450612001',
                'timestamp': 1482255315,
                'upload_date': '20161220',
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
            'add_ie': ['BrightcoveLegacy'],
            'skip': 'video gone',
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
            'add_ie': ['BrightcoveLegacy'],
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
        # ooyala video
        {
            'url': 'http://www.rollingstone.com/music/videos/norwegian-dj-cashmere-cat-goes-spartan-on-with-me-premiere-20131219',
            'md5': '166dd577b433b4d4ebfee10b0824d8ff',
            'info_dict': {
                'id': 'BwY2RxaTrTkslxOfcan0UCf0YqyvWysJ',
                'ext': 'mp4',
                'title': '2cc213299525360.mov',  # that's what we get
                'duration': 238.231,
            },
            'add_ie': ['Ooyala'],
        },
        {
            # ooyala video embedded with http://player.ooyala.com/iframe.js
            'url': 'http://www.macrumors.com/2015/07/24/steve-jobs-the-man-in-the-machine-first-trailer/',
            'info_dict': {
                'id': 'p0MGJndjoG5SOKqO_hZJuZFPB-Tr5VgB',
                'ext': 'mp4',
                'title': '"Steve Jobs: Man in the Machine" trailer',
                'description': 'The first trailer for the Alex Gibney documentary "Steve Jobs: Man in the Machine."',
                'duration': 135.427,
            },
            'params': {
                'skip_download': True,
            },
            'skip': 'movie expired',
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
            # HEAD requests lead to endless 301, while GET is OK
            'expected_warnings': ['301'],
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
        # TVC embed
        {
            'url': 'http://sch1298sz.mskobr.ru/dou_edu/karamel_ki/filial_galleries/video/iframe_src_http_tvc_ru_video_iframe_id_55304_isplay_false_acc_video_id_channel_brand_id_11_show_episodes_episode_id_32307_frameb/',
            'info_dict': {
                'id': '55304',
                'ext': 'mp4',
                'title': 'Дошкольное воспитание',
            },
        },
        # SportBox embed
        {
            'url': 'http://www.vestifinance.ru/articles/25753',
            'info_dict': {
                'id': '25753',
                'title': 'Прямые трансляции с Форума-выставки "Госзаказ-2013"',
            },
            'playlist': [{
                'info_dict': {
                    'id': '370908',
                    'title': 'Госзаказ. День 3',
                    'ext': 'mp4',
                }
            }, {
                'info_dict': {
                    'id': '370905',
                    'title': 'Госзаказ. День 2',
                    'ext': 'mp4',
                }
            }, {
                'info_dict': {
                    'id': '370902',
                    'title': 'Госзаказ. День 1',
                    'ext': 'mp4',
                }
            }],
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        # Myvi.ru embed
        {
            'url': 'http://www.kinomyvi.tv/news/detail/Pervij-dublirovannij-trejler--Uzhastikov-_nOw1',
            'info_dict': {
                'id': 'f4dafcad-ff21-423d-89b5-146cfd89fa1e',
                'ext': 'mp4',
                'title': 'Ужастики, русский трейлер (2015)',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 153,
            }
        },
        # XHamster embed
        {
            'url': 'http://www.numisc.com/forum/showthread.php?11696-FM15-which-pumiscer-was-this-%28-vid-%29-%28-alfa-as-fuck-srx-%29&s=711f5db534502e22260dec8c5e2d66d8',
            'info_dict': {
                'id': 'showthread',
                'title': '[NSFL] [FM15] which pumiscer was this ( vid ) ( alfa as fuck srx )',
            },
            'playlist_mincount': 7,
            # This forum does not allow <iframe> syntaxes anymore
            # Now HTML tags are displayed as-is
            'skip': 'No videos on this page',
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
        # Embedded Ustream video
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
            },
            'skip': 'video gone',
        },
        # francetv embed
        {
            'url': 'http://www.tsprod.com/replay-du-concert-alcaline-de-calogero',
            'info_dict': {
                'id': 'EV_30231',
                'ext': 'mp4',
                'title': 'Alcaline, le concert avec Calogero',
                'description': 'md5:61f08036dcc8f47e9cfc33aed08ffaff',
                'upload_date': '20150226',
                'timestamp': 1424989860,
                'duration': 5400,
            },
            'params': {
                # m3u8 downloads
                'skip_download': True,
            },
            'expected_warnings': [
                'Forbidden'
            ]
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
                'description': 'md5:faf028e48a461b8b7fad38f1e104b119',
                'uploader': 'Spi0n',
                'uploader_id': 'xgditw',
                'upload_date': '20140425',
                'timestamp': 1398441542,
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
            'url': 'http://www.vulture.com/2016/06/new-key-peele-sketches-released.html',
            'md5': 'ca1aef97695ef2c1d6973256a57e5252',
            'info_dict': {
                'id': '769f7ec0-0692-4d62-9b45-0d88074bffc1',
                'ext': 'mp4',
                'title': 'Key and Peele|October 10, 2012|2|203|Liam Neesons - Uncensored',
                'description': 'Two valets share their love for movie star Liam Neesons.',
                'timestamp': 1349922600,
                'upload_date': '20121011',
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
            'url': 'http://study.com/academy/lesson/north-american-exploration-failed-colonies-of-spain-france-england.html#lesson',
            'md5': '1953f3a698ab51cfc948ed3992a0b7ff',
            'info_dict': {
                'id': '6e2wtrbdaf',
                'ext': 'mov',
                'title': 'paywall_north-american-exploration-failed-colonies-of-spain-france-england',
                'description': 'a Paywall Videos video from Remilon',
                'duration': 644.072,
                'uploader': 'study.com',
                'timestamp': 1459678540,
                'upload_date': '20160403',
                'filesize': 24687186,
            },
        },
        {
            'url': 'http://thoughtworks.wistia.com/medias/uxjb0lwrcz',
            'md5': 'baf49c2baa8a7de5f3fc145a8506dcd4',
            'info_dict': {
                'id': 'uxjb0lwrcz',
                'ext': 'mp4',
                'title': 'Conversation about Hexagonal Rails Part 1',
                'description': 'a Martin Fowler video from ThoughtWorks',
                'duration': 1715.0,
                'uploader': 'thoughtworks.wistia.com',
                'timestamp': 1401832161,
                'upload_date': '20140603',
            },
        },
        # Wistia standard embed (async)
        {
            'url': 'https://www.getdrip.com/university/brennan-dunn-drip-workshop/',
            'info_dict': {
                'id': '807fafadvk',
                'ext': 'mp4',
                'title': 'Drip Brennan Dunn Workshop',
                'description': 'a JV Webinars video from getdrip-1',
                'duration': 4986.95,
                'timestamp': 1463607249,
                'upload_date': '20160518',
            },
            'params': {
                'skip_download': True,
            }
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
        # Soundcloud multiple embeds
        {
            'url': 'http://www.guitarplayer.com/lessons/1014/legato-workout-one-hour-to-more-fluid-performance---tab/52809',
            'info_dict': {
                'id': '52809',
                'title': 'Guitar Essentials: Legato Workout—One-Hour to Fluid Performance  | TAB + AUDIO',
            },
            'playlist_mincount': 7,
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
        # Another Livestream embed, without 'new.' in URL
        {
            'url': 'https://www.freespeech.org/',
            'info_dict': {
                'id': '123537347',
                'ext': 'mp4',
                'title': 're:^FSTV [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
            },
            'params': {
                # Live stream
                'skip_download': True,
            },
        },
        # LazyYT
        {
            'url': 'http://discourse.ubuntu.com/t/unity-8-desktop-mode-windows-on-mir/1986',
            'info_dict': {
                'id': '1986',
                'title': 'Unity 8 desktop-mode windows on Mir! - Ubuntu Discourse',
            },
            'playlist_mincount': 2,
        },
        # Cinchcast embed
        {
            'url': 'http://undergroundwellness.com/podcasts/306-5-steps-to-permanent-gut-healing/',
            'info_dict': {
                'id': '7141703',
                'ext': 'mp3',
                'upload_date': '20141126',
                'title': 'Jack Tips: 5 Steps to Permanent Gut Healing',
            }
        },
        # Cinerama player
        {
            'url': 'http://www.abc.net.au/7.30/content/2015/s4164797.htm',
            'info_dict': {
                'id': '730m_DandD_1901_512k',
                'ext': 'mp4',
                'uploader': 'www.abc.net.au',
                'title': 'Game of Thrones with dice - Dungeons and Dragons fantasy role-playing game gets new life - 19/01/2015',
            }
        },
        # embedded viddler video
        {
            'url': 'http://deadspin.com/i-cant-stop-watching-john-wall-chop-the-nuggets-with-th-1681801597',
            'info_dict': {
                'id': '4d03aad9',
                'ext': 'mp4',
                'uploader': 'deadspin',
                'title': 'WALL-TO-GORTAT',
                'timestamp': 1422285291,
                'upload_date': '20150126',
            },
            'add_ie': ['Viddler'],
        },
        # Libsyn embed
        {
            'url': 'http://thedailyshow.cc.com/podcast/episodetwelve',
            'info_dict': {
                'id': '3377616',
                'ext': 'mp3',
                'title': "The Daily Show Podcast without Jon Stewart - Episode 12: Bassem Youssef: Egypt's Jon Stewart",
                'description': 'md5:601cb790edd05908957dae8aaa866465',
                'upload_date': '20150220',
            },
            'skip': 'All The Daily Show URLs now redirect to http://www.cc.com/shows/',
        },
        # jwplayer YouTube
        {
            'url': 'http://media.nationalarchives.gov.uk/index.php/webinar-using-discovery-national-archives-online-catalogue/',
            'info_dict': {
                'id': 'Mrj4DVp2zeA',
                'ext': 'mp4',
                'upload_date': '20150212',
                'uploader': 'The National Archives UK',
                'description': 'md5:a236581cd2449dd2df4f93412f3f01c6',
                'uploader_id': 'NationalArchives08',
                'title': 'Webinar: Using Discovery, The National Archives’ online catalogue',
            },
        },
        # rtl.nl embed
        {
            'url': 'http://www.rtlnieuws.nl/nieuws/buitenland/aanslagen-kopenhagen',
            'playlist_mincount': 5,
            'info_dict': {
                'id': 'aanslagen-kopenhagen',
                'title': 'Aanslagen Kopenhagen | RTL Nieuws',
            }
        },
        # Zapiks embed
        {
            'url': 'http://www.skipass.com/news/116090-bon-appetit-s5ep3-baqueira-mi-cor.html',
            'info_dict': {
                'id': '118046',
                'ext': 'mp4',
                'title': 'EP3S5 - Bon Appétit - Baqueira Mi Corazon !',
            }
        },
        # Kaltura embed (different embed code)
        {
            'url': 'http://www.premierchristianradio.com/Shows/Saturday/Unbelievable/Conference-Videos/Os-Guinness-Is-It-Fools-Talk-Unbelievable-Conference-2014',
            'info_dict': {
                'id': '1_a52wc67y',
                'ext': 'flv',
                'upload_date': '20150127',
                'uploader_id': 'PremierMedia',
                'timestamp': int,
                'title': 'Os Guinness // Is It Fools Talk? // Unbelievable? Conference 2014',
            },
        },
        # Kaltura embed protected with referrer
        {
            'url': 'http://www.disney.nl/disney-channel/filmpjes/achter-de-schermen#/videoId/violetta-achter-de-schermen-ruggero',
            'info_dict': {
                'id': '1_g4fbemnq',
                'ext': 'mp4',
                'title': 'Violetta - Achter De Schermen - Ruggero',
                'description': 'Achter de schermen met Ruggero',
                'timestamp': 1435133761,
                'upload_date': '20150624',
                'uploader_id': 'echojecka',
            },
        },
        # Kaltura embed with single quotes
        {
            'url': 'http://fod.infobase.com/p_ViewPlaylist.aspx?AssignmentID=NUN8ZY',
            'info_dict': {
                'id': '0_izeg5utt',
                'ext': 'mp4',
                'title': '35871',
                'timestamp': 1355743100,
                'upload_date': '20121217',
                'uploader_id': 'batchUser',
            },
            'add_ie': ['Kaltura'],
        },
        {
            # Kaltura embedded via quoted entry_id
            'url': 'https://www.oreilly.com/ideas/my-cloud-makes-pretty-pictures',
            'info_dict': {
                'id': '0_utuok90b',
                'ext': 'mp4',
                'title': '06_matthew_brender_raj_dutt',
                'timestamp': 1466638791,
                'upload_date': '20160622',
            },
            'add_ie': ['Kaltura'],
            'expected_warnings': [
                'Could not send HEAD request'
            ],
            'params': {
                'skip_download': True,
            }
        },
        {
            # Kaltura embedded, some fileExt broken (#11480)
            'url': 'http://www.cornell.edu/video/nima-arkani-hamed-standard-models-of-particle-physics',
            'info_dict': {
                'id': '1_sgtvehim',
                'ext': 'mp4',
                'title': 'Our "Standard Models" of particle physics and cosmology',
                'description': 'md5:67ea74807b8c4fea92a6f38d6d323861',
                'timestamp': 1321158993,
                'upload_date': '20111113',
                'uploader_id': 'kps1',
            },
            'add_ie': ['Kaltura'],
        },
        # Eagle.Platform embed (generic URL)
        {
            'url': 'http://lenta.ru/news/2015/03/06/navalny/',
            # Not checking MD5 as sometimes the direct HTTP link results in 404 and HLS is used
            'info_dict': {
                'id': '227304',
                'ext': 'mp4',
                'title': 'Навальный вышел на свободу',
                'description': 'md5:d97861ac9ae77377f3f20eaf9d04b4f5',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 87,
                'view_count': int,
                'age_limit': 0,
            },
        },
        # ClipYou (Eagle.Platform) embed (custom URL)
        {
            'url': 'http://muz-tv.ru/play/7129/',
            # Not checking MD5 as sometimes the direct HTTP link results in 404 and HLS is used
            'info_dict': {
                'id': '12820',
                'ext': 'mp4',
                'title': "'O Sole Mio",
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 216,
                'view_count': int,
            },
        },
        # Pladform embed
        {
            'url': 'http://muz-tv.ru/kinozal/view/7400/',
            'info_dict': {
                'id': '100183293',
                'ext': 'mp4',
                'title': 'Тайны перевала Дятлова • 1 серия 2 часть',
                'description': 'Документальный сериал-расследование одной из самых жутких тайн ХХ века',
                'thumbnail': 're:^https?://.*\.jpg$',
                'duration': 694,
                'age_limit': 0,
            },
        },
        # Playwire embed
        {
            'url': 'http://www.cinemablend.com/new/First-Joe-Dirt-2-Trailer-Teaser-Stupid-Greatness-70874.html',
            'info_dict': {
                'id': '3519514',
                'ext': 'mp4',
                'title': 'Joe Dirt 2 Beautiful Loser Teaser Trailer',
                'thumbnail': 're:^https?://.*\.png$',
                'duration': 45.115,
            },
        },
        # 5min embed
        {
            'url': 'http://techcrunch.com/video/facebook-creates-on-this-day-crunch-report/518726732/',
            'md5': '4c6f127a30736b59b3e2c19234ee2bf7',
            'info_dict': {
                'id': '518726732',
                'ext': 'mp4',
                'title': 'Facebook Creates "On This Day" | Crunch Report',
            },
        },
        # SVT embed
        {
            'url': 'http://www.svt.se/sport/ishockey/jagr-tacklar-giroux-under-intervjun',
            'info_dict': {
                'id': '2900353',
                'ext': 'flv',
                'title': 'Här trycker Jagr till Giroux (under SVT-intervjun)',
                'duration': 27,
                'age_limit': 0,
            },
        },
        # Crooks and Liars embed
        {
            'url': 'http://crooksandliars.com/2015/04/fox-friends-says-protecting-atheists',
            'info_dict': {
                'id': '8RUoRhRi',
                'ext': 'mp4',
                'title': "Fox & Friends Says Protecting Atheists From Discrimination Is Anti-Christian!",
                'description': 'md5:e1a46ad1650e3a5ec7196d432799127f',
                'timestamp': 1428207000,
                'upload_date': '20150405',
                'uploader': 'Heather',
            },
        },
        # Crooks and Liars external embed
        {
            'url': 'http://theothermccain.com/2010/02/02/video-proves-that-bill-kristol-has-been-watching-glenn-beck/comment-page-1/',
            'info_dict': {
                'id': 'MTE3MjUtMzQ2MzA',
                'ext': 'mp4',
                'title': 'md5:5e3662a81a4014d24c250d76d41a08d5',
                'description': 'md5:9b8e9542d6c3c5de42d6451b7d780cec',
                'timestamp': 1265032391,
                'upload_date': '20100201',
                'uploader': 'Heather',
            },
        },
        # NBC Sports vplayer embed
        {
            'url': 'http://www.riderfans.com/forum/showthread.php?121827-Freeman&s=e98fa1ea6dc08e886b1678d35212494a',
            'info_dict': {
                'id': 'ln7x1qSThw4k',
                'ext': 'flv',
                'title': "PFT Live: New leader in the 'new-look' defense",
                'description': 'md5:65a19b4bbfb3b0c0c5768bed1dfad74e',
                'uploader': 'NBCU-SPORTS',
                'upload_date': '20140107',
                'timestamp': 1389118457,
            },
        },
        # NBC News embed
        {
            'url': 'http://www.vulture.com/2016/06/letterman-couldnt-care-less-about-late-night.html',
            'md5': '1aa589c675898ae6d37a17913cf68d66',
            'info_dict': {
                'id': '701714499682',
                'ext': 'mp4',
                'title': 'PREVIEW: On Assignment: David Letterman',
                'description': 'A preview of Tom Brokaw\'s interview with David Letterman as part of the On Assignment series powered by Dateline. Airs Sunday June 12 at 7/6c.',
            },
        },
        # UDN embed
        {
            'url': 'https://video.udn.com/news/300346',
            'md5': 'fd2060e988c326991037b9aff9df21a6',
            'info_dict': {
                'id': '300346',
                'ext': 'mp4',
                'title': '中一中男師變性 全校師生力挺',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        # Ooyala embed
        {
            'url': 'http://www.businessinsider.com/excel-index-match-vlookup-video-how-to-2015-2?IR=T',
            'info_dict': {
                'id': '50YnY4czr4ms1vJ7yz3xzq0excz_pUMs',
                'ext': 'mp4',
                'description': 'VIDEO: INDEX/MATCH versus VLOOKUP.',
                'title': 'This is what separates the Excel masters from the wannabes',
                'duration': 191.933,
            },
            'params': {
                # m3u8 downloads
                'skip_download': True,
            }
        },
        # Brightcove URL in single quotes
        {
            'url': 'http://www.sportsnet.ca/baseball/mlb/sn-presents-russell-martin-world-citizen/',
            'md5': '4ae374f1f8b91c889c4b9203c8c752af',
            'info_dict': {
                'id': '4255764656001',
                'ext': 'mp4',
                'title': 'SN Presents: Russell Martin, World Citizen',
                'description': 'To understand why he was the Toronto Blue Jays’ top off-season priority is to appreciate his background and upbringing in Montreal, where he first developed his baseball skills. Written and narrated by Stephen Brunt.',
                'uploader': 'Rogers Sportsnet',
                'uploader_id': '1704050871',
                'upload_date': '20150525',
                'timestamp': 1432570283,
            },
        },
        # Dailymotion Cloud video
        {
            'url': 'http://replay.publicsenat.fr/vod/le-debat/florent-kolandjian,dominique-cena,axel-decourtye,laurence-abeille,bruno-parmentier/175910',
            'md5': 'dcaf23ad0c67a256f4278bce6e0bae38',
            'info_dict': {
                'id': 'x2uy8t3',
                'ext': 'mp4',
                'title': 'Sauvons les abeilles ! - Le débat',
                'description': 'md5:d9082128b1c5277987825d684939ca26',
                'thumbnail': 're:^https?://.*\.jpe?g$',
                'timestamp': 1434970506,
                'upload_date': '20150622',
                'uploader': 'Public Sénat',
                'uploader_id': 'xa9gza',
            }
        },
        # OnionStudios embed
        {
            'url': 'http://www.clickhole.com/video/dont-understand-bitcoin-man-will-mumble-explanatio-2537',
            'info_dict': {
                'id': '2855',
                'ext': 'mp4',
                'title': 'Don’t Understand Bitcoin? This Man Will Mumble An Explanation At You',
                'thumbnail': 're:^https?://.*\.jpe?g$',
                'uploader': 'ClickHole',
                'uploader_id': 'clickhole',
            }
        },
        # SnagFilms embed
        {
            'url': 'http://whilewewatch.blogspot.ru/2012/06/whilewewatch-whilewewatch-gripping.html',
            'info_dict': {
                'id': '74849a00-85a9-11e1-9660-123139220831',
                'ext': 'mp4',
                'title': '#whilewewatch',
            }
        },
        # AdobeTVVideo embed
        {
            'url': 'https://helpx.adobe.com/acrobat/how-to/new-experience-acrobat-dc.html?set=acrobat--get-started--essential-beginners',
            'md5': '43662b577c018ad707a63766462b1e87',
            'info_dict': {
                'id': '2456',
                'ext': 'mp4',
                'title': 'New experience with Acrobat DC',
                'description': 'New experience with Acrobat DC',
                'duration': 248.667,
            },
        },
        # BrightcoveInPageEmbed embed
        {
            'url': 'http://www.geekandsundry.com/tabletop-bonus-wils-final-thoughts-on-dread/',
            'info_dict': {
                'id': '4238694884001',
                'ext': 'flv',
                'title': 'Tabletop: Dread, Last Thoughts',
                'description': 'Tabletop: Dread, Last Thoughts',
                'duration': 51690,
            },
        },
        # Brightcove embed, with no valid 'renditions' but valid 'IOSRenditions'
        # This video can't be played in browsers if Flash disabled and UA set to iPhone, which is actually a false alarm
        {
            'url': 'https://dl.dropboxusercontent.com/u/29092637/interview.html',
            'info_dict': {
                'id': '4785848093001',
                'ext': 'mp4',
                'title': 'The Cardinal Pell Interview',
                'description': 'Sky News Contributor Andrew Bolt interviews George Pell in Rome, following the Cardinal\'s evidence before the Royal Commission into Child Abuse. ',
                'uploader': 'GlobeCast Australia - GlobeStream',
                'uploader_id': '2733773828001',
                'upload_date': '20160304',
                'timestamp': 1457083087,
            },
            'params': {
                # m3u8 downloads
                'skip_download': True,
            },
        },
        # Another form of arte.tv embed
        {
            'url': 'http://www.tv-replay.fr/redirection/09-04-16/arte-reportage-arte-11508975.html',
            'md5': '850bfe45417ddf221288c88a0cffe2e2',
            'info_dict': {
                'id': '030273-562_PLUS7-F',
                'ext': 'mp4',
                'title': 'ARTE Reportage - Nulle part, en France',
                'description': 'md5:e3a0e8868ed7303ed509b9e3af2b870d',
                'upload_date': '20160409',
            },
        },
        # LiveLeak embed
        {
            'url': 'http://www.wykop.pl/link/3088787/',
            'md5': 'ace83b9ed19b21f68e1b50e844fdf95d',
            'info_dict': {
                'id': '874_1459135191',
                'ext': 'mp4',
                'title': 'Man shows poor quality of new apartment building',
                'description': 'The wall is like a sand pile.',
                'uploader': 'Lake8737',
            }
        },
        # Duplicated embedded video URLs
        {
            'url': 'http://www.hudl.com/athlete/2538180/highlights/149298443',
            'info_dict': {
                'id': '149298443_480_16c25b74_2',
                'ext': 'mp4',
                'title': 'vs. Blue Orange Spring Game',
                'uploader': 'www.hudl.com',
            },
        },
        # twitter:player:stream embed
        {
            'url': 'http://www.rtl.be/info/video/589263.aspx?CategoryID=288',
            'info_dict': {
                'id': 'master',
                'ext': 'mp4',
                'title': 'Une nouvelle espèce de dinosaure découverte en Argentine',
                'uploader': 'www.rtl.be',
            },
            'params': {
                # m3u8 downloads
                'skip_download': True,
            },
        },
        # twitter:player embed
        {
            'url': 'http://www.theatlantic.com/video/index/484130/what-do-black-holes-sound-like/',
            'md5': 'a3e0df96369831de324f0778e126653c',
            'info_dict': {
                'id': '4909620399001',
                'ext': 'mp4',
                'title': 'What Do Black Holes Sound Like?',
                'description': 'what do black holes sound like',
                'upload_date': '20160524',
                'uploader_id': '29913724001',
                'timestamp': 1464107587,
                'uploader': 'TheAtlantic',
            },
            'add_ie': ['BrightcoveLegacy'],
        },
        # Facebook <iframe> embed
        {
            'url': 'https://www.hostblogger.de/blog/archives/6181-Auto-jagt-Betonmischer.html',
            'md5': 'fbcde74f534176ecb015849146dd3aee',
            'info_dict': {
                'id': '599637780109885',
                'ext': 'mp4',
                'title': 'Facebook video #599637780109885',
            },
        },
        # Facebook API embed
        {
            'url': 'http://www.lothype.com/blue-stars-2016-preview-standstill-full-show/',
            'md5': 'a47372ee61b39a7b90287094d447d94e',
            'info_dict': {
                'id': '10153467542406923',
                'ext': 'mp4',
                'title': 'Facebook video #10153467542406923',
            },
        },
        # Wordpress "YouTube Video Importer" plugin
        {
            'url': 'http://www.lothype.com/blue-devils-drumline-stanford-lot-2016/',
            'md5': 'd16797741b560b485194eddda8121b48',
            'info_dict': {
                'id': 'HNTXWDXV9Is',
                'ext': 'mp4',
                'title': 'Blue Devils Drumline Stanford lot 2016',
                'upload_date': '20160627',
                'uploader_id': 'GENOCIDE8GENERAL10',
                'uploader': 'cylus cyrus',
            },
        },
        {
            # video stored on custom kaltura server
            'url': 'http://www.expansion.com/multimedia/videos.html?media=EQcM30NHIPv',
            'md5': '537617d06e64dfed891fa1593c4b30cc',
            'info_dict': {
                'id': '0_1iotm5bh',
                'ext': 'mp4',
                'title': 'Elecciones británicas: 5 lecciones para Rajoy',
                'description': 'md5:435a89d68b9760b92ce67ed227055f16',
                'uploader_id': 'videos.expansion@el-mundo.net',
                'upload_date': '20150429',
                'timestamp': 1430303472,
            },
            'add_ie': ['Kaltura'],
        },
        {
            # Non-standard Vimeo embed
            'url': 'https://openclassrooms.com/courses/understanding-the-web',
            'md5': '64d86f1c7d369afd9a78b38cbb88d80a',
            'info_dict': {
                'id': '148867247',
                'ext': 'mp4',
                'title': 'Understanding the web - Teaser',
                'description': 'This is "Understanding the web - Teaser" by openclassrooms on Vimeo, the home for high quality videos and the people who love them.',
                'upload_date': '20151214',
                'uploader': 'OpenClassrooms',
                'uploader_id': 'openclassrooms',
            },
            'add_ie': ['Vimeo'],
        },
        {
            # generic vimeo embed that requires original URL passed as Referer
            'url': 'http://racing4everyone.eu/2016/07/30/formula-1-2016-round12-germany/',
            'only_matching': True,
        },
        {
            'url': 'https://support.arkena.com/display/PLAY/Ways+to+embed+your+video',
            'md5': 'b96f2f71b359a8ecd05ce4e1daa72365',
            'info_dict': {
                'id': 'b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe',
                'ext': 'mp4',
                'title': 'Big Buck Bunny',
                'description': 'Royalty free test video',
                'timestamp': 1432816365,
                'upload_date': '20150528',
                'is_live': False,
            },
            'params': {
                'skip_download': True,
            },
            'add_ie': [ArkenaIE.ie_key()],
        },
        {
            'url': 'http://nova.bg/news/view/2016/08/16/156543/%D0%BD%D0%B0-%D0%BA%D0%BE%D1%81%D1%8A%D0%BC-%D0%BE%D1%82-%D0%B2%D0%B7%D1%80%D0%B8%D0%B2-%D0%BE%D1%82%D1%86%D0%B5%D0%BF%D0%B8%D1%85%D0%B0-%D1%86%D1%8F%D0%BB-%D0%BA%D0%B2%D0%B0%D1%80%D1%82%D0%B0%D0%BB-%D0%B7%D0%B0%D1%80%D0%B0%D0%B4%D0%B8-%D0%B8%D0%B7%D1%82%D0%B8%D1%87%D0%B0%D0%BD%D0%B5-%D0%BD%D0%B0-%D0%B3%D0%B0%D0%B7-%D0%B2-%D0%BF%D0%BB%D0%BE%D0%B2%D0%B4%D0%B8%D0%B2/',
            'info_dict': {
                'id': '1c7141f46c',
                'ext': 'mp4',
                'title': 'НА КОСЪМ ОТ ВЗРИВ: Изтичане на газ на бензиностанция в Пловдив',
            },
            'params': {
                'skip_download': True,
            },
            'add_ie': [Vbox7IE.ie_key()],
        },
        {
            # DBTV embeds
            'url': 'http://www.dagbladet.no/2016/02/23/nyheter/nordlys/ski/troms/ver/43254897/',
            'info_dict': {
                'id': '43254897',
                'title': 'Etter ett års planlegging, klaffet endelig alt: - Jeg måtte ta en liten dans',
            },
            'playlist_mincount': 3,
        },
        {
            # Videa embeds
            'url': 'http://forum.dvdtalk.com/movie-talk/623756-deleted-magic-star-wars-ot-deleted-alt-scenes-docu-style.html',
            'info_dict': {
                'id': '623756-deleted-magic-star-wars-ot-deleted-alt-scenes-docu-style',
                'title': 'Deleted Magic - Star Wars: OT Deleted / Alt. Scenes Docu. Style - DVD Talk Forum',
            },
            'playlist_mincount': 2,
        },
        # {
        #     # TODO: find another test
        #     # http://schema.org/VideoObject
        #     'url': 'https://flipagram.com/f/nyvTSJMKId',
        #     'md5': '888dcf08b7ea671381f00fab74692755',
        #     'info_dict': {
        #         'id': 'nyvTSJMKId',
        #         'ext': 'mp4',
        #         'title': 'Flipagram by sjuria101 featuring Midnight Memories by One Direction',
        #         'description': '#love for cats.',
        #         'timestamp': 1461244995,
        #         'upload_date': '20160421',
        #     },
        #     'params': {
        #         'force_generic_extractor': True,
        #     },
        # }
    ]

    def report_following_redirect(self, new_url):
        """Report information extraction."""
        self._downloader.to_screen('[redirect] Following redirect to %s' % new_url)

    def _extract_rss(self, url, video_id, doc):
        playlist_title = doc.find('./channel/title').text
        playlist_desc_el = doc.find('./channel/description')
        playlist_desc = None if playlist_desc_el is None else playlist_desc_el.text

        entries = []
        for it in doc.findall('./channel/item'):
            next_url = xpath_text(it, 'link', fatal=False)
            if not next_url:
                enclosure_nodes = it.findall('./enclosure')
                for e in enclosure_nodes:
                    next_url = e.attrib.get('url')
                    if next_url:
                        break

            if not next_url:
                continue

            entries.append({
                '_type': 'url',
                'url': next_url,
                'title': it.find('title').text,
            })

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
            video_id = self._generic_id(url)

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
            request = sanitized_Request(url)
            request.add_header('Accept-Encoding', '*')
            full_response = self._request_webpage(request, video_id)
            head_response = full_response

        info_dict = {
            'id': video_id,
            'title': self._generic_title(url),
            'upload_date': unified_strdate(head_response.headers.get('Last-Modified'))
        }

        # Check for direct link to a video
        content_type = head_response.headers.get('Content-Type', '').lower()
        m = re.match(r'^(?P<type>audio|video|application(?=/(?:ogg$|(?:vnd\.apple\.|x-)?mpegurl)))/(?P<format_id>[^;\s]+)', content_type)
        if m:
            format_id = m.group('format_id')
            if format_id.endswith('mpegurl'):
                formats = self._extract_m3u8_formats(url, video_id, 'mp4')
            elif format_id == 'f4m':
                formats = self._extract_f4m_formats(url, video_id)
            else:
                formats = [{
                    'format_id': m.group('format_id'),
                    'url': url,
                    'vcodec': 'none' if m.group('type') == 'audio' else None
                }]
                info_dict['direct'] = True
            self._sort_formats(formats)
            info_dict['formats'] = formats
            return info_dict

        if not self._downloader.params.get('test', False) and not is_intentional:
            force = self._downloader.params.get('force_generic_extractor', False)
            self._downloader.report_warning(
                '%s on generic information extractor.' % ('Forcing' if force else 'Falling back'))

        if not full_response:
            request = sanitized_Request(url)
            # Some webservers may serve compressed content of rather big size (e.g. gzipped flac)
            # making it impossible to download only chunk of the file (yet we need only 512kB to
            # test whether it's HTML or not). According to youtube-dl default Accept-Encoding
            # that will always result in downloading the whole file that is not desirable.
            # Therefore for extraction pass we have to override Accept-Encoding to any in order
            # to accept raw bytes and being able to download only a chunk.
            # It may probably better to solve this by checking Content-Type for application/octet-stream
            # after HEAD request finishes, but not sure if we can rely on this.
            request.add_header('Accept-Encoding', '*')
            full_response = self._request_webpage(request, video_id)

        first_bytes = full_response.read(512)

        # Is it an M3U playlist?
        if first_bytes.startswith(b'#EXTM3U'):
            info_dict['formats'] = self._extract_m3u8_formats(url, video_id, 'mp4')
            self._sort_formats(info_dict['formats'])
            return info_dict

        # Maybe it's a direct link to a video?
        # Be careful not to download the whole thing!
        if not is_html(first_bytes):
            self._downloader.report_warning(
                'URL could be a direct video link, returning it as such.')
            info_dict.update({
                'direct': True,
                'url': url,
            })
            return info_dict

        webpage = self._webpage_read_content(
            full_response, url, video_id, prefix=first_bytes)

        self.report_extraction(video_id)

        # Is it an RSS feed, a SMIL file, an XSPF playlist or a MPD manifest?
        try:
            doc = compat_etree_fromstring(webpage.encode('utf-8'))
            if doc.tag == 'rss':
                return self._extract_rss(url, video_id, doc)
            elif doc.tag == 'SmoothStreamingMedia':
                info_dict['formats'] = self._parse_ism_formats(doc, url)
                self._sort_formats(info_dict['formats'])
                return info_dict
            elif re.match(r'^(?:{[^}]+})?smil$', doc.tag):
                smil = self._parse_smil(doc, url, video_id)
                self._sort_formats(smil['formats'])
                return smil
            elif doc.tag == '{http://xspf.org/ns/0/}playlist':
                return self.playlist_result(self._parse_xspf(doc, video_id), video_id)
            elif re.match(r'(?i)^(?:{[^}]+})?MPD$', doc.tag):
                info_dict['formats'] = self._parse_mpd_formats(
                    doc, video_id,
                    mpd_base_url=full_response.geturl().rpartition('/')[0],
                    mpd_url=url)
                self._sort_formats(info_dict['formats'])
                return info_dict
            elif re.match(r'^{http://ns\.adobe\.com/f4m/[12]\.0}manifest$', doc.tag):
                info_dict['formats'] = self._parse_f4m_formats(doc, url, video_id)
                self._sort_formats(info_dict['formats'])
                return info_dict
        except compat_xml_parse_error:
            pass

        # Is it a Camtasia project?
        camtasia_res = self._extract_camtasia(url, video_id, webpage)
        if camtasia_res is not None:
            return camtasia_res

        # Sometimes embedded video player is hidden behind percent encoding
        # (e.g. https://github.com/rg3/youtube-dl/issues/2448)
        # Unescaping the whole page allows to handle those cases in a generic way
        webpage = compat_urllib_parse_unquote(webpage)

        # it's tempting to parse this further, but you would
        # have to take into account all the variations like
        #   Video Title - Site Name
        #   Site Name | Video Title
        #   Video Title - Tagline | Site Name
        # and so on and so forth; it's just not practical
        video_title = self._og_search_title(
            webpage, default=None) or self._html_search_regex(
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

        video_description = self._og_search_description(webpage, default=None)
        video_thumbnail = self._og_search_thumbnail(webpage, default=None)

        # Helper method
        def _playlist_from_matches(matches, getter=None, ie=None):
            urlrs = orderedSet(
                self.url_result(self._proto_relative_url(getter(m) if getter else m), ie)
                for m in matches)
            return self.playlist_result(
                urlrs, playlist_id=video_id, playlist_title=video_title)

        # Look for Brightcove Legacy Studio embeds
        bc_urls = BrightcoveLegacyIE._extract_brightcove_urls(webpage)
        if bc_urls:
            self.to_screen('Brightcove video detected.')
            entries = [{
                '_type': 'url',
                'url': smuggle_url(bc_url, {'Referer': url}),
                'ie_key': 'BrightcoveLegacy'
            } for bc_url in bc_urls]

            return {
                '_type': 'playlist',
                'title': video_title,
                'id': video_id,
                'entries': entries,
            }

        # Look for Brightcove New Studio embeds
        bc_urls = BrightcoveNewIE._extract_urls(webpage)
        if bc_urls:
            return _playlist_from_matches(bc_urls, ie='BrightcoveNew')

        # Look for ThePlatform embeds
        tp_urls = ThePlatformIE._extract_urls(webpage)
        if tp_urls:
            return _playlist_from_matches(tp_urls, ie='ThePlatform')

        # Look for Vessel embeds
        vessel_urls = VesselIE._extract_urls(webpage)
        if vessel_urls:
            return _playlist_from_matches(vessel_urls, ie=VesselIE.ie_key())

        # Look for embedded rtl.nl player
        matches = re.findall(
            r'<iframe[^>]+?src="((?:https?:)?//(?:www\.)?rtl\.nl/system/videoplayer/[^"]+(?:video_)?embed[^"]+)"',
            webpage)
        if matches:
            return _playlist_from_matches(matches, ie='RtlNl')

        vimeo_urls = VimeoIE._extract_urls(url, webpage)
        if vimeo_urls:
            return _playlist_from_matches(vimeo_urls, ie=VimeoIE.ie_key())

        vid_me_embed_url = self._search_regex(
            r'src=[\'"](https?://vid\.me/[^\'"]+)[\'"]',
            webpage, 'vid.me embed', default=None)
        if vid_me_embed_url is not None:
            return self.url_result(vid_me_embed_url, 'Vidme')

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

        # Look for Wordpress "YouTube Video Importer" plugin
        matches = re.findall(r'''(?x)<div[^>]+
            class=(?P<q1>[\'"])[^\'"]*\byvii_single_video_player\b[^\'"]*(?P=q1)[^>]+
            data-video_id=(?P<q2>[\'"])([^\'"]+)(?P=q2)''', webpage)
        if matches:
            return _playlist_from_matches(matches, lambda m: m[-1])

        matches = DailymotionIE._extract_urls(webpage)
        if matches:
            return _playlist_from_matches(matches)

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
            }

        match = re.search(r'(?:id=["\']wistia_|data-wistia-?id=["\']|Wistia\.embed\(["\'])(?P<id>[^"\']+)', webpage)
        if match:
            return {
                '_type': 'url_transparent',
                'url': 'wistia:%s' % match.group('id'),
                'ie_key': 'Wistia',
                'uploader': video_uploader,
            }

        match = re.search(
            r'''(?sx)
                <script[^>]+src=(["'])(?:https?:)?//fast\.wistia\.com/assets/external/E-v1\.js\1[^>]*>.*?
                <div[^>]+class=(["']).*?\bwistia_async_(?P<id>[a-z0-9]+)\b.*?\2
            ''', webpage)
        if match:
            return self.url_result(self._proto_relative_url(
                'wistia:%s' % match.group('id')), 'Wistia')

        # Look for SVT player
        svt_url = SVTIE._extract_url(webpage)
        if svt_url:
            return self.url_result(svt_url, 'SVT')

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

        # Look for embedded Viddler player
        mobj = re.search(
            r'<(?:iframe[^>]+?src|param[^>]+?value)=(["\'])(?P<url>(?:https?:)?//(?:www\.)?viddler\.com/(?:embed|player)/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for NYTimes player
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//graphics8\.nytimes\.com/bcvideo/[^/]+/iframe/embed\.html.+?)\1>',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Libsyn player
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//html5-player\.libsyn\.com/embed/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for Ooyala videos
        mobj = (re.search(r'player\.ooyala\.com/[^"?]+[?#][^"]*?(?:embedCode|ec)=(?P<ec>[^"&]+)', webpage) or
                re.search(r'OO\.Player\.create\([\'"].*?[\'"],\s*[\'"](?P<ec>.{32})[\'"]', webpage) or
                re.search(r'SBN\.VideoLinkset\.ooyala\([\'"](?P<ec>.{32})[\'"]\)', webpage) or
                re.search(r'data-ooyala-video-id\s*=\s*[\'"](?P<ec>.{32})[\'"]', webpage))
        if mobj is not None:
            return OoyalaIE._build_url_result(smuggle_url(mobj.group('ec'), {'domain': url}))

        # Look for multiple Ooyala embeds on SBN network websites
        mobj = re.search(r'SBN\.VideoLinkset\.entryGroup\((\[.*?\])', webpage)
        if mobj is not None:
            embeds = self._parse_json(mobj.group(1), video_id, fatal=False)
            if embeds:
                return _playlist_from_matches(
                    embeds, getter=lambda v: OoyalaIE._url_for_embed_code(smuggle_url(v['provider_video_id'], {'domain': url})), ie='Ooyala')

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
        facebook_url = FacebookIE._extract_url(webpage)
        if facebook_url is not None:
            return self.url_result(facebook_url, 'Facebook')

        # Look for embedded VK player
        mobj = re.search(r'<iframe[^>]+?src=(["\'])(?P<url>https?://vk\.com/video_ext\.php.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'VK')

        # Look for embedded Odnoklassniki player
        mobj = re.search(r'<iframe[^>]+?src=(["\'])(?P<url>https?://(?:odnoklassniki|ok)\.ru/videoembed/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Odnoklassniki')

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
            return self.url_result(compat_urllib_parse_unquote(mobj.group('url')))

        # Look for funnyordie embed
        matches = re.findall(r'<iframe[^>]+?src="(https?://(?:www\.)?funnyordie\.com/embed/[^"]+)"', webpage)
        if matches:
            return _playlist_from_matches(
                matches, getter=unescapeHTML, ie='FunnyOrDie')

        # Look for BBC iPlayer embed
        matches = re.findall(r'setPlaylist\("(https?://www\.bbc\.co\.uk/iplayer/[^/]+/[\da-z]{8})"\)', webpage)
        if matches:
            return _playlist_from_matches(matches, ie='BBCCoUk')

        # Look for embedded RUTV player
        rutv_url = RUTVIE._extract_url(webpage)
        if rutv_url:
            return self.url_result(rutv_url, 'RUTV')

        # Look for embedded TVC player
        tvc_url = TVCIE._extract_url(webpage)
        if tvc_url:
            return self.url_result(tvc_url, 'TVC')

        # Look for embedded SportBox player
        sportbox_urls = SportBoxEmbedIE._extract_urls(webpage)
        if sportbox_urls:
            return _playlist_from_matches(sportbox_urls, ie='SportBoxEmbed')

        # Look for embedded XHamster player
        xhamster_urls = XHamsterEmbedIE._extract_urls(webpage)
        if xhamster_urls:
            return _playlist_from_matches(xhamster_urls, ie='XHamsterEmbed')

        # Look for embedded TNAFlixNetwork player
        tnaflix_urls = TNAFlixNetworkEmbedIE._extract_urls(webpage)
        if tnaflix_urls:
            return _playlist_from_matches(tnaflix_urls, ie=TNAFlixNetworkEmbedIE.ie_key())

        # Look for embedded PornHub player
        pornhub_urls = PornHubIE._extract_urls(webpage)
        if pornhub_urls:
            return _playlist_from_matches(pornhub_urls, ie=PornHubIE.ie_key())

        # Look for embedded DrTuber player
        drtuber_urls = DrTuberIE._extract_urls(webpage)
        if drtuber_urls:
            return _playlist_from_matches(drtuber_urls, ie=DrTuberIE.ie_key())

        # Look for embedded RedTube player
        redtube_urls = RedTubeIE._extract_urls(webpage)
        if redtube_urls:
            return _playlist_from_matches(redtube_urls, ie=RedTubeIE.ie_key())

        # Look for embedded Tvigle player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//cloud\.tvigle\.ru/video/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Tvigle')

        # Look for embedded TED player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://embed(?:-ssl)?\.ted\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'TED')

        # Look for embedded Ustream videos
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>http://www\.ustream\.tv/embed/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Ustream')

        # Look for embedded arte.tv player
        mobj = re.search(
            r'<(?:script|iframe) [^>]*?src="(?P<url>http://www\.arte\.tv/(?:playerv2/embed|arte_vp/index)[^"]+)"',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'ArteTVEmbed')

        # Look for embedded francetv player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?://)?embed\.francetv\.fr/\?ue=.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for embedded smotri.com player
        smotri_url = SmotriIE._extract_url(webpage)
        if smotri_url:
            return self.url_result(smotri_url, 'Smotri')

        # Look for embedded Myvi.ru player
        myvi_url = MyviIE._extract_url(webpage)
        if myvi_url:
            return self.url_result(myvi_url)

        # Look for embedded soundcloud player
        soundcloud_urls = SoundcloudIE._extract_urls(webpage)
        if soundcloud_urls:
            return _playlist_from_matches(soundcloud_urls, getter=unescapeHTML, ie=SoundcloudIE.ie_key())

        # Look for embedded mtvservices player
        mtvservices_url = MTVServicesEmbeddedIE._extract_url(webpage)
        if mtvservices_url:
            return self.url_result(mtvservices_url, ie='MTVServicesEmbedded')

        # Look for embedded yahoo player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://(?:screen|movies)\.yahoo\.com/.+?\.html\?format=embed)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Yahoo')

        # Look for embedded sbs.com.au player
        mobj = re.search(
            r'''(?x)
            (?:
                <meta\s+property="og:video"\s+content=|
                <iframe[^>]+?src=
            )
            (["\'])(?P<url>https?://(?:www\.)?sbs\.com\.au/ondemand/video/.+?)\1''',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'SBS')

        # Look for embedded Cinchcast player
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://player\.cinchcast\.com/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Cinchcast')

        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>https?://m(?:lb)?\.mlb\.com/shared/video/embed/embed\.html\?.+?)\1',
            webpage)
        if not mobj:
            mobj = re.search(
                r'data-video-link=["\'](?P<url>http://m.mlb.com/video/[^"\']+)',
                webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'MLB')

        mobj = re.search(
            r'<(?:iframe|script)[^>]+?src=(["\'])(?P<url>%s)\1' % CondeNastIE.EMBED_URL,
            webpage)
        if mobj is not None:
            return self.url_result(self._proto_relative_url(mobj.group('url'), scheme='http:'), 'CondeNast')

        mobj = re.search(
            r'<iframe[^>]+src="(?P<url>https?://(?:new\.)?livestream\.com/[^"]+/player[^"]+)"',
            webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Livestream')

        # Look for Zapiks embed
        mobj = re.search(
            r'<iframe[^>]+src="(?P<url>https?://(?:www\.)?zapiks\.fr/index\.php\?.+?)"', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'), 'Zapiks')

        # Look for Kaltura embeds
        kaltura_url = KalturaIE._extract_url(webpage)
        if kaltura_url:
            return self.url_result(smuggle_url(kaltura_url, {'source_url': url}), KalturaIE.ie_key())

        # Look for Eagle.Platform embeds
        eagleplatform_url = EaglePlatformIE._extract_url(webpage)
        if eagleplatform_url:
            return self.url_result(eagleplatform_url, EaglePlatformIE.ie_key())

        # Look for ClipYou (uses Eagle.Platform) embeds
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?P<host>media\.clipyou\.ru)/index/player\?.*\brecord_id=(?P<id>\d+).*"', webpage)
        if mobj is not None:
            return self.url_result('eagleplatform:%(host)s:%(id)s' % mobj.groupdict(), 'EaglePlatform')

        # Look for Pladform embeds
        pladform_url = PladformIE._extract_url(webpage)
        if pladform_url:
            return self.url_result(pladform_url)

        # Look for Videomore embeds
        videomore_url = VideomoreIE._extract_url(webpage)
        if videomore_url:
            return self.url_result(videomore_url)

        # Look for Webcaster embeds
        webcaster_url = WebcasterFeedIE._extract_url(self, webpage)
        if webcaster_url:
            return self.url_result(webcaster_url, ie=WebcasterFeedIE.ie_key())

        # Look for Playwire embeds
        mobj = re.search(
            r'<script[^>]+data-config=(["\'])(?P<url>(?:https?:)?//config\.playwire\.com/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for 5min embeds
        mobj = re.search(
            r'<meta[^>]+property="og:video"[^>]+content="https?://embed\.5min\.com/(?P<id>[0-9]+)/?', webpage)
        if mobj is not None:
            return self.url_result('5min:%s' % mobj.group('id'), 'FiveMin')

        # Look for Crooks and Liars embeds
        mobj = re.search(
            r'<(?:iframe[^>]+src|param[^>]+value)=(["\'])(?P<url>(?:https?:)?//embed\.crooksandliars\.com/(?:embed|v)/.+?)\1', webpage)
        if mobj is not None:
            return self.url_result(mobj.group('url'))

        # Look for NBC Sports VPlayer embeds
        nbc_sports_url = NBCSportsVPlayerIE._extract_url(webpage)
        if nbc_sports_url:
            return self.url_result(nbc_sports_url, 'NBCSportsVPlayer')

        # Look for NBC News embeds
        nbc_news_embed_url = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//www\.nbcnews\.com/widget/video-embed/[^"\']+)\1', webpage)
        if nbc_news_embed_url:
            return self.url_result(nbc_news_embed_url.group('url'), 'NBCNews')

        # Look for Google Drive embeds
        google_drive_url = GoogleDriveIE._extract_url(webpage)
        if google_drive_url:
            return self.url_result(google_drive_url, 'GoogleDrive')

        # Look for UDN embeds
        mobj = re.search(
            r'<iframe[^>]+src="(?P<url>%s)"' % UDNEmbedIE._PROTOCOL_RELATIVE_VALID_URL, webpage)
        if mobj is not None:
            return self.url_result(
                compat_urlparse.urljoin(url, mobj.group('url')), 'UDNEmbed')

        # Look for Senate ISVP iframe
        senate_isvp_url = SenateISVPIE._search_iframe_url(webpage)
        if senate_isvp_url:
            return self.url_result(senate_isvp_url, 'SenateISVP')

        # Look for Dailymotion Cloud videos
        dmcloud_url = DailymotionCloudIE._extract_dmcloud_url(webpage)
        if dmcloud_url:
            return self.url_result(dmcloud_url, 'DailymotionCloud')

        # Look for OnionStudios embeds
        onionstudios_url = OnionStudiosIE._extract_url(webpage)
        if onionstudios_url:
            return self.url_result(onionstudios_url)

        # Look for ViewLift embeds
        viewlift_url = ViewLiftEmbedIE._extract_url(webpage)
        if viewlift_url:
            return self.url_result(viewlift_url)

        # Look for JWPlatform embeds
        jwplatform_url = JWPlatformIE._extract_url(webpage)
        if jwplatform_url:
            return self.url_result(jwplatform_url, 'JWPlatform')

        # Look for Digiteka embeds
        digiteka_url = DigitekaIE._extract_url(webpage)
        if digiteka_url:
            return self.url_result(self._proto_relative_url(digiteka_url), DigitekaIE.ie_key())

        # Look for Arkena embeds
        arkena_url = ArkenaIE._extract_url(webpage)
        if arkena_url:
            return self.url_result(arkena_url, ArkenaIE.ie_key())

        # Look for Piksel embeds
        piksel_url = PikselIE._extract_url(webpage)
        if piksel_url:
            return self.url_result(piksel_url, PikselIE.ie_key())

        # Look for Limelight embeds
        mobj = re.search(r'LimelightPlayer\.doLoad(Media|Channel|ChannelList)\(["\'](?P<id>[a-z0-9]{32})', webpage)
        if mobj:
            lm = {
                'Media': 'media',
                'Channel': 'channel',
                'ChannelList': 'channel_list',
            }
            return self.url_result('limelight:%s:%s' % (
                lm[mobj.group(1)], mobj.group(2)), 'Limelight%s' % mobj.group(1), mobj.group(2))

        mobj = re.search(
            r'''(?sx)
                <object[^>]+class=(["\'])LimelightEmbeddedPlayerFlash\1[^>]*>.*?
                    <param[^>]+
                        name=(["\'])flashVars\2[^>]+
                        value=(["\'])(?:(?!\3).)*mediaId=(?P<id>[a-z0-9]{32})
            ''', webpage)
        if mobj:
            return self.url_result('limelight:media:%s' % mobj.group('id'))

        # Look for AdobeTVVideo embeds
        mobj = re.search(
            r'<iframe[^>]+src=[\'"]((?:https?:)?//video\.tv\.adobe\.com/v/\d+[^"]+)[\'"]',
            webpage)
        if mobj is not None:
            return self.url_result(
                self._proto_relative_url(unescapeHTML(mobj.group(1))),
                'AdobeTVVideo')

        # Look for Vine embeds
        mobj = re.search(
            r'<iframe[^>]+src=[\'"]((?:https?:)?//(?:www\.)?vine\.co/v/[^/]+/embed/(?:simple|postcard))',
            webpage)
        if mobj is not None:
            return self.url_result(
                self._proto_relative_url(unescapeHTML(mobj.group(1))), 'Vine')

        # Look for VODPlatform embeds
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?vod-platform\.net/[eE]mbed/.+?)\1',
            webpage)
        if mobj is not None:
            return self.url_result(
                self._proto_relative_url(unescapeHTML(mobj.group('url'))), 'VODPlatform')

        # Look for Mangomolo embeds
        mobj = re.search(
            r'''(?x)<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?admin\.mangomolo\.com/analytics/index\.php/customers/embed/
                (?:
                    video\?.*?\bid=(?P<video_id>\d+)|
                    index\?.*?\bchannelid=(?P<channel_id>(?:[A-Za-z0-9+/=]|%2B|%2F|%3D)+)
                ).+?)\1''', webpage)
        if mobj is not None:
            info = {
                '_type': 'url_transparent',
                'url': self._proto_relative_url(unescapeHTML(mobj.group('url'))),
                'title': video_title,
                'description': video_description,
                'thumbnail': video_thumbnail,
                'uploader': video_uploader,
            }
            video_id = mobj.group('video_id')
            if video_id:
                info.update({
                    'ie_key': 'MangomoloVideo',
                    'id': video_id,
                })
            else:
                info.update({
                    'ie_key': 'MangomoloLive',
                    'id': mobj.group('channel_id'),
                })
            return info

        # Look for Instagram embeds
        instagram_embed_url = InstagramIE._extract_embed_url(webpage)
        if instagram_embed_url is not None:
            return self.url_result(
                self._proto_relative_url(instagram_embed_url), InstagramIE.ie_key())

        # Look for LiveLeak embeds
        liveleak_url = LiveLeakIE._extract_url(webpage)
        if liveleak_url:
            return self.url_result(liveleak_url, 'LiveLeak')

        # Look for 3Q SDN embeds
        threeqsdn_url = ThreeQSDNIE._extract_url(webpage)
        if threeqsdn_url:
            return {
                '_type': 'url_transparent',
                'ie_key': ThreeQSDNIE.ie_key(),
                'url': self._proto_relative_url(threeqsdn_url),
                'title': video_title,
                'description': video_description,
                'thumbnail': video_thumbnail,
                'uploader': video_uploader,
            }

        # Look for VBOX7 embeds
        vbox7_url = Vbox7IE._extract_url(webpage)
        if vbox7_url:
            return self.url_result(vbox7_url, Vbox7IE.ie_key())

        # Look for DBTV embeds
        dbtv_urls = DBTVIE._extract_urls(webpage)
        if dbtv_urls:
            return _playlist_from_matches(dbtv_urls, ie=DBTVIE.ie_key())

        # Look for Videa embeds
        videa_urls = VideaIE._extract_urls(webpage)
        if videa_urls:
            return _playlist_from_matches(videa_urls, ie=VideaIE.ie_key())

        # Looking for http://schema.org/VideoObject
        json_ld = self._search_json_ld(
            webpage, video_id, default={}, expected_type='VideoObject')
        if json_ld.get('url'):
            info_dict.update({
                'title': video_title or info_dict['title'],
                'description': video_description,
                'thumbnail': video_thumbnail,
                'age_limit': age_limit
            })
            info_dict.update(json_ld)
            return info_dict

        # Look for HTML5 media
        entries = self._parse_html5_media_entries(url, webpage, video_id, m3u8_id='hls')
        if entries:
            for entry in entries:
                entry.update({
                    'id': video_id,
                    'title': video_title,
                })
                self._sort_formats(entry['formats'])
            return self.playlist_result(entries)

        def check_video(vurl):
            if YoutubeIE.suitable(vurl):
                return True
            vpath = compat_urlparse.urlparse(vurl).path
            vext = determine_ext(vpath)
            return '.' in vpath and vext not in ('swf', 'png', 'jpg', 'srt', 'sbv', 'sub', 'vtt', 'ttml', 'js')

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
                .*?
                ['"]?file['"]?\s*:\s*["\'](.*?)["\']''', webpage))
        if not found:
            # Broaden the search a little bit
            found = filter_video(re.findall(r'[^A-Za-z0-9]?(?:file|source)=(http[^\'"&]*)', webpage))
        if not found:
            # Broaden the findall a little bit: JWPlayer JS loader
            found = filter_video(re.findall(
                r'[^A-Za-z0-9]?(?:file|video_url)["\']?:\s*["\'](http(?![^\'"]+\.[0-9]+[\'"])[^\'"]+)["\']', webpage))
        if not found:
            # Flow player
            found = filter_video(re.findall(r'''(?xs)
                flowplayer\("[^"]+",\s*
                    \{[^}]+?\}\s*,
                    \s*\{[^}]+? ["']?clip["']?\s*:\s*\{\s*
                        ["']?url["']?\s*:\s*["']([^"']+)["']
            ''', webpage))
        if not found:
            # Cinerama player
            found = re.findall(
                r"cinerama\.embedPlayer\(\s*\'[^']+\',\s*'([^']+)'", webpage)
        if not found:
            # Try to find twitter cards info
            # twitter:player:stream should be checked before twitter:player since
            # it is expected to contain a raw stream (see
            # https://dev.twitter.com/cards/types/player#On_twitter.com_via_desktop_browser)
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
            REDIRECT_REGEX = r'[0-9]{,2};\s*(?:URL|url)=\'?([^\'"]+)'
            found = re.search(
                r'(?i)<meta\s+(?=(?:[a-z-]+="[^"]+"\s+)*http-equiv="refresh")'
                r'(?:[a-z-]+="[^"]+"\s+)*?content="%s' % REDIRECT_REGEX,
                webpage)
            if not found:
                # Look also in Refresh HTTP header
                refresh_header = head_response.headers.get('Refresh')
                if refresh_header:
                    # In python 2 response HTTP headers are bytestrings
                    if sys.version_info < (3, 0) and isinstance(refresh_header, str):
                        refresh_header = refresh_header.decode('iso-8859-1')
                    found = re.search(REDIRECT_REGEX, refresh_header)
            if found:
                new_url = compat_urlparse.urljoin(url, unescapeHTML(found.group(1)))
                self.report_following_redirect(new_url)
                return {
                    '_type': 'url',
                    'url': new_url,
                }

        if not found:
            # twitter:player is a https URL to iframe player that may or may not
            # be supported by youtube-dl thus this is checked the very last (see
            # https://dev.twitter.com/cards/types/player#On_twitter.com_via_desktop_browser)
            embed_url = self._html_search_meta('twitter:player', webpage, default=None)
            if embed_url:
                return self.url_result(embed_url)

        if not found:
            raise UnsupportedError(url)

        entries = []
        for video_url in orderedSet(found):
            video_url = unescapeHTML(video_url)
            video_url = video_url.replace('\\/', '/')
            video_url = compat_urlparse.urljoin(url, video_url)
            video_id = compat_urllib_parse_unquote(os.path.basename(video_url))

            # Sometimes, jwplayer extraction will result in a YouTube URL
            if YoutubeIE.suitable(video_url):
                entries.append(self.url_result(video_url, 'Youtube'))
                continue

            # here's a fun little line of code for you:
            video_id = os.path.splitext(video_id)[0]

            entry_info_dict = {
                'id': video_id,
                'uploader': video_uploader,
                'title': video_title,
                'age_limit': age_limit,
            }

            ext = determine_ext(video_url)
            if ext == 'smil':
                entry_info_dict['formats'] = self._extract_smil_formats(video_url, video_id)
            elif ext == 'xspf':
                return self.playlist_result(self._extract_xspf_playlist(video_url, video_id), video_id)
            elif ext == 'm3u8':
                entry_info_dict['formats'] = self._extract_m3u8_formats(video_url, video_id, ext='mp4')
            elif ext == 'mpd':
                entry_info_dict['formats'] = self._extract_mpd_formats(video_url, video_id)
            elif ext == 'f4m':
                entry_info_dict['formats'] = self._extract_f4m_formats(video_url, video_id)
            elif re.search(r'(?i)\.(?:ism|smil)/manifest', video_url) and video_url != url:
                # Just matching .ism/manifest is not enough to be reliably sure
                # whether it's actually an ISM manifest or some other streaming
                # manifest since there are various streaming URL formats
                # possible (see [1]) as well as some other shenanigans like
                # .smil/manifest URLs that actually serve an ISM (see [2]) and
                # so on.
                # Thus the most reasonable way to solve this is to delegate
                # to generic extractor in order to look into the contents of
                # the manifest itself.
                # 1. https://azure.microsoft.com/en-us/documentation/articles/media-services-deliver-content-overview/#streaming-url-formats
                # 2. https://svs.itworkscdn.net/lbcivod/smil:itwfcdn/lbci/170976.smil/Manifest
                entry_info_dict = self.url_result(
                    smuggle_url(video_url, {'to_generic': True}),
                    GenericIE.ie_key())
            else:
                entry_info_dict['url'] = video_url

            if entry_info_dict.get('formats'):
                self._sort_formats(entry_info_dict['formats'])

            entries.append(entry_info_dict)

        if len(entries) == 1:
            return entries[0]
        else:
            for num, e in enumerate(entries, start=1):
                # 'url' results don't have a title
                if e.get('title') is not None:
                    e['title'] = '%s (%d)' % (e['title'], num)
            return {
                '_type': 'playlist',
                'entries': entries,
            }
