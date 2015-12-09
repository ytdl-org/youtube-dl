# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    determine_ext,
    int_or_none,
    strip_jsonp,
    unified_strdate,
    US_RATINGS,
)


class PBSIE(InfoExtractor):
    _STATIONS = (
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # http://aptv.org/
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # http://www.gpb.org/
        ('mpbonline.org', 'Mississippi Public Broadcasting (WMPN)'),  # http://www.mpbonline.org
        ('wnpt.org', 'Nashville Public Television (WNPT)'),  # http://www.wnpt.org
        ('wfsu.org', 'WFSU-TV (WFSU)'),  # http://wfsu.org/
        ('wsre.org', 'WSRE (WSRE)'),  # http://www.wsre.org
        ('wtcitv.org', 'WTCI (WTCI)'),  # http://www.wtcitv.org
        ('pba.org', 'WPBA/Channel 30 (WPBA)'),  # http://pba.org/
        ('alaskapublic.org', 'Alaska Public Media (KAKM)'),  # http://alaskapublic.org/kakm
        ('kuac.org', 'KUAC (KUAC)'),  # http://kuac.org/kuac-tv/
        ('ktoo.org', '360 North (KTOO)'),  # http://www.ktoo.org/
        ('azpm.org', 'KUAT 6 (KUAT)'),  # http://www.azpm.org/
        ('azpbs.org', 'Arizona PBS (KAET)'),  # http://www.azpbs.org
        ('newmexicopbs.org', 'KNME-TV/Channel 5 (KNME)'),  # http://www.newmexicopbs.org/
        ('vegaspbs.org', 'Vegas PBS (KLVX)'),  # http://vegaspbs.org/
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # http://www.aetn.org/
        ('ket.org', 'KET (WKLE)'),  # http://www.ket.org/
        ('wkno.org', 'WKNO/Channel 10 (WKNO)'),  # http://www.wkno.org/
        ('lpb.org', 'LPB/LOUISIANA PUBLIC BROADCASTING (WLPB)'),  # http://www.lpb.org/
        ('oeta.tv', 'OETA (KETA)'),  # http://www.oeta.tv
        ('optv.org', 'Ozarks Public Television (KOZK)'),  # http://www.optv.org/
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # http://www.wsiu.org/
        ('keet.org', 'KEET TV (KEET)'),  # http://www.keet.org
        ('kixe.org', 'KIXE/Channel 9 (KIXE)'),  # http://kixe.org/
        ('kpbs.org', 'KPBS San Diego (KPBS)'),  # http://www.kpbs.org/
        ('kqed.org', 'KQED (KQED)'),  # http://www.kqed.org
        ('kvie.org', 'KVIE Public Television (KVIE)'),  # http://www.kvie.org
        ('pbssocal.org', 'PBS SoCal/KOCE (KOCE)'),  # http://www.pbssocal.org/
        ('valleypbs.org', 'ValleyPBS (KVPT)'),  # http://www.valleypbs.org/
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # http://cptv.org
        ('knpb.org', 'KNPB Channel 5 (KNPB)'),  # http://www.knpb.org/
        ('soptv.org', 'SOPTV (KSYS)'),  # http://www.soptv.org
        ('klcs.org', 'KLCS/Channel 58 (KLCS)'),  # http://www.klcs.org
        ('krcb.org', 'KRCB Television & Radio (KRCB)'),  # http://www.krcb.org
        ('kvcr.org', 'KVCR TV/DT/FM :: Vision for the Future (KVCR)'),  # http://kvcr.org
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # http://www.rmpbs.org
        ('kenw.org', 'KENW-TV3 (KENW)'),  # http://www.kenw.org
        ('kued.org', 'KUED Channel 7 (KUED)'),  # http://www.kued.org
        ('wyomingpbs.org', 'Wyoming PBS (KCWC)'),  # http://www.wyomingpbs.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # http://www.cpt12.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # http://www.kbyutv.org/
        ('thirteen.org', 'Thirteen/WNET New York (WNET)'),  # http://www.thirteen.org
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # http://wgbh.org
        ('wgby.org', 'WGBY (WGBY)'),  # http://www.wgby.org
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # http://www.njtvonline.org/
        ('ripbs.org', 'Rhode Island PBS (WSBE)'),  # http://www.ripbs.org/home/
        ('wliw.org', 'WLIW21 (WLIW)'),  # http://www.wliw.org/
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # http://www.mpt.org
        ('weta.org', 'WETA Television and Radio (WETA)'),  # http://www.weta.org
        ('whyy.org', 'WHYY (WHYY)'),  # http://www.whyy.org
        ('wlvt.org', 'PBS 39 (WLVT)'),  # http://www.wlvt.org/
        ('wvpt.net', 'WVPT - Your Source for PBS and More! (WVPT)'),  # http://www.wvpt.net
        ('whut.org', 'Howard University Television (WHUT)'),  # http://www.whut.org
        ('wedu.org', 'WEDU PBS (WEDU)'),  # http://www.wedu.org
        ('wgcu.org', 'WGCU Public Media (WGCU)'),  # http://www.wgcu.org/
        ('wjct.org', 'WJCT Public Broadcasting (WJCT)'),  # http://www.wjct.org
        ('wpbt2.org', 'WPBT2 (WPBT)'),  # http://www.wpbt2.org
        ('wucftv.org', 'WUCF TV (WUCF)'),  # http://wucftv.org
        ('wuft.org', 'WUFT/Channel 5 (WUFT)'),  # http://www.wuft.org
        ('wxel.org', 'WXEL/Channel 42 (WXEL)'),  # http://www.wxel.org/home/
        ('wlrn.org', 'WLRN/Channel 17 (WLRN)'),  # http://www.wlrn.org/
        ('wusf.org', 'WUSF Public Broadcasting (WUSF)'),  # http://wusf.org/
        ('scetv.org', 'ETV (WRLK)'),  # http://www.scetv.org
        ('unctv.org', 'UNC-TV (WUNC)'),  # http://www.unctv.org/
        ('pbsguam.org', 'PBS Guam (KGTF)'),  # http://www.pbsguam.org/
        ('pbshawaii.org', 'PBS Hawaii - Oceanic Cable Channel 10 (KHET)'),  # http://www.pbshawaii.org/
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # http://idahoptv.org
        ('ksps.org', 'KSPS (KSPS)'),  # http://www.ksps.org/home/
        ('opb.org', 'OPB (KOPB)'),  # http://www.opb.org
        ('kwsu.org', 'KWSU/Channel 10 & KTNW/Channel 31 (KWSU)'),  # http://www.kwsu.org
        ('illinois.edu', 'WILL-TV (WILL)'),  # http://will.illinois.edu/
        ('wsec.tv', 'Network Knowledge - WSEC/Springfield (WSEC)'),  # http://www.wsec.tv
        ('wttw.com', 'WTTW11 (WTTW)'),  # http://www.wttw.com/
        ('wtvp.org', 'WTVP & WTVP.org, Public Media for Central Illinois (WTVP)'),  # http://www.wtvp.org/
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # http://www.iptv.org/
        ('ninenet.org', 'Nine Network (KETC)'),  # http://www.ninenet.org
        ('wfwa.org', 'PBS39 Fort Wayne (WFWA)'),  # http://wfwa.org/
        ('wfyi.org', 'WFYI Indianapolis (WFYI)'),  # http://www.wfyi.org
        ('mptv.org', 'Milwaukee Public Television (WMVS)'),  # http://www.mptv.org
        ('wnin.org', 'WNIN (WNIN)'),  # http://www.wnin.org/
        ('wnit.org', 'WNIT Public Television (WNIT)'),  # http://www.wnit.org/
        ('wpt.org', 'WPT (WPNE)'),  # http://www.wpt.org/
        ('wvut.org', 'WVUT/Channel 22 (WVUT)'),  # http://wvut.org/
        ('weiu.net', 'WEIU/Channel 51 (WEIU)'),  # http://www.weiu.net
        ('wqpt.org', 'WQPT-TV (WQPT)'),  # http://www.wqpt.org
        ('wycc.org', 'WYCC PBS Chicago (WYCC)'),  # http://www.wycc.org
        ('lakeshorepublicmedia.org', 'Lakeshore Public Television (WYIN)'),  # http://lakeshorepublicmedia.org/
        ('wipb.org', 'WIPB-TV (WIPB)'),  # http://wipb.org
        ('indianapublicmedia.org', 'WTIU (WTIU)'),  # http://indianapublicmedia.org/tv/
        ('cetconnect.org', 'CET  (WCET)'),  # http://www.cetconnect.org
        ('thinktv.org', 'ThinkTVNetwork (WPTD)'),  # http://www.thinktv.org
        ('wbgu.org', 'WBGU-TV (WBGU)'),  # http://wbgu.org
        ('wgvu.org', 'WGVU TV (WGVU)'),  # http://www.wgvu.org/
        ('netnebraska.org', 'NET1 (KUON)'),  # http://netnebraska.org
        ('pioneer.org', 'Pioneer Public Television (KWCM)'),  # http://www.pioneer.org
        ('sdpb.org', 'SDPB Television (KUSD)'),  # http://www.sdpb.org
        ('tpt.org', 'TPT (KTCA)'),  # http://www.tpt.org
        ('ksmq.org', 'KSMQ (KSMQ)'),  # http://www.ksmq.org/
        ('kpts.org', 'KPTS/Channel 8 (KPTS)'),  # http://www.kpts.org/
        ('ktwu.org', 'KTWU/Channel 11 (KTWU)'),  # http://ktwu.org
        ('shptv.org', 'Smoky Hills Public Television (KOOD)'),  # http://www.shptv.org
        ('kcpt.org', 'KCPT Kansas City Public Television (KCPT)'),  # http://kcpt.org/
        ('blueridgepbs.org', 'Blue Ridge PBS (WBRA)'),  # http://www.blueridgepbs.org/
        ('easttennesseepbs.org', 'East Tennessee PBS (WSJK)'),  # http://easttennesseepbs.org
        ('wcte.org', 'WCTE-TV (WCTE)'),  # http://www.wcte.org
        ('wljt.org', 'WLJT, Channel 11 (WLJT)'),  # http://wljt.org/
        ('wosu.org', 'WOSU TV (WOSU)'),  # http://wosu.org/
        ('woub.org', 'WOUB/WOUC (WOUB)'),  # http://woub.org/tv/index.php?section=5
        ('wvpublic.org', 'WVPB (WVPB)'),  # http://wvpublic.org/
        ('wkyupbs.org', 'WKYU-PBS (WKYU)'),  # http://www.wkyupbs.org
        ('wyes.org', 'WYES-TV/New Orleans (WYES)'),  # http://www.wyes.org
        ('kera.org', 'KERA 13 (KERA)'),  # http://www.kera.org/
        ('mpbn.net', 'MPBN (WCBB)'),  # http://www.mpbn.net/
        ('mountainlake.org', 'Mountain Lake PBS (WCFE)'),  # http://www.mountainlake.org/
        ('nhptv.org', 'NHPTV (WENH)'),  # http://nhptv.org/
        ('vpt.org', 'Vermont PBS (WETK)'),  # http://www.vpt.org
        ('witf.org', 'witf (WITF)'),  # http://www.witf.org
        ('wqed.org', 'WQED Multimedia (WQED)'),  # http://www.wqed.org/
        ('wmht.org', 'WMHT Educational Telecommunications (WMHT)'),  # http://www.wmht.org/home/
        ('deltabroadcasting.org', 'Q-TV (WDCQ)'),  # http://www.deltabroadcasting.org
        ('dptv.org', 'WTVS Detroit Public TV (WTVS)'),  # http://www.dptv.org/
        ('wcmu.org', 'CMU Public Television (WCMU)'),  # http://www.wcmu.org
        ('wkar.org', 'WKAR-TV (WKAR)'),  # http://wkar.org/
        ('nmu.edu', 'WNMU-TV Public TV 13 (WNMU)'),  # http://wnmutv.nmu.edu
        ('wdse.org', 'WDSE - WRPT (WDSE)'),  # http://www.wdse.org/
        ('wgte.org', 'WGTE TV (WGTE)'),  # http://www.wgte.org
        ('lakelandptv.org', 'Lakeland Public Television (KAWE)'),  # http://www.lakelandptv.org
        ('prairiepublic.org', 'PRAIRIE PUBLIC (KFME)'),  # http://www.prairiepublic.org/
        ('kmos.org', 'KMOS-TV - Channels 6.1, 6.2 and 6.3 (KMOS)'),  # http://www.kmos.org/
        ('montanapbs.org', 'MontanaPBS (KUSM)'),  # http://montanapbs.org
        ('krwg.org', 'KRWG/Channel 22 (KRWG)'),  # http://www.krwg.org
        ('panhandlepbs.org', 'KACV (KACV)'),  # http://www.panhandlepbs.org/home/
        ('kcostv.org', 'KCOS/Channel 13 (KCOS)'),  # www.kcostv.org
        ('wcny.org', 'WCNY/Channel 24 (WCNY)'),  # http://www.wcny.org
        ('wned.org', 'WNED (WNED)'),  # http://www.wned.org/
        ('wpbstv.org', 'WPBS (WPBS)'),  # http://www.wpbstv.org
        ('wskg.org', 'WSKG Public TV (WSKG)'),  # http://wskg.org
        ('wxxi.org', 'WXXI (WXXI)'),  # http://wxxi.org
        ('wpsu.org', 'WPSU (WPSU)'),  # http://www.wpsu.org
        ('wqln.org', 'WQLN/Channel 54 (WQLN)'),  # http://www.wqln.org
        ('wvia.org', 'WVIA Public Media Studios (WVIA)'),  # http://www.wvia.org/
        ('wtvi.org', 'WTVI (WTVI)'),  # http://www.wtvi.org/
        ('whro.org', 'WHRO (WHRO)'),  # http://whro.org
        ('westernreservepublicmedia.org', 'Western Reserve PBS (WNEO)'),  # http://www.WesternReservePublicMedia.org/
        ('wviz.org', 'WVIZ/PBS ideastream (WVIZ)'),  # http://www.wviz.org/
        ('kcts9.org', 'KCTS 9 (KCTS)'),  # http://kcts9.org/
        ('basinpbs.org', 'Basin PBS (KPBT)'),  # http://www.basinpbs.org
        ('houstonpublicmedia.org', 'KUHT / Channel 8 (KUHT)'),  # http://www.houstonpublicmedia.org/
        ('tamu.edu', 'KAMU - TV (KAMU)'),  # http://KAMU.tamu.edu
        ('kedt.org', 'KEDT/Channel 16 (KEDT)'),  # http://www.kedt.org
        ('klrn.org', 'KLRN (KLRN)'),  # http://www.klrn.org
        ('klru.org', 'KLRU (KLRU)'),  # http://www.klru.org
        ('kmbh.org', 'KMBH-TV (KMBH)'),  # http://www.kmbh.org
        ('knct.org', 'KNCT (KNCT)'),  # http://www.knct.org
        ('ktxt.org', 'KTTZ-TV (KTXT)'),  # http://www.ktxt.org
        ('wtjx.org', 'WTJX Channel 12 (WTJX)'),  # http://www.wtjx.org/
        ('ideastations.org', 'WCVE PBS (WCVE)'),  # http://ideastations.org/
        ('kbtc.org', 'KBTC Public Television (KBTC)'),  # http://kbtc.org
    )

    IE_NAME = 'pbs'
    IE_DESC = 'Public Broadcasting Service (PBS) and member stations: %s' % ', '.join(list(zip(*_STATIONS))[1])

    _VALID_URL = r'''(?x)https?://
        (?:
           # Direct video URL
           (?:videos?|watch)\.(?:%s)/(?:viralplayer|video)/(?P<id>[0-9]+)/? |
           # Article with embedded player (or direct video)
           (?:www\.)?pbs\.org/(?:[^/]+/){2,5}(?P<presumptive_id>[^/]+?)(?:\.html)?/?(?:$|[?\#]) |
           # Player
           (?:video|player)\.pbs\.org/(?:widget/)?partnerplayer/(?P<player_id>[^/]+)/
        )
    ''' % '|'.join(list(zip(*_STATIONS))[0])

    _TESTS = [
        {
            'url': 'http://www.pbs.org/tpt/constitution-usa-peter-sagal/watch/a-more-perfect-union/',
            'md5': 'ce1888486f0908d555a8093cac9a7362',
            'info_dict': {
                'id': '2365006249',
                'ext': 'mp4',
                'title': 'Constitution USA with Peter Sagal - A More Perfect Union',
                'description': 'md5:ba0c207295339c8d6eced00b7c363c6a',
                'duration': 3190,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://www.pbs.org/wgbh/pages/frontline/losing-iraq/',
            'md5': '143c98aa54a346738a3d78f54c925321',
            'info_dict': {
                'id': '2365297690',
                'ext': 'mp4',
                'title': 'FRONTLINE - Losing Iraq',
                'description': 'md5:f5bfbefadf421e8bb8647602011caf8e',
                'duration': 5050,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            }
        },
        {
            'url': 'http://www.pbs.org/newshour/bb/education-jan-june12-cyberschools_02-23/',
            'md5': 'b19856d7f5351b17a5ab1dc6a64be633',
            'info_dict': {
                'id': '2201174722',
                'ext': 'mp4',
                'title': 'PBS NewsHour - Cyber Schools Gain Popularity, but Quality Questions Persist',
                'description': 'md5:5871c15cba347c1b3d28ac47a73c7c28',
                'duration': 801,
            },
        },
        {
            'url': 'http://www.pbs.org/wnet/gperf/dudamel-conducts-verdi-requiem-hollywood-bowl-full-episode/3374/',
            'md5': 'c62859342be2a0358d6c9eb306595978',
            'info_dict': {
                'id': '2365297708',
                'ext': 'mp4',
                'description': 'md5:68d87ef760660eb564455eb30ca464fe',
                'title': 'Great Performances - Dudamel Conducts Verdi Requiem at the Hollywood Bowl - Full',
                'duration': 6559,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://www.pbs.org/wgbh/nova/earth/killer-typhoon.html',
            'md5': '908f3e5473a693b266b84e25e1cf9703',
            'info_dict': {
                'id': '2365160389',
                'display_id': 'killer-typhoon',
                'ext': 'mp4',
                'description': 'md5:c741d14e979fc53228c575894094f157',
                'title': 'NOVA - Killer Typhoon',
                'duration': 3172,
                'thumbnail': 're:^https?://.*\.jpg$',
                'upload_date': '20140122',
                'age_limit': 10,
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://www.pbs.org/wgbh/pages/frontline/united-states-of-secrets/',
            'info_dict': {
                'id': 'united-states-of-secrets',
            },
            'playlist_count': 2,
        },
        {
            'url': 'http://www.pbs.org/wgbh/americanexperience/films/death/player/',
            'info_dict': {
                'id': '2276541483',
                'display_id': 'player',
                'ext': 'mp4',
                'title': 'American Experience - Death and the Civil War, Chapter 1',
                'description': 'American Experience, TV’s most-watched history series, brings to life the compelling stories from our past that inform our understanding of the world today.',
                'duration': 682,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://video.pbs.org/video/2365367186/',
            'info_dict': {
                'id': '2365367186',
                'display_id': '2365367186',
                'ext': 'mp4',
                'title': 'To Catch A Comet - Full Episode',
                'description': 'On November 12, 2014, billions of kilometers from Earth, spacecraft orbiter Rosetta and lander Philae did what no other had dared to attempt \u2014 land on the volatile surface of a comet as it zooms around the sun at 67,000 km/hr. The European Space Agency hopes this mission can help peer into our past and unlock secrets of our origins.',
                'duration': 3342,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
            'skip': 'Expired',
        },
        {
            # Video embedded in iframe containing angle brackets as attribute's value (e.g.
            # "<iframe style='position: absolute;<br />\ntop: 0; left: 0;' ...", see
            # https://github.com/rg3/youtube-dl/issues/7059)
            'url': 'http://www.pbs.org/food/features/a-chefs-life-season-3-episode-5-prickly-business/',
            'info_dict': {
                'id': '2365546844',
                'display_id': 'a-chefs-life-season-3-episode-5-prickly-business',
                'ext': 'mp4',
                'title': "A Chef's Life - Season 3, Ep. 5: Prickly Business",
                'description': 'md5:61db2ddf27c9912f09c241014b118ed1',
                'duration': 1480,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            # Frontline video embedded via flp2012.js
            'url': 'http://www.pbs.org/wgbh/pages/frontline/the-atomic-artists',
            'info_dict': {
                'id': '2070868960',
                'display_id': 'the-atomic-artists',
                'ext': 'mp4',
                'title': 'FRONTLINE - The Atomic Artists',
                'description': 'md5:f5bfbefadf421e8bb8647602011caf8e',
                'duration': 723,
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                'skip_download': True,  # requires ffmpeg
            },
        },
        {
            'url': 'http://player.pbs.org/widget/partnerplayer/2365297708/?start=0&end=0&chapterbar=false&endscreen=false&topbar=true',
            'only_matching': True,
        },
        {
            'url': 'http://watch.knpb.org/video/2365616055/',
            'only_matching': True,
        }
    ]
    _ERRORS = {
        101: 'We\'re sorry, but this video is not yet available.',
        403: 'We\'re sorry, but this video is not available in your region due to right restrictions.',
        404: 'We are experiencing technical difficulties that are preventing us from playing the video at this time. Please check back again soon.',
        410: 'This video has expired and is no longer available for online streaming.',
    }

    def _extract_webpage(self, url):
        mobj = re.match(self._VALID_URL, url)

        presumptive_id = mobj.group('presumptive_id')
        display_id = presumptive_id
        if presumptive_id:
            webpage = self._download_webpage(url, display_id)

            upload_date = unified_strdate(self._search_regex(
                r'<input type="hidden" id="air_date_[0-9]+" value="([^"]+)"',
                webpage, 'upload date', default=None))

            # tabbed frontline videos
            tabbed_videos = re.findall(
                r'<div[^>]+class="videotab[^"]*"[^>]+vid="(\d+)"', webpage)
            if tabbed_videos:
                return tabbed_videos, presumptive_id, upload_date

            MEDIA_ID_REGEXES = [
                r"div\s*:\s*'videoembed'\s*,\s*mediaid\s*:\s*'(\d+)'",  # frontline video embed
                r'class="coveplayerid">([^<]+)<',                       # coveplayer
                r'<section[^>]+data-coveid="(\d+)"',                    # coveplayer from http://www.pbs.org/wgbh/frontline/film/real-csi/
                r'<input type="hidden" id="pbs_video_id_[0-9]+" value="([0-9]+)"/>',  # jwplayer
            ]

            media_id = self._search_regex(
                MEDIA_ID_REGEXES, webpage, 'media ID', fatal=False, default=None)
            if media_id:
                return media_id, presumptive_id, upload_date

            # Fronline video embedded via flp
            video_id = self._search_regex(
                r'videoid\s*:\s*"([\d+a-z]{7,})"', webpage, 'videoid', default=None)
            if video_id:
                # pkg_id calculation is reverse engineered from
                # http://www.pbs.org/wgbh/pages/frontline/js/flp2012.js
                prg_id = self._search_regex(
                    r'videoid\s*:\s*"([\d+a-z]{7,})"', webpage, 'videoid')[7:]
                if 'q' in prg_id:
                    prg_id = prg_id.split('q')[1]
                prg_id = int(prg_id, 16)
                getdir = self._download_json(
                    'http://www.pbs.org/wgbh/pages/frontline/.json/getdir/getdir%d.json' % prg_id,
                    presumptive_id, 'Downloading getdir JSON',
                    transform_source=strip_jsonp)
                return getdir['mid'], presumptive_id, upload_date

            for iframe in re.findall(r'(?s)<iframe(.+?)></iframe>', webpage):
                url = self._search_regex(
                    r'src=(["\'])(?P<url>.+?partnerplayer.+?)\1', iframe,
                    'player URL', default=None, group='url')
                if url:
                    break

            mobj = re.match(self._VALID_URL, url)

        player_id = mobj.group('player_id')
        if not display_id:
            display_id = player_id
        if player_id:
            player_page = self._download_webpage(
                url, display_id, note='Downloading player page',
                errnote='Could not download player page')
            video_id = self._search_regex(
                r'<div\s+id="video_([0-9]+)"', player_page, 'video ID')
        else:
            video_id = mobj.group('id')
            display_id = video_id

        return video_id, display_id, None

    def _real_extract(self, url):
        video_id, display_id, upload_date = self._extract_webpage(url)

        if isinstance(video_id, list):
            entries = [self.url_result(
                'http://video.pbs.org/video/%s' % vid_id, 'PBS', vid_id)
                for vid_id in video_id]
            return self.playlist_result(entries, display_id)

        info = self._download_json(
            'http://player.pbs.org/videoInfo/%s?format=json&type=partner' % video_id,
            display_id)

        formats = []
        for encoding_name in ('recommended_encoding', 'alternate_encoding'):
            redirect = info.get(encoding_name)
            if not redirect:
                continue
            redirect_url = redirect.get('url')
            if not redirect_url:
                continue

            redirect_info = self._download_json(
                redirect_url + '?format=json', display_id,
                'Downloading %s video url info' % encoding_name)

            if redirect_info['status'] == 'error':
                raise ExtractorError(
                    '%s said: %s' % (
                        self.IE_NAME,
                        self._ERRORS.get(redirect_info['http_code'], redirect_info['message'])),
                    expected=True)

            format_url = redirect_info.get('url')
            if not format_url:
                continue

            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, display_id, 'mp4', preference=1, m3u8_id='hls'))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': redirect.get('eeid'),
                })
        self._sort_formats(formats)

        rating_str = info.get('rating')
        if rating_str is not None:
            rating_str = rating_str.rpartition('-')[2]
        age_limit = US_RATINGS.get(rating_str)

        subtitles = {}
        closed_captions_url = info.get('closed_captions_url')
        if closed_captions_url:
            subtitles['en'] = [{
                'ext': 'ttml',
                'url': closed_captions_url,
            }]

        # info['title'] is often incomplete (e.g. 'Full Episode', 'Episode 5', etc)
        # Try turning it to 'program - title' naming scheme if possible
        alt_title = info.get('program', {}).get('title')
        if alt_title:
            info['title'] = alt_title + ' - ' + re.sub(r'^' + alt_title + '[\s\-:]+', '', info['title'])

        return {
            'id': video_id,
            'display_id': display_id,
            'title': info['title'],
            'description': info['program'].get('description'),
            'thumbnail': info.get('image_url'),
            'duration': int_or_none(info.get('duration')),
            'age_limit': age_limit,
            'upload_date': upload_date,
            'formats': formats,
            'subtitles': subtitles,
        }
