from __future__ import unicode_literals
from datetime import (
    datetime,
    timedelta,
)

from .common import InfoExtractor
from ..utils import (
    update_url_query,
    xpath_text,
    str_to_int,
    int_or_none,
    HEADRequest,
)

import re


class Kanal2IE(InfoExtractor):
    _VALID_URL = r'(?P<base>.+\.postimees\.ee)[a-zA-Z0-9\/._-]+\?[a-zA-Z0-9=&._-]*id=(?P<id>[0-9]+)[^ ]*'
    _TESTS = [{
        # The most ordinary case
        'url': 'http://kanal2.postimees.ee/pluss/video/?id=40792',
        'md5': '173e29daea5f5fab49390bddd78aaaf0',
        'info_dict': {
            'id': '40792',
            'ext': 'flv',
            'title': 'Aedniku aabits (06.08.2016 10:30)',
            'thumbnail': 'http://kanal2.postimees.ee/imagecache/http_img.cdn.mind.ee/kanal2//14/100/00033/0053_4468c974c1010a21817c1ee37f3e7902.jpeg',
            'description': 'Aedniku aabits" on saade, mis pakub kaasaelamist ja teadmisi nii algajatele, kui juba kogenud rohenäppudele. Kõik alates vajalikest näpunäidetest, nutikatest lahendustest, uudistoodetest kuni taimede hingeeluni ning aias kasutatava tehnikani välja.',
            'upload_date': '20160805',
            'timestamp': 1470434400,
        }
    }, {
        # Embed player, also needs login in reality but all the streams are accessable without logging in
        'url': 'http://kanal2.postimees.ee/video/lonelyPlayer?videoid=28848',
        'md5': '18edb2fd235c06a60b81b3590a357ace',
        'info_dict': {
            'id': '28848',
            'ext': 'flv',
            'title': 'Viimane võmm - Rita, ära jama (24.11.2015 21:30)',
            'thumbnail': 'http://kanal2.postimees.ee/imagecache/http_img.cdn.mind.ee/kanal2//14/100/00002/0050_4468c974c1010a21817c1ee37f3e7902.jpeg',
            'description': 'Kinnisvaraomanik Villem Meius leitakse oma korterist tapetuna. Turvakaamera video paljastab surnukeha kõrvalt lahkumas ühe Meiuse üürniku - ei kellegi muu, kui politseinike kaitseingli Rita! Rita võetakse vahi alla ning kogu jaoskond näeb vaeva selle nimel, et teda vabastada ning tema kinniistumise ajal Rita baari käigus hoida. Uurimise käigus paljastub ulatuslik ja häbitu kinnisvarahangeldamine Kalamajas, mille niidid ulatuvad ka justiitsmaailma ladvikusse. Vastasleeri moodustavad Kalamaja põliselanikud. Organisatsiooni peakorter asub kellegi Mort Pärgi matusebüroos. Sealt hakkabki asi lõpuks hargnema.'
        }
    }, {
        # Other ordinary case
        'url': 'http://kanal2.postimees.ee/pluss/preview?id=40744',
        'md5': '2579cdbf16013d7e7a7361a832bc818e',
        'info_dict': {
            'id': '40744',
            'ext': 'flv',
            'title': 'Kaunis Dila (10.08.2016 19:00)',
            'thumbnail': 'http://kanal2.postimees.ee/imagecache/http_img.cdn.mind.ee/kanal2//16/300/00208/0050_4468c974c1010a21817c1ee37f3e7902.jpeg',
        }
    }, {
        # Not on kanal2 subdomain like others, the site has different layout, so a lot of data can't be accessed, but the api's are same. also has rating
        'url': 'http://kanal12.postimees.ee/vaatasaateid/Punkri-joulueri?videoid=248',
        'md5': '4633c310980201e4d8195d22b948ad10',
        'info_dict': {
            'id': '248',
            'ext': 'flv',
            'title': 'Punkri jõulueri',
            'thumbnail': 'http://img.cdn.mind.ee/kanal2/clips/KANAL 12/punkri joulueri.jpeg',
            'description': 'Eestlaste lemmik-krõbesaade lõpetab aasta loodetavasti südamliku pühade-eriga! Hapukapsad ninast välja! Jeesuse sündi on tulnud tähistama Ivo Linna, pastor, saatan ja paljud teised. Saadet juhivad Marge Tava, Aleksander Ots ja Marek Reinaas.',
            'average_rating': int,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # base url, e.g. kanal2.postimees.ee (in chrome, the black part of the address)
        base = re.compile(self._VALID_URL).match(url).group('base')

        # Acquire the video's address, where we can search for website data(needed in case of embed player)
        if "pluss" not in url and "kanal2" in base:
            # Generic url for all the kanal2 videos, may redirect
            url = base + '/pluss/video/?id=' + video_id
            # This part copied from generic.py, bypasses redirects
            head_response = self._request_webpage(HEADRequest(url), video_id)
            if head_response is not False:
                new_url = head_response.geturl()
                if url != new_url:
                    self._downloader.to_screen('[redirect] Following redirect to %s' % new_url)
                return self.url_result(new_url)
                # copied until here

        xmlfile = self._download_xml(update_url_query(base + '/video/playerPlaylistApi', {'id': video_id}), video_id)

        # Remove stacked urls(e.g. http://test.comhttp://test2.com, removes everything before second http)
        thumbnail = re.compile('[^\0]*(?P<realurl>https?:\/\/[^"]+)[^\0]*').match(base + xpath_text(xmlfile, './playlist/video/thumbUrl')).group('realurl')
        average_rating = int_or_none(xpath_text(xmlfile, './playlist/video/rating/value'))

        # Determine, whether the stream is high or low quality and act accordingly
        for stream in xmlfile.findall('./playlist/video/streamItems/streamItem'):
            # Found low quality stream, but keep iterating streamItems in hope of finding hq stream
            if "k2lq" in stream.get('streamName'):
                streamname = stream.get('streamName')
                width = str_to_int(stream.get('width'))
                height = str_to_int(stream.get('height'))
                continue
            # Found high quality stream, looping no longer necessary
            if "k2hq" in stream.get('streamName'):
                streamname = stream.get('streamName')
                width = str_to_int(stream.get('width'))
                height = str_to_int(stream.get('height'))
                break

        webpage = self._download_webpage(url, video_id)
        # Is the following info on website? if div player-container is present, info also is
        if 'player-container' in webpage:
            # Find description
            description = self._search_regex(r'[^\0]*<p class="full"[^>]*>([^<]*)<\/p>[^\0]*', webpage, 'description', default=None)
            if description is not None:
                # Remove a lot of trailing spaces, that were added to get the text to be in the right place on webpage
                description = description.strip()
            # Episode and season
            epandseason = self._search_regex('[^\0]*(Osa *[0-9]+ *Hooaeg *[0-9]+)[^\0]*', webpage, 'epandseason', default=None)
            if epandseason is not None:
                episode = int_or_none(re.compile('Osa *(?P<episode>[0-9]+) *Hooaeg *[0-9]+').match(epandseason).group('episode'))
                season = int_or_none(re.compile('Osa *[0-9]+ *Hooaeg *(?P<season>[0-9]+)').match(epandseason).group('season'))
            # Timestamp generation
            dateandtime = self._search_regex('[^\0]*(eetris[^\0]*<\/span>[^\0]*[0-9]{1,2}.[0-9]{1,2}.[0-9]{4,}[^0-9]*[0-9]{1,2}:[0-9]{1,2})[^\0]*', webpage, 'dateandtime', default=None)
            if dateandtime is not None:
                date = re.compile('[^\0]*eetris[^\0]*<\/span>[^\0]*(?P<date>[0-9]{1,2}.[0-9]{1,2}.[0-9]{4,})[^0-9]*(?P<time>[0-9]{1,2}:[0-9]{1,2})[^\0]*').match(dateandtime).group('date')
                time = re.compile('[^\0]*eetris[^\0]*<\/span>[^\0]*(?P<date>[0-9]{1,2}.[0-9]{1,2}.[0-9]{4,})[^0-9]*(?P<time>[0-9]{1,2}:[0-9]{1,2})[^\0]*').match(dateandtime).group('time')
                timestamp = int_or_none((datetime.strptime(date + " " + time, '%d.%m.%Y %H:%M') - datetime(1970, 1, 1) + timedelta(seconds=60 * 60 * 2)).total_seconds())  # No dst support, but added the 2 default hours of estonia
            player_url = self._search_regex('[^\0]embedSWF\("([^"]+)[^\0]', webpage, 'player_url', default=None)

        # There are videos that can only be seen when logged in, so some data can't be accessed(but we can still download the video)
        else:
            # Try to get description from api(which is mostly empty result) or in other case from og meta tag.
            description = xpath_text(xmlfile, './playlist/video/description') or self._search_regex('[^\0]og:description"[^\0]*content="(.*)\" \/>', webpage, 'description', default=None)
            # Basic character parsing to turn character references into real characters. also remove excessive whitespace
            if description is not None:
                description = description.strip().replace("&otilde;", "õ").replace("&Otilde;", "Õ").replace("&auml;", "ä").replace("&Auml;", "Ä").replace("&ouml;", "ö").replace("&Ouml;", "Ö").replace("&uuml;", "ü").replace("&Uuml;", "Ü").replace("&amp;", "&")

            player_url = None
            episode = int_or_none(xpath_text(xmlfile, './playlist/video/episode')) or None
            season = None  # Episode is mostly empty in the xml but season does not even appear there
            timestamp = None
        return {
            'app': "kanal2vod",
            'average_rating': average_rating,
            'description': description,
            'episode_number': episode,
            'ext': "flv",
            'height': height,
            'id': video_id,
            'page_url': url,
            'player_url': player_url,
            'play_path': "mp4:" + streamname,
            'protocol': "rtmp",
            'rtmp_real_time': True,
            'season_number': season,
            'timestamp': timestamp,
            'title': xpath_text(xmlfile, './playlist/video/name'),
            'thumbnail': thumbnail,
            'url': xmlfile.find('./playlist/video/streamItems').get('host') + streamname,
            'width': width,
        }
