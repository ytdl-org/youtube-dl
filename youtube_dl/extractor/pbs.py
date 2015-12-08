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
        ('pbs.org', 'PBS: Public Broadcasting Service'),  # http://www.pbs.org/
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # AL, http://aptv.org/
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # AL, http://www.gpb.org/
        ('mpbonline.org', 'Mississippi Public Broadcasting (WMPN)'),  # AL, http://www.mpbonline.org
        ('wnpt.org', 'Nashville Public Television (WNPT)'),  # AL, http://www.wnpt.org
        ('wfsu.org', 'WFSU-TV (WFSU)'),  # AL, http://wfsu.org/
        ('wsre.org', 'WSRE (WSRE)'),  # AL, http://www.wsre.org
        ('wtcitv.org', 'WTCI (WTCI)'),  # AL, http://www.wtcitv.org
        ('pba.org', 'WPBA/Channel 30 (WPBA)'),  # AL, http://pba.org/
        ('alaskapublic.org', 'Alaska Public Media (KAKM)'),  # AK, http://alaskapublic.org/kakm
        ('kuac.org', 'KUAC (KUAC)'),  # AK, http://kuac.org/kuac-tv/
        ('ktoo.org', '360 North (KTOO)'),  # AK, http://www.ktoo.org/
        ('azpm.org', 'KUAT 6 (KUAT)'),  # AZ, http://www.azpm.org/
        ('azpbs.org', 'Arizona PBS (KAET)'),  # AZ, http://www.azpbs.org
        ('newmexicopbs.org', 'KNME-TV/Channel 5 (KNME)'),  # AZ, http://www.newmexicopbs.org/
        ('vegaspbs.org', 'Vegas PBS (KLVX)'),  # AZ, http://vegaspbs.org/
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # AR, http://www.aetn.org/
        ('ket.org', 'KET (WKLE)'),  # AR, http://www.ket.org/
        ('wkno.org', 'WKNO/Channel 10 (WKNO)'),  # AR, http://www.wkno.org/
        ('lpb.org', 'LPB/LOUISIANA PUBLIC BROADCASTING (WLPB)'),  # AR, http://www.lpb.org/
        ('mpbonline.org', 'Mississippi Public Broadcasting (WMPN)'),  # AR, http://www.mpbonline.org
        ('oeta.tv', 'OETA (KETA)'),  # AR, http://www.oeta.tv
        ('optv.org', 'Ozarks Public Television (KOZK)'),  # AR, http://www.optv.org/
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # AR, http://www.wsiu.org/
        ('keet.org', 'KEET TV (KEET)'),  # CA, http://www.keet.org
        ('kixe.org', 'KIXE/Channel 9 (KIXE)'),  # CA, http://kixe.org/
        ('kpbs.org', 'KPBS San Diego (KPBS)'),  # CA, http://www.kpbs.org/
        ('kqed.org', 'KQED (KQED)'),  # CA, http://www.kqed.org
        ('kvie.org', 'KVIE Public Television (KVIE)'),  # CA, http://www.kvie.org
        ('pbssocal.org', 'PBS SoCal/KOCE (KOCE)'),  # CA, http://www.pbssocal.org/
        ('valleypbs.org', 'ValleyPBS (KVPT)'),  # CA, http://www.valleypbs.org/
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # CA, http://aptv.org/
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # CA, http://cptv.org
        ('azpbs.org', 'Arizona PBS (KAET)'),  # CA, http://www.azpbs.org
        ('knpb.org', 'KNPB Channel 5 (KNPB)'),  # CA, http://www.knpb.org/
        ('soptv.org', 'SOPTV (KSYS)'),  # CA, http://www.soptv.org
        ('klcs.org', 'KLCS/Channel 58 (KLCS)'),  # CA, http://www.klcs.org
        ('krcb.org', 'KRCB Television & Radio (KRCB)'),  # CA, http://www.krcb.org
        ('kvcr.org', 'KVCR TV/DT/FM :: Vision for the Future (KVCR)'),  # CA, http://kvcr.org
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # CO, http://www.rmpbs.org
        ('kenw.org', 'KENW-TV3 (KENW)'),  # CO, http://www.kenw.org
        ('kued.org', 'KUED Channel 7 (KUED)'),  # CO, http://www.kued.org
        ('newmexicopbs.org', 'KNME-TV/Channel 5 (KNME)'),  # CO, http://www.newmexicopbs.org/
        ('wyomingpbs.org', 'Wyoming PBS (KCWC)'),  # CO, http://www.wyomingpbs.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # CO, http://www.cpt12.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # CO, http://www.kbyutv.org/
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # CT, http://cptv.org
        ('thirteen.org', 'Thirteen/WNET New York (WNET)'),  # CT, http://www.thirteen.org
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # CT, http://wgbh.org
        ('wgby.org', 'WGBY (WGBY)'),  # CT, http://www.wgby.org
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # CT, http://www.njtvonline.org/
        ('ripbs.org', 'Rhode Island PBS (WSBE)'),  # CT, http://www.ripbs.org/home/
        ('wliw.org', 'WLIW21 (WLIW)'),  # CT, http://www.wliw.org/
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # DE, http://www.mpt.org
        ('weta.org', 'WETA Television and Radio (WETA)'),  # DE, http://www.weta.org
        ('whyy.org', 'WHYY (WHYY)'),  # DE, http://www.whyy.org
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # DE, http://www.njtvonline.org/
        ('wlvt.org', 'PBS 39 (WLVT)'),  # DE, http://www.wlvt.org/
        ('wliw.org', 'WLIW21 (WLIW)'),  # DE, http://www.wliw.org/
        ('weta.org', 'WETA Television and Radio (WETA)'),  # DC, http://www.weta.org
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # DC, http://www.mpt.org
        ('wvpt.net', 'WVPT - Your Source for PBS and More! (WVPT)'),  # DC, http://www.wvpt.net
        ('whut.org', 'Howard University Television (WHUT)'),  # DC, http://www.whut.org
        ('wedu.org', 'WEDU PBS (WEDU)'),  # FL, http://www.wedu.org
        ('wfsu.org', 'WFSU-TV (WFSU)'),  # FL, http://wfsu.org/
        ('wgcu.org', 'WGCU Public Media (WGCU)'),  # FL, http://www.wgcu.org/
        ('wjct.org', 'WJCT Public Broadcasting (WJCT)'),  # FL, http://www.wjct.org
        ('wpbt2.org', 'WPBT2 (WPBT)'),  # FL, http://www.wpbt2.org
        ('wsre.org', 'WSRE (WSRE)'),  # FL, http://www.wsre.org
        ('wucftv.org', 'WUCF TV (WUCF)'),  # FL, http://wucftv.org
        ('wuft.org', 'WUFT/Channel 5 (WUFT)'),  # FL, http://www.wuft.org
        ('wxel.org', 'WXEL/Channel 42 (WXEL)'),  # FL, http://www.wxel.org/home/
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # FL, http://aptv.org/
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # FL, http://www.gpb.org/
        ('wlrn.org', 'WLRN/Channel 17 (WLRN)'),  # FL, http://www.wlrn.org/
        ('wusf.org', 'WUSF Public Broadcasting (WUSF)'),  # FL, http://wusf.org/
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # FL, http://www.njtvonline.org/
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # GA, http://www.gpb.org/
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # GA, http://aptv.org/
        ('scetv.org', 'ETV (WRLK)'),  # GA, http://www.scetv.org
        ('unctv.org', 'UNC-TV (WUNC)'),  # GA, http://www.unctv.org/
        ('wfsu.org', 'WFSU-TV (WFSU)'),  # GA, http://wfsu.org/
        ('wjct.org', 'WJCT Public Broadcasting (WJCT)'),  # GA, http://www.wjct.org
        ('wtcitv.org', 'WTCI (WTCI)'),  # GA, http://www.wtcitv.org
        ('pba.org', 'WPBA/Channel 30 (WPBA)'),  # GA, http://pba.org/
        ('pbsguam.org', 'PBS Guam (KGTF)'),  # GU, http://www.pbsguam.org/
        ('pbshawaii.org', 'PBS Hawaii - Oceanic Cable Channel 10 (KHET)'),  # HI, http://www.pbshawaii.org/
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # ID, http://idahoptv.org
        ('ksps.org', 'KSPS (KSPS)'),  # ID, http://www.ksps.org/home/
        ('kued.org', 'KUED Channel 7 (KUED)'),  # ID, http://www.kued.org
        ('opb.org', 'OPB (KOPB)'),  # ID, http://www.opb.org
        ('soptv.org', 'SOPTV (KSYS)'),  # ID, http://www.soptv.org
        ('wyomingpbs.org', 'Wyoming PBS (KCWC)'),  # ID, http://www.wyomingpbs.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # ID, http://www.cpt12.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # ID, http://www.kbyutv.org/
        ('kwsu.org', 'KWSU/Channel 10 & KTNW/Channel 31 (KWSU)'),  # ID, http://www.kwsu.org
        ('illinois.edu', 'WILL-TV (WILL)'),  # IL, http://will.illinois.edu/
        ('wsec.tv', 'Network Knowledge - WSEC/Springfield (WSEC)'),  # IL, http://www.wsec.tv
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # IL, http://www.wsiu.org/
        ('wttw.com', 'WTTW11 (WTTW)'),  # IL, http://www.wttw.com/
        ('wtvp.org', 'WTVP & WTVP.org, Public Media for Central Illinois (WTVP)'),  # IL, http://www.wtvp.org/
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # IL, http://www.iptv.org/
        ('ket.org', 'KET (WKLE)'),  # IL, http://www.ket.org/
        ('ninenet.org', 'Nine Network (KETC)'),  # IL, http://www.ninenet.org
        ('wfwa.org', 'PBS39 Fort Wayne (WFWA)'),  # IL, http://wfwa.org/
        ('wfyi.org', 'WFYI Indianapolis (WFYI)'),  # IL, http://www.wfyi.org
        ('mptv.org', 'Milwaukee Public Television (WMVS)'),  # IL, http://www.mptv.org
        ('wnin.org', 'WNIN (WNIN)'),  # IL, http://www.wnin.org/
        ('wnit.org', 'WNIT Public Television (WNIT)'),  # IL, http://www.wnit.org/
        ('wpt.org', 'WPT (WPNE)'),  # IL, http://www.wpt.org/
        ('wvut.org', 'WVUT/Channel 22 (WVUT)'),  # IL, http://wvut.org/
        ('weiu.net', 'WEIU/Channel 51 (WEIU)'),  # IL, http://www.weiu.net
        ('wqpt.org', 'WQPT-TV (WQPT)'),  # IL, http://www.wqpt.org
        ('wycc.org', 'WYCC PBS Chicago (WYCC)'),  # IL, http://www.wycc.org
        ('lakeshorepublicmedia.org', 'Lakeshore Public Television (WYIN)'),  # IL, http://lakeshorepublicmedia.org/
        ('wfwa.org', 'PBS39 Fort Wayne (WFWA)'),  # IN, http://wfwa.org/
        ('wfyi.org', 'WFYI Indianapolis (WFYI)'),  # IN, http://www.wfyi.org
        ('wipb.org', 'WIPB-TV (WIPB)'),  # IN, http://wipb.org
        ('wnin.org', 'WNIN (WNIN)'),  # IN, http://www.wnin.org/
        ('wnit.org', 'WNIT Public Television (WNIT)'),  # IN, http://www.wnit.org/
        ('indianapublicmedia.org', 'WTIU (WTIU)'),  # IN, http://indianapublicmedia.org/tv/
        ('wvut.org', 'WVUT/Channel 22 (WVUT)'),  # IN, http://wvut.org/
        ('cetconnect.org', 'CET  (WCET)'),  # IN, http://www.cetconnect.org
        ('ket.org', 'KET (WKLE)'),  # IN, http://www.ket.org/
        ('thinktv.org', 'ThinkTVNetwork (WPTD)'),  # IN, http://www.thinktv.org
        ('wbgu.org', 'WBGU-TV (WBGU)'),  # IN, http://wbgu.org
        ('wgvu.org', 'WGVU TV (WGVU)'),  # IN, http://www.wgvu.org/
        ('illinois.edu', 'WILL-TV (WILL)'),  # IN, http://will.illinois.edu/
        ('wsec.tv', 'Network Knowledge - WSEC/Springfield (WSEC)'),  # IN, http://www.wsec.tv
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # IN, http://www.wsiu.org/
        ('wttw.com', 'WTTW11 (WTTW)'),  # IN, http://www.wttw.com/
        ('lakeshorepublicmedia.org', 'Lakeshore Public Television (WYIN)'),  # IN, http://lakeshorepublicmedia.org/
        ('weiu.net', 'WEIU/Channel 51 (WEIU)'),  # IN, http://www.weiu.net
        ('wycc.org', 'WYCC PBS Chicago (WYCC)'),  # IN, http://www.wycc.org
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # IA, http://www.iptv.org/
        ('netnebraska.org', 'NET1 (KUON)'),  # IA, http://netnebraska.org
        ('pioneer.org', 'Pioneer Public Television (KWCM)'),  # IA, http://www.pioneer.org
        ('sdpb.org', 'SDPB Television (KUSD)'),  # IA, http://www.sdpb.org
        ('tpt.org', 'TPT (KTCA)'),  # IA, http://www.tpt.org
        ('wsec.tv', 'Network Knowledge - WSEC/Springfield (WSEC)'),  # IA, http://www.wsec.tv
        ('wpt.org', 'WPT (WPNE)'),  # IA, http://www.wpt.org/
        ('ksmq.org', 'KSMQ (KSMQ)'),  # IA, http://www.ksmq.org/
        ('wqpt.org', 'WQPT-TV (WQPT)'),  # IA, http://www.wqpt.org
        ('kpts.org', 'KPTS/Channel 8 (KPTS)'),  # KS, http://www.kpts.org/
        ('ktwu.org', 'KTWU/Channel 11 (KTWU)'),  # KS, http://ktwu.org
        ('shptv.org', 'Smoky Hills Public Television (KOOD)'),  # KS, http://www.shptv.org
        ('kcpt.org', 'KCPT Kansas City Public Television (KCPT)'),  # KS, http://kcpt.org/
        ('netnebraska.org', 'NET1 (KUON)'),  # KS, http://netnebraska.org
        ('oeta.tv', 'OETA (KETA)'),  # KS, http://www.oeta.tv
        ('optv.org', 'Ozarks Public Television (KOZK)'),  # KS, http://www.optv.org/
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # KS, http://www.rmpbs.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # KS, http://www.cpt12.org/
        ('ket.org', 'KET (WKLE)'),  # KY, http://www.ket.org/
        ('blueridgepbs.org', 'Blue Ridge PBS (WBRA)'),  # KY, http://www.blueridgepbs.org/
        ('cetconnect.org', 'CET  (WCET)'),  # KY, http://www.cetconnect.org
        ('easttennesseepbs.org', 'East Tennessee PBS (WSJK)'),  # KY, http://easttennesseepbs.org
        ('wnpt.org', 'Nashville Public Television (WNPT)'),  # KY, http://www.wnpt.org
        ('thinktv.org', 'ThinkTVNetwork (WPTD)'),  # KY, http://www.thinktv.org
        ('wcte.org', 'WCTE-TV (WCTE)'),  # KY, http://www.wcte.org
        ('wljt.org', 'WLJT, Channel 11 (WLJT)'),  # KY, http://wljt.org/
        ('wnin.org', 'WNIN (WNIN)'),  # KY, http://www.wnin.org/
        ('wosu.org', 'WOSU TV (WOSU)'),  # KY, http://wosu.org/
        ('woub.org', 'WOUB/WOUC (WOUB)'),  # KY, http://woub.org/tv/index.php?section=5
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # KY, http://www.wsiu.org/
        ('wvpublic.org', 'WVPB (WVPB)'),  # KY, http://wvpublic.org/
        ('wkyupbs.org', 'WKYU-PBS (WKYU)'),  # KY, http://www.wkyupbs.org
        ('lpb.org', 'LPB/LOUISIANA PUBLIC BROADCASTING (WLPB)'),  # LA, http://www.lpb.org/
        ('wyes.org', 'WYES-TV/New Orleans (WYES)'),  # LA, http://www.wyes.org
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # LA, http://www.aetn.org/
        ('kera.org', 'KERA 13 (KERA)'),  # LA, http://www.kera.org/
        ('mpbonline.org', 'Mississippi Public Broadcasting (WMPN)'),  # LA, http://www.mpbonline.org
        ('mpbn.net', 'MPBN (WCBB)'),  # ME, http://www.mpbn.net/
        ('mountainlake.org', 'Mountain Lake PBS (WCFE)'),  # ME, http://www.mountainlake.org/
        ('nhptv.org', 'NHPTV (WENH)'),  # ME, http://nhptv.org/
        ('vpt.org', 'Vermont PBS (WETK)'),  # ME, http://www.vpt.org
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # ME, http://wgbh.org
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # MD, http://www.mpt.org
        ('thirteen.org', 'Thirteen/WNET New York (WNET)'),  # MD, http://www.thirteen.org
        ('weta.org', 'WETA Television and Radio (WETA)'),  # MD, http://www.weta.org
        ('whyy.org', 'WHYY (WHYY)'),  # MD, http://www.whyy.org
        ('witf.org', 'witf (WITF)'),  # MD, http://www.witf.org
        ('wqed.org', 'WQED Multimedia (WQED)'),  # MD, http://www.wqed.org/
        ('wvpublic.org', 'WVPB (WVPB)'),  # MD, http://wvpublic.org/
        ('wvpt.net', 'WVPT - Your Source for PBS and More! (WVPT)'),  # MD, http://www.wvpt.net
        ('whut.org', 'Howard University Television (WHUT)'),  # MD, http://www.whut.org
        ('wliw.org', 'WLIW21 (WLIW)'),  # MD, http://www.wliw.org/
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # MA, http://wgbh.org
        ('wgby.org', 'WGBY (WGBY)'),  # MA, http://www.wgby.org
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # MA, http://cptv.org
        ('nhptv.org', 'NHPTV (WENH)'),  # MA, http://nhptv.org/
        ('vpt.org', 'Vermont PBS (WETK)'),  # MA, http://www.vpt.org
        ('wmht.org', 'WMHT Educational Telecommunications (WMHT)'),  # MA, http://www.wmht.org/home/
        ('ripbs.org', 'Rhode Island PBS (WSBE)'),  # MA, http://www.ripbs.org/home/
        ('deltabroadcasting.org', 'Q-TV (WDCQ)'),  # MI, http://www.deltabroadcasting.org
        ('dptv.org', 'WTVS Detroit Public TV (WTVS)'),  # MI, http://www.dptv.org/
        ('wcmu.org', 'CMU Public Television (WCMU)'),  # MI, http://www.wcmu.org
        ('wgvu.org', 'WGVU TV (WGVU)'),  # MI, http://www.wgvu.org/
        ('wkar.org', 'WKAR-TV (WKAR)'),  # MI, http://wkar.org/
        ('nmu.edu', 'WNMU-TV Public TV 13 (WNMU)'),  # MI, http://wnmutv.nmu.edu
        ('wdse.org', 'WDSE - WRPT (WDSE)'),  # MI, http://www.wdse.org/
        ('wbgu.org', 'WBGU-TV (WBGU)'),  # MI, http://wbgu.org
        ('wgte.org', 'WGTE TV (WGTE)'),  # MI, http://www.wgte.org
        ('wnit.org', 'WNIT Public Television (WNIT)'),  # MI, http://www.wnit.org/
        ('wpt.org', 'WPT (WPNE)'),  # MI, http://www.wpt.org/
        ('wttw.com', 'WTTW11 (WTTW)'),  # MI, http://www.wttw.com/
        ('wycc.org', 'WYCC PBS Chicago (WYCC)'),  # MI, http://www.wycc.org
        ('lakelandptv.org', 'Lakeland Public Television (KAWE)'),  # MN, http://www.lakelandptv.org
        ('wdse.org', 'WDSE - WRPT (WDSE)'),  # MN, http://www.wdse.org/
        ('pioneer.org', 'Pioneer Public Television (KWCM)'),  # MN, http://www.pioneer.org
        ('tpt.org', 'TPT (KTCA)'),  # MN, http://www.tpt.org
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # MN, http://www.iptv.org/
        ('prairiepublic.org', 'PRAIRIE PUBLIC (KFME)'),  # MN, http://www.prairiepublic.org/
        ('ninenet.org', 'Nine Network (KETC)'),  # MN, http://www.ninenet.org
        ('sdpb.org', 'SDPB Television (KUSD)'),  # MN, http://www.sdpb.org
        ('wpt.org', 'WPT (WPNE)'),  # MN, http://www.wpt.org/
        ('ksmq.org', 'KSMQ (KSMQ)'),  # MN, http://www.ksmq.org/
        ('mpbonline.org', 'Mississippi Public Broadcasting (WMPN)'),  # MS, http://www.mpbonline.org
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # MS, http://www.aetn.org/
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # MS, http://aptv.org/
        ('wkno.org', 'WKNO/Channel 10 (WKNO)'),  # MS, http://www.wkno.org/
        ('lpb.org', 'LPB/LOUISIANA PUBLIC BROADCASTING (WLPB)'),  # MS, http://www.lpb.org/
        ('wsre.org', 'WSRE (WSRE)'),  # MS, http://www.wsre.org
        ('wyes.org', 'WYES-TV/New Orleans (WYES)'),  # MS, http://www.wyes.org
        ('kcpt.org', 'KCPT Kansas City Public Television (KCPT)'),  # MO, http://kcpt.org/
        ('kmos.org', 'KMOS-TV - Channels 6.1, 6.2 and 6.3 (KMOS)'),  # MO, http://www.kmos.org/
        ('ninenet.org', 'Nine Network (KETC)'),  # MO, http://www.ninenet.org
        ('optv.org', 'Ozarks Public Television (KOZK)'),  # MO, http://www.optv.org/
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # MO, http://www.aetn.org/
        ('dptv.org', 'WTVS Detroit Public TV (WTVS)'),  # MO, http://www.dptv.org/
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # MO, http://www.iptv.org/
        ('ket.org', 'KET (WKLE)'),  # MO, http://www.ket.org/
        ('wkno.org', 'WKNO/Channel 10 (WKNO)'),  # MO, http://www.wkno.org/
        ('ktwu.org', 'KTWU/Channel 11 (KTWU)'),  # MO, http://ktwu.org
        ('netnebraska.org', 'NET1 (KUON)'),  # MO, http://netnebraska.org
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # MO, http://www.rmpbs.org
        ('wsec.tv', 'Network Knowledge - WSEC/Springfield (WSEC)'),  # MO, http://www.wsec.tv
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # MO, http://www.wsiu.org/
        ('montanapbs.org', 'MontanaPBS (KUSM)'),  # MT, http://montanapbs.org
        ('azpbs.org', 'Arizona PBS (KAET)'),  # MT, http://www.azpbs.org
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # MT, http://idahoptv.org
        ('prairiepublic.org', 'PRAIRIE PUBLIC (KFME)'),  # MT, http://www.prairiepublic.org/
        ('ksps.org', 'KSPS (KSPS)'),  # MT, http://www.ksps.org/home/
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # MT, http://www.rmpbs.org
        ('sdpb.org', 'SDPB Television (KUSD)'),  # MT, http://www.sdpb.org
        ('netnebraska.org', 'NET1 (KUON)'),  # NE, http://netnebraska.org
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # NE, http://www.iptv.org/
        ('ktwu.org', 'KTWU/Channel 11 (KTWU)'),  # NE, http://ktwu.org
        ('pioneer.org', 'Pioneer Public Television (KWCM)'),  # NE, http://www.pioneer.org
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # NE, http://www.rmpbs.org
        ('sdpb.org', 'SDPB Television (KUSD)'),  # NE, http://www.sdpb.org
        ('wyomingpbs.org', 'Wyoming PBS (KCWC)'),  # NE, http://www.wyomingpbs.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # NE, http://www.cpt12.org/
        ('knpb.org', 'KNPB Channel 5 (KNPB)'),  # NV, http://www.knpb.org/
        ('vegaspbs.org', 'Vegas PBS (KLVX)'),  # NV, http://vegaspbs.org/
        ('azpbs.org', 'Arizona PBS (KAET)'),  # NV, http://www.azpbs.org
        ('kued.org', 'KUED Channel 7 (KUED)'),  # NV, http://www.kued.org
        ('pbssocal.org', 'PBS SoCal/KOCE (KOCE)'),  # NV, http://www.pbssocal.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # NV, http://www.kbyutv.org/
        ('nhptv.org', 'NHPTV (WENH)'),  # NH, http://nhptv.org/
        ('scetv.org', 'ETV (WRLK)'),  # NH, http://www.scetv.org
        ('mountainlake.org', 'Mountain Lake PBS (WCFE)'),  # NH, http://www.mountainlake.org/
        ('mpbn.net', 'MPBN (WCBB)'),  # NH, http://www.mpbn.net/
        ('vpt.org', 'Vermont PBS (WETK)'),  # NH, http://www.vpt.org
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # NH, http://wgbh.org
        ('wgby.org', 'WGBY (WGBY)'),  # NH, http://www.wgby.org
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # NJ, http://cptv.org
        ('thirteen.org', 'Thirteen/WNET New York (WNET)'),  # NJ, http://www.thirteen.org
        ('whyy.org', 'WHYY (WHYY)'),  # NJ, http://www.whyy.org
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # NJ, http://www.njtvonline.org/
        ('wlvt.org', 'PBS 39 (WLVT)'),  # NJ, http://www.wlvt.org/
        ('wliw.org', 'WLIW21 (WLIW)'),  # NJ, http://www.wliw.org/
        ('kenw.org', 'KENW-TV3 (KENW)'),  # NM, http://www.kenw.org
        ('krwg.org', 'KRWG/Channel 22 (KRWG)'),  # NM, http://www.krwg.org
        ('newmexicopbs.org', 'KNME-TV/Channel 5 (KNME)'),  # NM, http://www.newmexicopbs.org/
        ('azpm.org', 'KUAT 6 (KUAT)'),  # NM, http://www.azpm.org/
        ('panhandlepbs.org', 'KACV (KACV)'),  # NM, http://www.panhandlepbs.org/home/
        ('kcostv.org', 'KCOS/Channel 13 (KCOS)'),  # NM, www.kcostv.org
        ('kued.org', 'KUED Channel 7 (KUED)'),  # NM, http://www.kued.org
        ('oeta.tv', 'OETA (KETA)'),  # NM, http://www.oeta.tv
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # NM, http://www.rmpbs.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # NM, http://www.cpt12.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # NM, http://www.kbyutv.org/
        ('mountainlake.org', 'Mountain Lake PBS (WCFE)'),  # NY, http://www.mountainlake.org/
        ('thirteen.org', 'Thirteen/WNET New York (WNET)'),  # NY, http://www.thirteen.org
        ('wcny.org', 'WCNY/Channel 24 (WCNY)'),  # NY, http://www.wcny.org
        ('wmht.org', 'WMHT Educational Telecommunications (WMHT)'),  # NY, http://www.wmht.org/home/
        ('wned.org', 'WNED (WNED)'),  # NY, http://www.wned.org/
        ('wpbstv.org', 'WPBS (WPBS)'),  # NY, http://www.wpbstv.org
        ('wskg.org', 'WSKG Public TV (WSKG)'),  # NY, http://wskg.org
        ('wxxi.org', 'WXXI (WXXI)'),  # NY, http://wxxi.org
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # NY, http://cptv.org
        ('nhptv.org', 'NHPTV (WENH)'),  # NY, http://nhptv.org/
        ('vpt.org', 'Vermont PBS (WETK)'),  # NY, http://www.vpt.org
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # NY, http://wgbh.org
        ('wpsu.org', 'WPSU (WPSU)'),  # NY, http://www.wpsu.org
        ('wqln.org', 'WQLN/Channel 54 (WQLN)'),  # NY, http://www.wqln.org
        ('wvia.org', 'WVIA Public Media Studios (WVIA)'),  # NY, http://www.wvia.org/
        ('wliw.org', 'WLIW21 (WLIW)'),  # NY, http://www.wliw.org/
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # NY, http://www.njtvonline.org/
        ('unctv.org', 'UNC-TV (WUNC)'),  # NC, http://www.unctv.org/
        ('wtvi.org', 'WTVI (WTVI)'),  # NC, http://www.wtvi.org/
        ('blueridgepbs.org', 'Blue Ridge PBS (WBRA)'),  # NC, http://www.blueridgepbs.org/
        ('scetv.org', 'ETV (WRLK)'),  # NC, http://www.scetv.org
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # NC, http://www.gpb.org/
        ('whro.org', 'WHRO (WHRO)'),  # NC, http://whro.org
        ('wtcitv.org', 'WTCI (WTCI)'),  # NC, http://www.wtcitv.org
        ('pba.org', 'WPBA/Channel 30 (WPBA)'),  # NC, http://pba.org/
        ('prairiepublic.org', 'PRAIRIE PUBLIC (KFME)'),  # ND, http://www.prairiepublic.org/
        ('sdpb.org', 'SDPB Television (KUSD)'),  # ND, http://www.sdpb.org
        ('cetconnect.org', 'CET  (WCET)'),  # OH, http://www.cetconnect.org
        ('thinktv.org', 'ThinkTVNetwork (WPTD)'),  # OH, http://www.thinktv.org
        ('wbgu.org', 'WBGU-TV (WBGU)'),  # OH, http://wbgu.org
        ('wgte.org', 'WGTE TV (WGTE)'),  # OH, http://www.wgte.org
        ('WesternReservePublicMedia.org', 'Western Reserve PBS (WNEO)'),  # OH, http://www.WesternReservePublicMedia.org/
        ('wosu.org', 'WOSU TV (WOSU)'),  # OH, http://wosu.org/
        ('woub.org', 'WOUB/WOUC (WOUB)'),  # OH, http://woub.org/tv/index.php?section=5
        ('wviz.org', 'WVIZ/PBS ideastream (WVIZ)'),  # OH, http://www.wviz.org/
        ('dptv.org', 'WTVS Detroit Public TV (WTVS)'),  # OH, http://www.dptv.org/
        ('ket.org', 'KET (WKLE)'),  # OH, http://www.ket.org/
        ('wfwa.org', 'PBS39 Fort Wayne (WFWA)'),  # OH, http://wfwa.org/
        ('wipb.org', 'WIPB-TV (WIPB)'),  # OH, http://wipb.org
        ('wqed.org', 'WQED Multimedia (WQED)'),  # OH, http://www.wqed.org/
        ('wqln.org', 'WQLN/Channel 54 (WQLN)'),  # OH, http://www.wqln.org
        ('wvpublic.org', 'WVPB (WVPB)'),  # OH, http://wvpublic.org/
        ('oeta.tv', 'OETA (KETA)'),  # OK, http://www.oeta.tv
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # OK, http://www.aetn.org/
        ('panhandlepbs.org', 'KACV (KACV)'),  # OK, http://www.panhandlepbs.org/home/
        ('kera.org', 'KERA 13 (KERA)'),  # OK, http://www.kera.org/
        ('lpb.org', 'LPB/LOUISIANA PUBLIC BROADCASTING (WLPB)'),  # OK, http://www.lpb.org/
        ('optv.org', 'Ozarks Public Television (KOZK)'),  # OK, http://www.optv.org/
        ('opb.org', 'OPB (KOPB)'),  # OR, http://www.opb.org
        ('soptv.org', 'SOPTV (KSYS)'),  # OR, http://www.soptv.org
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # OR, http://idahoptv.org
        ('kcts9.org', 'KCTS 9 (KCTS)'),  # OR, http://kcts9.org/
        ('keet.org', 'KEET TV (KEET)'),  # OR, http://www.keet.org
        ('ksps.org', 'KSPS (KSPS)'),  # OR, http://www.ksps.org/home/
        ('kwsu.org', 'KWSU/Channel 10 & KTNW/Channel 31 (KWSU)'),  # OR, http://www.kwsu.org
        ('whyy.org', 'WHYY (WHYY)'),  # PA, http://www.whyy.org
        ('witf.org', 'witf (WITF)'),  # PA, http://www.witf.org
        ('wpsu.org', 'WPSU (WPSU)'),  # PA, http://www.wpsu.org
        ('wqed.org', 'WQED Multimedia (WQED)'),  # PA, http://www.wqed.org/
        ('wqln.org', 'WQLN/Channel 54 (WQLN)'),  # PA, http://www.wqln.org
        ('wvia.org', 'WVIA Public Media Studios (WVIA)'),  # PA, http://www.wvia.org/
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # PA, http://cptv.org
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # PA, http://www.mpt.org
        ('thirteen.org', 'Thirteen/WNET New York (WNET)'),  # PA, http://www.thirteen.org
        ('weta.org', 'WETA Television and Radio (WETA)'),  # PA, http://www.weta.org
        ('wned.org', 'WNED (WNED)'),  # PA, http://www.wned.org/
        ('WesternReservePublicMedia.org', 'Western Reserve PBS (WNEO)'),  # PA, http://www.WesternReservePublicMedia.org/
        ('wskg.org', 'WSKG Public TV (WSKG)'),  # PA, http://wskg.org
        ('wviz.org', 'WVIZ/PBS ideastream (WVIZ)'),  # PA, http://www.wviz.org/
        ('wvpublic.org', 'WVPB (WVPB)'),  # PA, http://wvpublic.org/
        ('wvpt.net', 'WVPT - Your Source for PBS and More! (WVPT)'),  # PA, http://www.wvpt.net
        ('wlvt.org', 'PBS 39 (WLVT)'),  # PA, http://www.wlvt.org/
        ('njtvonline.org', 'NJTV Public Media NJ (WNJT)'),  # PA, http://www.njtvonline.org/
        ('whut.org', 'Howard University Television (WHUT)'),  # PA, http://www.whut.org
        ('wliw.org', 'WLIW21 (WLIW)'),  # PA, http://www.wliw.org/
        ('cptv.org', 'CONNECTICUT PUBLIC TELEVISION (WEDH)'),  # RI, http://cptv.org
        ('nhptv.org', 'NHPTV (WENH)'),  # RI, http://nhptv.org/
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # RI, http://wgbh.org
        ('ripbs.org', 'Rhode Island PBS (WSBE)'),  # RI, http://www.ripbs.org/home/
        ('scetv.org', 'ETV (WRLK)'),  # SC, http://www.scetv.org
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # SC, http://www.gpb.org/
        ('unctv.org', 'UNC-TV (WUNC)'),  # SC, http://www.unctv.org/
        ('wtvi.org', 'WTVI (WTVI)'),  # SC, http://www.wtvi.org/
        ('pba.org', 'WPBA/Channel 30 (WPBA)'),  # SC, http://pba.org/
        ('sdpb.org', 'SDPB Television (KUSD)'),  # SD, http://www.sdpb.org
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # SD, http://www.iptv.org/
        ('prairiepublic.org', 'PRAIRIE PUBLIC (KFME)'),  # SD, http://www.prairiepublic.org/
        ('netnebraska.org', 'NET1 (KUON)'),  # SD, http://netnebraska.org
        ('pioneer.org', 'Pioneer Public Television (KWCM)'),  # SD, http://www.pioneer.org
        ('easttennesseepbs.org', 'East Tennessee PBS (WSJK)'),  # TN, http://easttennesseepbs.org
        ('wkno.org', 'WKNO/Channel 10 (WKNO)'),  # TN, http://www.wkno.org/
        ('wnpt.org', 'Nashville Public Television (WNPT)'),  # TN, http://www.wnpt.org
        ('wcte.org', 'WCTE-TV (WCTE)'),  # TN, http://www.wcte.org
        ('wljt.org', 'WLJT, Channel 11 (WLJT)'),  # TN, http://wljt.org/
        ('wtcitv.org', 'WTCI (WTCI)'),  # TN, http://www.wtcitv.org
        ('aptv.org', 'APT - Alabama Public Television (WBIQ)'),  # TN, http://aptv.org/
        ('blueridgepbs.org', 'Blue Ridge PBS (WBRA)'),  # TN, http://www.blueridgepbs.org/
        ('gpb.org', 'GPB/Georgia Public Broadcasting (WGTV)'),  # TN, http://www.gpb.org/
        ('lakelandptv.org', 'Lakeland Public Television (KAWE)'),  # TN, http://www.lakelandptv.org
        ('ket.org', 'KET (WKLE)'),  # TN, http://www.ket.org/
        ('mpbonline.org', 'Mississippi Public Broadcasting (WMPN)'),  # TN, http://www.mpbonline.org
        ('unctv.org', 'UNC-TV (WUNC)'),  # TN, http://www.unctv.org/
        ('WesternReservePublicMedia.org', 'Western Reserve PBS (WNEO)'),  # TN, http://www.WesternReservePublicMedia.org/
        ('wsiu.org', 'WSIU Public Broadcasting (WSIU)'),  # TN, http://www.wsiu.org/
        ('wviz.org', 'WVIZ/PBS ideastream (WVIZ)'),  # TN, http://www.wviz.org/
        ('wkyupbs.org', 'WKYU-PBS (WKYU)'),  # TN, http://www.wkyupbs.org
        ('pba.org', 'WPBA/Channel 30 (WPBA)'),  # TN, http://pba.org/
        ('basinpbs.org', 'Basin PBS (KPBT)'),  # TX, http://www.basinpbs.org
        ('houstonpublicmedia.org', 'KUHT / Channel 8 (KUHT)'),  # TX, http://www.houstonpublicmedia.org/
        ('panhandlepbs.org', 'KACV (KACV)'),  # TX, http://www.panhandlepbs.org/home/
        ('tamu.edu', 'KAMU - TV (KAMU)'),  # TX, http://KAMU.tamu.edu
        ('kcostv.org', 'KCOS/Channel 13 (KCOS)'),  # TX, www.kcostv.org
        ('kedt.org', 'KEDT/Channel 16 (KEDT)'),  # TX, http://www.kedt.org
        ('kera.org', 'KERA 13 (KERA)'),  # TX, http://www.kera.org/
        ('klrn.org', 'KLRN (KLRN)'),  # TX, http://www.klrn.org
        ('klru.org', 'KLRU (KLRU)'),  # TX, http://www.klru.org
        ('kmbh.org', 'KMBH-TV (KMBH)'),  # TX, http://www.kmbh.org
        ('knct.org', 'KNCT (KNCT)'),  # TX, http://www.knct.org
        ('ktxt.org', 'KTTZ-TV (KTXT)'),  # TX, http://www.ktxt.org
        ('aetn.org', 'AETN/ARKANSAS ETV NETWORK (KETS)'),  # TX, http://www.aetn.org/
        ('kenw.org', 'KENW-TV3 (KENW)'),  # TX, http://www.kenw.org
        ('krwg.org', 'KRWG/Channel 22 (KRWG)'),  # TX, http://www.krwg.org
        ('lpb.org', 'LPB/LOUISIANA PUBLIC BROADCASTING (WLPB)'),  # TX, http://www.lpb.org/
        ('netnebraska.org', 'NET1 (KUON)'),  # TX, http://netnebraska.org
        ('newmexicopbs.org', 'KNME-TV/Channel 5 (KNME)'),  # TX, http://www.newmexicopbs.org/
        ('wnpt.org', 'Nashville Public Television (WNPT)'),  # TX, http://www.wnpt.org
        ('oeta.tv', 'OETA (KETA)'),  # TX, http://www.oeta.tv
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # TX, http://www.rmpbs.org
        ('kued.org', 'KUED Channel 7 (KUED)'),  # UT, http://www.kued.org
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # UT, http://idahoptv.org
        ('vegaspbs.org', 'Vegas PBS (KLVX)'),  # UT, http://vegaspbs.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # UT, http://www.kbyutv.org/
        ('vpt.org', 'Vermont PBS (WETK)'),  # VT, http://www.vpt.org
        ('mountainlake.org', 'Mountain Lake PBS (WCFE)'),  # VT, http://www.mountainlake.org/
        ('nhptv.org', 'NHPTV (WENH)'),  # VT, http://nhptv.org/
        ('wgbh.org', 'WGBH/Channel 2 (WGBH)'),  # VT, http://wgbh.org
        ('wgby.org', 'WGBY (WGBY)'),  # VT, http://www.wgby.org
        ('wmht.org', 'WMHT Educational Telecommunications (WMHT)'),  # VT, http://www.wmht.org/home/
        ('wtjx.org', 'WTJX Channel 12 (WTJX)'),  # VI, http://www.wtjx.org/
        ('blueridgepbs.org', 'Blue Ridge PBS (WBRA)'),  # VA, http://www.blueridgepbs.org/
        ('ideastations.org', 'WCVE PBS (WCVE)'),  # VA, http://ideastations.org/
        ('whro.org', 'WHRO (WHRO)'),  # VA, http://whro.org
        ('wvpt.net', 'WVPT - Your Source for PBS and More! (WVPT)'),  # VA, http://www.wvpt.net
        ('easttennesseepbs.org', 'East Tennessee PBS (WSJK)'),  # VA, http://easttennesseepbs.org
        ('ket.org', 'KET (WKLE)'),  # VA, http://www.ket.org/
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # VA, http://www.mpt.org
        ('unctv.org', 'UNC-TV (WUNC)'),  # VA, http://www.unctv.org/
        ('weta.org', 'WETA Television and Radio (WETA)'),  # VA, http://www.weta.org
        ('whut.org', 'Howard University Television (WHUT)'),  # VA, http://www.whut.org
        ('kcts9.org', 'KCTS 9 (KCTS)'),  # WA, http://kcts9.org/
        ('ksps.org', 'KSPS (KSPS)'),  # WA, http://www.ksps.org/home/
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # WA, http://idahoptv.org
        ('opb.org', 'OPB (KOPB)'),  # WA, http://www.opb.org
        ('kbtc.org', 'KBTC Public Television (KBTC)'),  # WA, http://kbtc.org
        ('kwsu.org', 'KWSU/Channel 10 & KTNW/Channel 31 (KWSU)'),  # WA, http://www.kwsu.org
        ('wvpublic.org', 'WVPB (WVPB)'),  # WV, http://wvpublic.org/
        ('blueridgepbs.org', 'Blue Ridge PBS (WBRA)'),  # WV, http://www.blueridgepbs.org/
        ('ket.org', 'KET (WKLE)'),  # WV, http://www.ket.org/
        ('mpt.org', 'mpt/Maryland Public Television (WMPB)'),  # WV, http://www.mpt.org
        ('weta.org', 'WETA Television and Radio (WETA)'),  # WV, http://www.weta.org
        ('WesternReservePublicMedia.org', 'Western Reserve PBS (WNEO)'),  # WV, http://www.WesternReservePublicMedia.org/
        ('wosu.org', 'WOSU TV (WOSU)'),  # WV, http://wosu.org/
        ('woub.org', 'WOUB/WOUC (WOUB)'),  # WV, http://woub.org/tv/index.php?section=5
        ('wqed.org', 'WQED Multimedia (WQED)'),  # WV, http://www.wqed.org/
        ('wvpt.net', 'WVPT - Your Source for PBS and More! (WVPT)'),  # WV, http://www.wvpt.net
        ('whut.org', 'Howard University Television (WHUT)'),  # WV, http://www.whut.org
        ('mptv.org', 'Milwaukee Public Television (WMVS)'),  # WI, http://www.mptv.org
        ('wpt.org', 'WPT (WPNE)'),  # WI, http://www.wpt.org/
        ('iptv.org', 'Iowa Public Television/IPTV (KDIN)'),  # WI, http://www.iptv.org/
        ('lakelandptv.org', 'Lakeland Public Television (KAWE)'),  # WI, http://www.lakelandptv.org
        ('wdse.org', 'WDSE - WRPT (WDSE)'),  # WI, http://www.wdse.org/
        ('tpt.org', 'TPT (KTCA)'),  # WI, http://www.tpt.org
        ('nmu.edu', 'WNMU-TV Public TV 13 (WNMU)'),  # WI, http://wnmutv.nmu.edu
        ('wttw.com', 'WTTW11 (WTTW)'),  # WI, http://www.wttw.com/
        ('ksmq.org', 'KSMQ (KSMQ)'),  # WI, http://www.ksmq.org/
        ('wycc.org', 'WYCC PBS Chicago (WYCC)'),  # WI, http://www.wycc.org
        ('wyomingpbs.org', 'Wyoming PBS (KCWC)'),  # WY, http://www.wyomingpbs.org
        ('idahoptv.org', 'Idaho Public Television (KAID)'),  # WY, http://idahoptv.org
        ('kued.org', 'KUED Channel 7 (KUED)'),  # WY, http://www.kued.org
        ('montanapbs.org', 'MontanaPBS (KUSM)'),  # WY, http://montanapbs.org
        ('netnebraska.org', 'NET1 (KUON)'),  # WY, http://netnebraska.org
        ('rmpbs.org', 'Rocky Mountain PBS (KRMA)'),  # WY, http://www.rmpbs.org
        ('sdpb.org', 'SDPB Television (KUSD)'),  # WY, http://www.sdpb.org
        ('cpt12.org', 'Colorado Public Television / KBDI 12 (KBDI)'),  # WY, http://www.cpt12.org/
        ('kbyutv.org', 'KBYU-TV (KBYU)'),  # WY, http://www.kbyutv.org/
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
