# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError

print_debug = 1    # 1 to turn on debug notification printing


class ErrIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/(?:[a-z0-9]*)\.?err\.ee\/(?:[a-z0-9_-]*)\/(?:[a-z0-9_-]*)'

    # For testing run: "/test/test_download.py TestDownload.test_Err" and Err_1 and Err_2 ...
    _TESTS = [{
        # ETV recent
        'url': 'http://etv.err.ee/v/9f77d07c-9ed7-4b29-bac0-03ddee4f4675',
        'info_dict': {
            'id': '2016-000934-0611_Pealtnagija.mp4',
            'ext': 'mp4',
            'title': '2016-000934-0611_Pealtnagija.mp4'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }, {
        # ETV recent (folder: /gb/, pattern: sources)
        'url': 'http://etv.err.ee/v/dokumentaalfilmid/valisilma_dokk/saated/c4e742ef-262f-4e8b-9eb7-90415630eff8/valisilma-dokk-suur-plaan-eestilatileedu-2016',
        'info_dict': {
            'id': '2015-023708-0001_Suur_plaan.mp4',
            'ext': 'mp4',
            'title': '2015-023708-0001_Suur_plaan.mp4'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }, {
        # ETV archive (video)
        'url': 'http://arhiiv.err.ee/vaata/vurst-volkonski',
        'info_dict': {
            'id': '1990-082743-0001_0001_D10_VURST-VOLKONSKI.mp4',
            'ext': 'mp4',
            'title': '1990-082743-0001_0001_D10_VURST-VOLKONSKI.mp4'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }, {
        # ETV archive (audio)
        'url': 'https://arhiiv.err.ee/vaata/estraadikava-naisevott-raali-abil',
        'info_dict': {
            'id': 'a_108175_RMARHIIV.m4a',
            'ext': 'm4a',
            'title': 'a_108175_RMARHIIV.m4a'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }, {
        # Radios: Vikerraadio, R2
        'url': 'http://r2.err.ee/v/2tartutudengipaevad/saated/8c0e0116-2f67-43a4-8b74-8bf974510d6a/tudengi-45',
        'info_dict': {
            'id': 'RR2049iu7382.m4a',
            'ext': 'mp4',
            'title': 'RR2049iu7382.m4a'
        },
        'params': {
            'skip_download': 'requires rtmpdump'
        },
    }]

    def _real_extract(self, url):

        webpage = self._download_webpage(url, "1")
        webpage_folder = ""
        source_pattern = ""
        clean_pattern = ""

        # remember to change the definitions in source_pattern cleaning part too
        search_pattern1 = r'clip = {sources: ":[\',"]?([^\&" >]+)'
        search_pattern2 = r'file=[\',"]?([^\&" >]+)'
        search_pattern3 = r'AUDIO/[\',"]?([^\&" >]+)'
        search_pattern4 = r'arhiiv/[\',"]?([^\&" >]+)'
        search_pattern5 = r'"Source":":[\',"]?([^\&" >]+)'

        # here we search for data folder, after that we know what patterns to search for
        if webpage.find("/gb/") != -1:
            webpage_folder = "gb"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
            elif len(re.findall(search_pattern2, webpage)) > 0:
                source_pattern = search_pattern2
        elif webpage.find("/etvsaated/") != -1:
            webpage_folder = "etvsaated"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
            elif len(re.findall(search_pattern2, webpage)) > 0:
                source_pattern = search_pattern2
        elif webpage.find("/etv2saated/") != -1:
            webpage_folder = "etv2saated"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
            elif len(re.findall(search_pattern2, webpage)) > 0:
                source_pattern = search_pattern2
        elif webpage.find("/etvvideod/") != -1:
            webpage_folder = "etvvideod"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
        elif webpage.find("/etv2videod/") != -1:
            webpage_folder = "etv2videod"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
        elif webpage.find("/etvplussvideod/") != -1:
            webpage_folder = "etvplussvideod"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
        elif webpage.find("/uudised/") != -1:
            webpage_folder = "uudised"
            if len(re.findall(search_pattern1, webpage)) > 0:
                source_pattern = search_pattern1
        elif webpage.find("/AUDIO/") != -1:
            webpage_folder = "AUDIO"
            if len(re.findall(search_pattern2, webpage)) > 0:
                source_pattern = search_pattern2
            elif len(re.findall(search_pattern3, webpage)) > 0:
                source_pattern = search_pattern3
        elif webpage.find("/arhiiv/") != -1:
            webpage_folder = "arhiiv"
            if len(re.findall(search_pattern4, webpage)) > 0:
                source_pattern = search_pattern4
        elif webpage.find("/viker/") != -1:
            webpage_folder = "viker"
            if len(re.findall(search_pattern5, webpage)) > 0:
                source_pattern = search_pattern5
        elif webpage.find("/r2/") != -1:
            webpage_folder = "r2"
            if len(re.findall(search_pattern5, webpage)) > 0:
                source_pattern = search_pattern5
        elif webpage.find("/r4/") != -1:
            webpage_folder = "r4"
            if len(re.findall(search_pattern5, webpage)) > 0:
                source_pattern = search_pattern5

        # folder was found checks
        if webpage_folder == "":
            raise ExtractorError('[Err] No *webpage_folder* was found from webpage: webpage_folder = ' + webpage_folder)
        elif webpage_folder != "":
            if print_debug == 1:
                self.to_screen('[DEBUG] Found from webpage: webpage_folder = ' + webpage_folder)

            # source pattern found checks
            if source_pattern == "":
                raise ExtractorError('[Err] Found webpage: webpage_folder: ' + webpage_folder + ', no data for *source_pattern* found!')
            elif source_pattern != "":
                if print_debug == 1:
                    self.to_screen('[DEBUG] Found pattern from webpage: source_pattern = ' + source_pattern)

                # common BEFORE cleanup for all source_patterns
                clean_pattern_v = re.findall(source_pattern, webpage)
                clean_pattern = clean_pattern_v[0]
                clean_pattern = clean_pattern.strip("[]")

                # search_pattern1 = r'clip = {sources: ":[\',"]?([^\&" >]+)'
                if source_pattern == search_pattern1:
                    # ETV ERR clips, 3.05.2016
                    # http://etv.err.ee/v/meelelahutus/4x4_magadan/videod/6e716cab-ba91-40b0-b27b-262e369f3d5a
                    # clip = {sources: "://media.err.ee/etvvideod/@2013-08-06-magadan-kyla.mp4" }
                    clean_pattern_v = clean_pattern.split("/")
                    clean_pattern = clean_pattern_v[-1]

                # search_pattern2 = r'file=[\',"]?([^\&" >]+)'
                # elif source_pattern == search_pattern2:
                    # ETV new archive, 9. september 2014
                    # <iframe id="mediaframe" style="height: 390px;" src="http://static.err.ee/media?stream=media.err.ee:80/arhiiv/&amp;
                    # file=1990-082743-0001_0001_D10_VURST-VOLKONSKI.mp4&amp;mediaspace=mediaframe&amp;autoplay=true&amp;mediamode=wowzavideo&amp;site=arhiiv.err.ee&amp;image=http://arhiiv.err.ee//thumbnails/1990-082743-0001_0001_D10_VURST-VOLKONSKI.jpg" scrolling="no" frameborder="0" width="100%"></iframe>

                # search_pattern3 = r'AUDIO/[\',"]?([^\&" >]+)'
                # elif source_pattern == search_pattern3:
                    # ERR audio archive:
                    # http://arhiiv.err.ee/guid/86328
                    # https://static.err.ee/media?stream=media.err.ee:80/arhiiv/&amp;file=/AUDIO/a_86328_RMARHIIV.m4a
                    # stream=media.err.ee:80/arhiiv/     # file=/AUDIO/a_86328_RMARHIIV.m4a

                # search_pattern4 = r'arhiiv/[\',"]?([^\&" >]+)'
                # elif source_pattern == search_pattern4:
                    # ETV video archive, 2.05.2016
                    # http://arhiiv.err.ee/vaata/vurst-volkonski
                    # setPlayer("://media.err.ee:80/arhiiv/@1990-082743-0001_0001_D10_VURST-VOLKONSKI.mp4", '# fPlayer', player, false)

                # search_pattern5 = r'"Source":":[\',"]?([^\&" >]+)'
                elif source_pattern == search_pattern5:
                    # Vikerraadio, 5.05.2016
                    # http://vikerraadio.err.ee/v/ooylikool/saated/8e51ea8b-e3f5-4c80-856b-35348e35d47e/ooulikool-linda-madalik-akustikast
                    # localList[am] = {"Source":"://media.err.ee:80/viker/@2728431.m4a","MediaType"
                    clean_pattern_v = clean_pattern.split("/")
                    clean_pattern = clean_pattern_v[-1]

                # common AFTER cleanup for all source_patterns
                clean_pattern = clean_pattern.replace("@", " ").strip(" ").replace("%28", "(").replace("%29", ")")

                # source_pattern was cleaned to clean_pattern
                if clean_pattern == "":
                    raise ExtractorError('[Err] found webpage_folder = ' + webpage_folder + ', source_pattern ' + source_pattern + ', but NO *clean_pattern* = ' + clean_pattern)
                elif clean_pattern != "":
                    self.to_screen('Found data pattern: ' + clean_pattern)

                    # if clean_pattern.find("m4a") > 0: don't use this control, because this hack works only for webpage_folder /AUDIO/
                    if webpage_folder == "AUDIO":
                        # command =("rtmpdump -v -r "rtmp://media.err.ee:80/arhiiv/" -y "mp4:/' + webpage_folder + '/' + clean_pattern + '" -o "'+clean_pattern+'"")
                        audio_id = clean_pattern
                        audio_ext = "m4a"
                        audio_play_path = "mp4:/" + webpage_folder + "/" + clean_pattern
                        audio_title = clean_pattern
                        audio_url = "rtmp://media.err.ee:80/arhiiv/"    # don't change it to webpage_folder, it doesn't work so
                        if print_debug == 1:
                            self.to_screen('[DEBUG] Starting to download audio data from ' + audio_url)
                        return {                      # id, title, url are mandatory, ext is for beauty, ERR audio download is not working without play_path, last two ones help to download
                            'id': audio_id,
                            'title': audio_title,
                            'url': audio_url,
                            'ext': audio_ext,
                            'play_path': audio_play_path,
                            'no_resume': True,        # rtmpdump -e means --resume is set
                            'rtmp_live': True,        # rtmpdump -v means --live   is set
                            # TODO more properties(see youtube_dl/extractor/common.py)
                        }
                    else:
                        # command =("rtmpdump -v -e -r "rtmp://media.err.ee/' + webpage_folder + '/mp4:%s" -o "%s"' %(clean_pattern, clean_pattern) )
                        video_id = clean_pattern
                        video_ext = "mp4"
                        video_title = clean_pattern
                        video_url = "rtmp://media.err.ee/" + webpage_folder + "/mp4:" + clean_pattern
                        if print_debug == 1:
                            self.to_screen('[DEBUG] Starting to download video data from ' + video_url)
                        return {                       # id, title, url are mandatory, ext is for beauty, last two ones help to download
                            'id': video_id,            # Video identifier
                            'title': video_title,      # Video title, unescaped.
                            'url': video_url,          # Final video URL.
                            'ext': video_ext,          # Video filename extension.
                            'no_resume': False,        # rtmpdump -e means --resume is set
                            'rtmp_live': True,         # rtmpdump -v means --live   is set
                            # TODO more properties(see youtube_dl/extractor/common.py)
                        }
