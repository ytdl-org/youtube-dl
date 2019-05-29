# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_resolution,
    try_get,
    unified_timestamp,
    url_or_none,
    urljoin,
)


class PeerTubeIE(InfoExtractor):
    # generated with (on the fish shell, with jq installed):
    # echo (echo -n "(?:" ; curl -s "https://instances.joinpeertube.org/api/v1/instances?start=0&count=5000" | jq | string match -r "\"host\": \"(.*)\"" | string match -vr "\"host\": \"" | string replace -a . "\." | string join "|"; echo -n "|tube\.22decembre\.eu)") > instancelist
    _INSTANCES_RE = r'''(?:tube\.openalgeria\.org|peertube\.mastodon\.host|armstube\.com|tube\.moxaik\.de|peertube\.gnumeria\.fr|video\.minzord\.eu\.org|video\.cohan\.io|peertube\.s2s\.video|peertube\.lol|tube\.open-plug\.eu|videos\.mikedilger\.com|open\.tube|peertube\.ch|peertube\.normandie-libre\.fr|pt\.a-trappes-terre\.fr|peertube\.slat\.org|video\.lacaveatonton\.ovh|peertube\.uno|peertube\.servebeer\.com|lexx\.impa\.me|peertube\.fedi\.quebec|tube\.h3z\.jp|tube\.plus200\.com|peertube\.eric\.ovh|tube\.metadocs\.cc|tube\.unmondemeilleur\.eu|dissidents\.tv|anartube\.zapto\.org|gouttedeau\.space|video\.antirep\.net|peertube\.odat\.xyz|peertube\.davidpeach\.co\.uk|nrop\.cant\.at|peertube\.hugolecourt\.fr|v\.mbius\.io|tube\.tr4sk\.me|peertube\.osureplayviewer\.xyz|video\.bruitbruit\.com|video\.abga\.be|tube\.dodsorf\.as|tube\.ksl-bmx\.de|tube\.plaf\.fr|tube\.tchncs\.de|peertube\.azkware\.net|video\.devinberg\.com|video\.hdys\.band|hitchtube\.fr|video\.glassbeadcollective\.org|nsfw\.wetube\.moe|peertube\.kosebamse\.com|medias\.libox\.fr|tube\.mux\.re|peertube\.travelpandas\.eu|yunopeertube\.myddns\.me|eggz\.tv|peertube\.varney\.fr|peertube\.anon-kenkai\.com|peertube\.bimwiki\.fr|video\.atlanti\.se|tube\.maiti\.info|vid\.lubar\.me|tubee\.fr|videos\.dinofly\.com|tube\.ipfixe\.info|toobnix\.org|videotape\.me|voca\.tube|peertube\.com\.au|peerwatch\.xyz|video\.heromuster\.com|video\.lemediatv\.fr|video\.up\.edu\.ph|balafon\.video|video\.ivel\.fr|thickrips\.cloud|pt\.laurentkruger\.fr|peertube\.m2\.nz|peertube\.esadhar\.net|peertube\.geismar\.paris|video\.monarch-pass\.net|peertube\.artica\.center|tube\.nx-pod\.de|video\.vny\.fr|video\.alternanet\.fr|indymotion\.fr|fanvid\.stopthatimp\.net|cine\.nashe\.be|video\.farci\.org|v\.lesterpig\.com|video\.okaris\.de|tube\.pawelko\.net|peertube\.mablr\.org|tube\.fede\.re|pytu\.be|evertron\.tv|peertube\.wivodaim\.com|devtube\.dev-wiki\.de|raptube\.antipub\.org|video\.selea\.se|peertube\.mygaia\.org|video\.oh14\.de|tube\.fabrigli\.fr|peertube\.livingutopia\.org|peertube\.the-penguin\.de|tube\.thechangebook\.org|peertube\.montecsys\.fr|tube\.anjara\.eu|pt\.pube\.tk|video\.samedi\.pm|mplayer\.demouliere\.eu|peertube\.dans-ma-bulle\.life|widemus\.de|peertube\.me|luttube\.tk|video\.depucelage\.xyz|peertube\.zapashcanon\.fr|mhtube\.de|video\.latavernedejohnjohn\.fr|peertube\.pcservice46\.fr|peertube\.mazzonetto\.eu|tube\.linc\.systems|video\.irem\.univ-paris-diderot\.fr|video\.livecchi\.cloud|alttube\.fr|video\.coop\.tools|peertube\.pretex\.space|video\.cabane-libre\.org|peertube\.openstreetmap\.fr|peertube\.nipponalba\.scot|videos\.alolise\.org|vis\.ion\.ovh|csictv\.csic\.es|peertube\.gaah\.duckdns\.org|0ch\.in|irrsinn\.video|video\.antopie\.org|scitech\.video|tube2\.nemsia\.org|video\.amic37\.fr|peertube\.freeforge\.eu|video\.arbitrarion\.com|peertube\.joel-smolski\.com|video\.datsemultimedia\.com|stoptrackingus\.tv|peertube\.ricostrongxxx\.com|tubercul\.es|peertube\.mindpalace\.io|docker\.videos\.lecygnenoir\.info|peertube\.terranout\.mine\.nu|peertube\.togart\.de|tube\.postblue\.info|videos\.domainepublic\.net|peertube\.cyber-tribal\.com|video\.gresille\.org|peertube\.dsmouse\.net|peertube\.david\.durieux\.family|cinema\.yunohost\.support|tube\.theocevaer\.fr|repro\.video|tube\.4aem\.com|opera42\.com|quaziinc\.com|peertube\.metawurst\.space|videos\.wakapo\.com|video\.ploud\.fr|video\.freeradical\.zone|tube\.valinor\.fr|refuznik\.video|rhoads\.com|tube\.64\.re|peertube\.xoddark\.com|peertube\.subak\.ovh|pt\.kircheneuenburg\.de|peertube\.asrun\.eu|peertube\.lagob\.fr|videos\.side-ways\.net|videos\.upr\.fr|peervideo\.net|peertube\.dynlinux\.io|91video\.online|video\.valme\.io|video\.taboulisme\.com|peertube\.la-famille-muller\.fr|videos-libr\.es|wetube\.moe|video\.monsieurbidouille\.fr|tv\.mooh\.fr|nuage\.acostey\.fr|video\.monsieur-a\.fr|peertube\.librelois\.fr|tube\.radiomercure\.fr|videos\.pair2jeux\.tube|videos\.pueseso\.club|peer\.mathdacloud\.ovh|media\.assassinate-you\.net|vidcommons\.org|ptube\.rousset\.nom\.fr|tube\.cyano\.at|videos\.squat\.net|video\.iphodase\.fr|peertube\.makotoworkshop\.org|peertube\.serveur\.slv-valbonne\.fr|vault\.mle\.party|hostyour\.tv|videos\.hack2g2\.fr|libre\.tube|pire\.artisanlogiciel\.net|videos\.numerique-en-commun\.fr|video\.netsyms\.com|tube\.ecutsa\.fr|video\.fdlibre\.eu|video\.die-partei\.social|video\.writeas\.org|peertube\.swarm\.solvingmaz\.es|tube\.pericoloso\.ovh|watching\.cypherpunk\.observer|videos\.adhocmusic\.com|tube\.rfc1149\.net|lostpod\.space|peertube\.librelabucm\.org|videos\.numericoop\.fr|peertube\.koehn\.com|peertube\.anarchmusicall\.net|tube\.kampftoast\.de|video\.jacky\.wtf|vid\.y-y\.li|peertube\.xtenz\.xyz|diode\.zone|tube\.egf\.mn|peertube\.nomagic\.uk|visionon\.tv|videos\.koumoul\.com|video\.rastapuls\.com|video\.mantlepro\.com|video\.deadsuperhero\.com|peertube\.leboulaire\.ovh|tube\.taker\.fr|peertube\.musicstudio\.pro|peertube\.we-keys\.fr|artitube\.artifaille\.fr|peertube\.ethernia\.net|video\.nesven\.eu|tube\.midov\.pl|peertube\.fr|watch\.snoot\.tube|peertube\.donnadieu\.fr|argos\.aquilenet\.fr|tube\.nemsia\.org|tube\.bruniau\.net|videos\.darckoune\.moe|tube\.traydent\.info|dev\.videos\.lecygnenoir\.info|peertube\.nayya\.org|peertube\.live|peertube\.mofgao\.space|tube\.yukimochi\.jp|video\.lequerrec\.eu|peertube\.amicale\.net|aperi\.tube|peertube\.alexkeating\.me|tube\.ac-lyon\.fr|video\.lw1\.at|www\.yiny\.org|videos\.pofilo\.fr|tube\.lou\.lt|peertube\.rencontres-atelier\.fr|choob\.h\.etbus\.ch|hoot\.video|tube\.hoga\.fr|queertube\.org|peertube\.heberge\.fr|peertube\.snargol\.com|video\.obermui\.de|videos\.cloudfrancois\.fr|betamax\.video|video\.typica\.us|tube\.piweb\.be|video\.blender\.org|peertube\.cat|peer\.tube|tube\.kdy\.ch|pe\.ertu\.be|peertube\.social|videos\.lescommuns\.org|tv\.datamol\.org|videonaute\.fr|dialup\.express|peertube\.nogafa\.org|megatube\.lilomoino\.fr|peertube\.tamanoir\.foucry\.net|peertube\.inapurna\.org|peertube\.devosi\.org|peertube\.1312\.media|tube\.bootlicker\.party|skeptikon\.fr|peertube\.geekshell\.fr|video\.blueline\.mg|tube\.homecomputing\.fr|tube\.ouahpiti\.info|video\.tedomum\.net|video\.g3l\.org|fontube\.fr|peertube\.gaialabs\.ch|tube\.kher\.nl|peertube\.qtg\.fr|video\.migennes\.net|tube\.p2p\.legal|troll\.tv|vid\.leotindall\.com|videos\.iut-orsay\.fr|peertube\.solidev\.net|videos\.cemea\.org|video\.passageenseine\.fr|videos\.festivalparminous\.org|peertube\.touhoppai\.moe|sikke\.fi|vidz\.dou\.bet|peer\.hostux\.social|share\.tube|peertube\.walkingmountains\.fr|videos\.benpro\.fr|tube\.otter\.sh|peertube\.parleur\.net|peertube\.heraut\.eu|vod\.mochi\.academy|exode\.me|tube\.aquilenet\.fr|peertube\.gegeweb\.eu|framatube\.org|thinkerview\.video|tube\.conferences-gesticulees\.net|peertube\.datagueule\.tv|video\.lqdn\.fr|tube\.mochi\.academy|media\.zat\.im|video\.colibris-outilslibres\.org|video\.hispagatos\.org|tube\.svnet\.fr|peertube\.video|videos\.lecygnenoir\.info|peertube3\.cpy\.re|peertube2\.cpy\.re|videos\.tcit\.fr|peertube\.cpy\.re |tube\.22decembre\.eu)
'''
    _UUID_RE = r'[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}'
    _VALID_URL = r'''(?x)
                    (?:
                        peertube:(?P<host>[^:]+):|
                        https?://(?P<host_2>%s)/(?:videos/(?:watch|embed)|api/v\d/videos)/
                    )
                    (?P<id>%s)
                    ''' % (_INSTANCES_RE, _UUID_RE)
    _TESTS = [{
        'url': "https://framatube.org/videos/watch/9c9de5e8-0a1e-484a-b099-e80766180a6d",
        'md5': '9bed8c0137913e17b86334e5885aacff',
        'info_dict': {
            'id': '9c9de5e8-0a1e-484a-b099-e80766180a6d',
            'ext': 'mp4',
            'title': 'What is PeerTube?',
            'description': """**[Want to help to translate this video?](https://trad.framasoft.org/iteration/view/what-is-peertube/master)** (documentation [here](https://trad.framasoft.org))!\r\n\r\n**Take back the control of your videos! [#JoinPeertube](https://joinpeertube.org)**\r\n*A decentralized video hosting network, based on free/libre software!*\r\n\r\n**Animation Produced by:** [LILA](https://libreart.info) - [ZeMarmot Team](https://film.zemarmot.net)\r\n*Directed by* Aryeom\r\n*Assistant* Jehan\r\n**Licence**: [CC-By-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)\r\n\r\n**Sponsored by** [Framasoft](https://framasoft.org)\r\n\r\n**Music**: [Red Step Forward](http://play.dogmazic.net/song.php?song_id=52491) - CC-By Ken Bushima\r\n\r\n**Movie Clip**: [Caminades 3: Llamigos](http://www.caminandes.com/) CC-By Blender Institute""",
            'timestamp': 1538391166,
            'upload_date': '20181001',
            'uploader': 'Framasoft',
            'uploader_id': '0a635cad-dcdb-443f-b600-6c38ffaffe1f',
            'uploader_url': 'https://framatube.org/accounts/framasoft',
            'license': 'Attribution - Share Alike',
            'duration': 113,
            'view_count': int,
            'like_count': int,
            'dislike_count': int,
            'tags': list,
            'categories': list,
        }
    }, {
        'url': 'https://peertube.tamanoir.foucry.net/videos/watch/0b04f13d-1e18-4f1d-814e-4979aa7c9c44',
        'only_matching': True,
    }, {
        # nsfw
        'url': 'https://tube.22decembre.eu/videos/watch/9bb88cd3-9959-46d9-9ab9-33d2bb704c39',
        'only_matching': True,
    }, {
        'url': 'https://tube.22decembre.eu/videos/embed/fed67262-6edb-4d1c-833b-daa9085c71d7',
        'only_matching': True,
    }, {
        'url': 'https://tube.openalgeria.org/api/v1/videos/c1875674-97d0-4c94-a058-3f7e64c962e8',
        'only_matching': True,
    }, {
        'url': 'peertube:video.blender.org:b37a5b9f-e6b5-415c-b700-04a5cd6ec205',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_peertube_url(webpage, source_url):
        mobj = re.match(
            r'https?://(?P<host>[^/]+)/videos/watch/(?P<id>%s)'
            % PeerTubeIE._UUID_RE, source_url)
        if mobj and any(p in webpage for p in (
                '<title>PeerTube<',
                'There will be other non JS-based clients to access PeerTube',
                '>We are sorry but it seems that PeerTube is not compatible with your web browser.<')):
            return 'peertube:%s:%s' % mobj.group('host', 'id')

    @staticmethod
    def _extract_urls(webpage, source_url):
        entries = re.findall(
            r'''(?x)<iframe[^>]+\bsrc=["\'](?P<url>(?:https?:)?//%s/videos/embed/%s)'''
            % (PeerTubeIE._INSTANCES_RE, PeerTubeIE._UUID_RE), webpage)
        if not entries:
            peertube_url = PeerTubeIE._extract_peertube_url(webpage, source_url)
            if peertube_url:
                entries = [peertube_url]
        return entries

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host') or mobj.group('host_2')
        video_id = mobj.group('id')

        video = self._download_json(
            'https://%s/api/v1/videos/%s' % (host, video_id), video_id)

        title = video['name']

        formats = []
        for file_ in video['files']:
            if not isinstance(file_, dict):
                continue
            file_url = url_or_none(file_.get('fileUrl'))
            if not file_url:
                continue
            file_size = int_or_none(file_.get('size'))
            format_id = try_get(
                file_, lambda x: x['resolution']['label'], compat_str)
            f = parse_resolution(format_id)
            f.update({
                'url': file_url,
                'format_id': format_id,
                'filesize': file_size,
            })
            formats.append(f)
        self._sort_formats(formats)

        def account_data(field):
            return try_get(video, lambda x: x['account'][field], compat_str)

        category = try_get(video, lambda x: x['category']['label'], compat_str)
        categories = [category] if category else None

        nsfw = video.get('nsfw')
        if nsfw is bool:
            age_limit = 18 if nsfw else 0
        else:
            age_limit = None

        try:
            description = self._download_json(
                'https://%s/api/v1/videos/%s/description' % (host, video_id), video_id, note="Downloading description", fatal=False).get("description")
        except BaseException:
            description = description.get("description")

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': urljoin(url, video.get('thumbnailPath')),
            'timestamp': unified_timestamp(video.get('publishedAt')),
            'uploader': account_data('displayName'),
            'uploader_id': account_data('uuid'),
            'uploader_url': account_data('url'),
            'license': try_get(
                video, lambda x: x['licence']['label'], compat_str),
            'duration': int_or_none(video.get('duration')),
            'view_count': int_or_none(video.get('views')),
            'like_count': int_or_none(video.get('likes')),
            'dislike_count': int_or_none(video.get('dislikes')),
            'age_limit': age_limit,
            'tags': try_get(video, lambda x: x['tags'], list),
            'categories': categories,
            'formats': formats,
        }


class PeerTubeChannelIE(PeerTubeIE):
    _CHANNEL_RE = r'[a-zA-Z0-9-_@\.]+'
    _VALID_URL = r'''(?x)
                    (?:
                        https?://(?P<host>%s)/(api/v\d/)?accounts/(?P<channel>%s)/videos
                    )
                    ''' % (PeerTubeIE._INSTANCES_RE, _CHANNEL_RE)
    _TESTS = [{
        'url': 'https://peertube.cpy.re/accounts/chocobozzz/videos',
        'info_dict': {
            'id': '1fccb6e4-863c-4538-a4db-770c464f06a1',
            'title': 'Default chocobozzz channel',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://videos.pair2jeux.tube/accounts/lecygnenoir/videos',
        'info_dict': {
            'title': 'Default lecygnenoir channel',
            'id': '8a1ea992-9adf-4c3e-90b2-972d5b299be9',
        },
        'playlist_mincount': 880,
    }, {
        'url': 'https://peertube.mastodon.host/accounts/ecoleduchatnoir@sikke.fi/videos',
        'only_matching': True
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        channelId = mobj.group('channel')

        videos = self._download_json(
            'https://%s/api/v1/accounts/%s/videos?count=50' % (host, channelId), channelId)

        channel = None
        if len(videos.get('data')) > 0:
            channel = videos.get('data')[0].get('channel')

        videoCount = videos.get("total") or 0

        videoListed = 0
        entries = []
        while videoListed < videoCount:
            for video in videos.get('data'):
                entries.append({
                    'url': "peertube:%s" % video.get("uuid"),
                    'id': video.get('uuid'),
                    'title': video.get("name"),
                    'description': video.get('description'),
                    'license': try_get(
                        video, lambda x: x['licence']['label'], compat_str),
                    'duration': int_or_none(video.get('duration')),
                    'view_count': int_or_none(video.get('views')),
                    'like_count': int_or_none(video.get('likes')),
                    'dislike_count': int_or_none(video.get('dislikes')),
                    'tags': try_get(video, lambda x: x['tags'], list),
                })
                videoListed += 1

            if videoListed != videoCount:
                videos = self._download_json(
                    'https://%s/api/v1/accounts/%s/videos?count=50&start=%s' % (host, channelId, str(videoListed)), channel, note="Downloading page from the video %s/%s" % (str(videoListed), str(videoCount)))

        if channel is None:
            return self.playlist_result(entries)
        else:
            return self.playlist_result(entries, channel.get('uuid'), channel.get('displayName'))
