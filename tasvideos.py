from .common import InfoExtractor
import re
from ..utils import (
    ExtractorError)

class TasVideosPlaylistIE(InfoExtractor):
#    _VALID_URL = r'http://tasvideos.org/2529M.html'
    _VALID_URL = r'(http:\/\/)(tasvideos\.org\/(?P<id>Movies-))((?!html).?)+(\.html)'

#    _VALID_URL = r'https?:\/\/(?:www)?tasvideos\.org.*M.*\.html'
    IE_NAME = 'IDKsomethingtodowithvideo??'

    def _real_extract(self, url):
 #       print("TasVideosIEdeo)")
        video_id = self._match_id(url)
        print("video_id is:")
        print(video_id)
        webpage = self._download_webpage(url, video_id)
        mobj = re.search('(?P<URL>archive\.org\/download\/[^\/]*\/[^\/]*\.mkv)',webpage)
        print(mobj.group())
        matches =  re.findall('(?P<URL>archive\.org\/download\/[^\/]*\/[^\/]*\.mkv)',webpage)
        initial_list = []
        for link in matches:
            url_dict = {'_type': 'url', 'url' : link }
            initial_list.append(url_dict)
        print("initial list:",initial_list)
        new_playlist_result = {'_type': 'playlist', 'entries': 'placeholder'}
        new_playlist_result.update({'entries' : initial_list})
        print(new_playlist_result)
        if (mobj != None):
            download_link = "http://" + mobj.group('URL')
        #print("couldn't get download link")
            vid_title = re.search('<span title="Movie #\d+">(?P<TITLE>.+?)<\/span>'
                , webpage)
            title = vid_title.group('TITLE')
        else:
            download_link = 'Couldn\'t find download link'
            title = 'Couldn\'t find a title'

        entries = {'_type': 'url', 'url': 'http://players.brightcove.net/2385340575001/ce10c91c-c518-4eaf-bcca-71af09a3d116_default/index.html?videoId=3974085541001', 'ie_key': 'BrightcoveNew'}

        self.playlist_result(entries, 69)
        playlist_result = {'_type': 'playlist', 'entries': [{'_type': 'url', 'url': 'http://archive.org/download/MasterjunsWindowsVvvvvvgameEndGlitchIn0045.33/vvvvvv-tas-gameend-masterjun.mkv'}, {'_type': 'url', 'url': 'http://archive.org/download/IlariEncodingTASVideosMovies5/syobonaction-tas-happymariotehh083_10bit444.mkv'}]}
        return (new_playlist_result)



class TasVideosVideoIE(InfoExtractor):
#    _VALID_URL = r'(http:\/\/)(tasvideos\.org\/(?P<id>Movies-))((?!html).?)+(\.html)'
 #   _VALID_URL = r'http://tasvideos.org/(?P<id>\d{4}M)\.html'
    _VALID_URL = r'http://tasvideos.org/(?P<id>\d+M).html'

    IE_NAME = 'tasvideo:video'

    def _real_extract(self, url):
        print("TasVideosIE selected! (playlist)")
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        mobj = re.search('(?P<URL>archive\.org\/download\/[^\/]*\/[^\/]*\.mkv)',webpage)
        print(mobj)
        if (mobj != None):
            download_link = "http://" + mobj.group('URL')
        #print("couldn't get download link")
            vid_title = re.search('<span title="Movie #\d+">(?P<TITLE>.+?)<\/span>'
                , webpage)
            title = vid_title.group('TITLE')
        else:
            download_link = 'Couldn\'t find download link'
            title = 'Couldn\'t find a title'

        entries = {'_type': 'url', 'url': 'http://players.brightcove.net/2385340575001/ce10c91c-c518-4eaf-bcca-71af09a3d116_default/index.html?videoId=3974085541001', 'ie_key': 'BrightcoveNew'}

        self.playlist_result(entries, 69)
        playlist_result = {'_type': 'playlist', 'entries': [{'_type': 'url', 'url': 'http://archive.org/download/MasterjunsWindowsVvvvvvgameEndGlitchIn0045.33/vvvvvv-tas-gameend-masterjun.mkv'}, {'_type': 'url', 'url': 'http://archive.org/download/IlariEncodingTASVideosMovies5/syobonaction-tas-happymariotehh083_10bit444.mkv'}], 'id': '3286'}


        return {
            'id': video_id,
            'title': title,
            'description': 'description',
            'thumbnail': 'thumbnail',
            'uploader': 'uploader',
            'upload_date': '19960831',
            'formats' : [{'url': download_link}]

        }        
        
