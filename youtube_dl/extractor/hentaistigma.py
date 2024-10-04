from __future__ import unicode_literals

from .common import InfoExtractor

##IFixThat additional imports (I insert them into every Extractor that I modify - can be removed if not needed)
import datetime
import os
import re
##IFixThat_end


class HentaiStigmaIE(InfoExtractor):
    _VALID_URL = r'^https?://hentai\.animestigma\.com/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://hentai.animestigma.com/inyouchuu-etsu-bonus/',
        'md5': '4e3d07422a68a4cc363d8f57c8bf0d23',
        'info_dict': {
            'id': 'inyouchuu-etsu-bonus',
            'ext': 'mp4',
            'title': 'Inyouchuu Etsu Bonus',
            'age_limit': 18,
        }
    }

    ##IFixThat general helper functions (I insert them into every Extractor that I modify - can be removed if not needed)

    def _ifixthat_helper_file_exists(self,filename):
        print('does '+filename+' exist?')
        if os.path.exists(filename):
            print('yes')
            return True
        else:
            print('no')
            return False

    def _ifixthat_helper_file_write(self,filename, content):
        if self._ifixthat_helper_file_exists(filename):
            print('backing up previous '+filename)
            os.rename(filename, filename+'.backup_'+datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        print('writing file')
        myfile = open(filename, "wt")
        myfile.write(content)
        myfile.close()

    def _ifixthat_helper_file_read(self,filename):
        if self._ifixthat_helper_file_exists(filename):
            myfile = open(filename, "rt")
            return myfile.read()
        else:
            return ''

    ##IFixThat_end

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<h2[^>]+class="posttitle"[^>]*><a[^>]*>([^<]+)</a>',
            webpage, 'title')

        ##IFixThat replacing 1st-iframe-search with all iframe-search

        #wrap_url = self._html_search_regex(
        #    r'<iframe[^>]+src="([^"]+mp4)"', webpage, 'wrapper url')
        #wrap_webpage = self._download_webpage(wrap_url, video_id)
        #video_url = self._html_search_regex(
        #    r'file\s*:\s*"([^"]+)"', wrap_webpage, 'video url')

        ##IFixThat >REPLACE<

        # foreach iframe do get source-src
        formats = []
        #print('-----------------------------------------------------------------------------------')
        mymatches = re.findall(r'<b> (SUB|RAW)</b></span><br/><iframe[^>]+src="([^"]+mp4)"', webpage)
        #print(mymatches)
        #print('-----------------------------------------------------------------------------------')
        for mymatch in mymatches:
            print('"'+mymatch[0]+'" : '+mymatch[1])
            wrap_webpage = self._download_webpage(mymatch[1], video_id)

            video_url = self._html_search_regex(
                #r'file\s*:\s*"([^"]+)"', wrap_webpage, 'video url')
                r'<source[^>]+src="([^"]+mp4)"[^>]+type=\'video/mp4\'>', wrap_webpage, 'video url')
                #e.g. <source src="https://v2.animestigma.com/videos/hd1/Inyouchuu_Etsu_-_Bonusssub.mp4" type="video/mp4">
            formats.append({
                    'url': video_url,
                    'format_id': 'mp4-'+mymatch[0],
                })

        ##IFixThat_end

        return {
            'id': video_id,
            ##IFixThat replace url with formats
            'formats': formats,
            'title': title,
            'age_limit': 18,
        }
