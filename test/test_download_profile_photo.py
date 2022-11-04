#!/usr/bin/env python

# Allow direct execution
import os
import sys
from pathlib import Path
import shutil
import subprocess
# import unittest
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from test.helper import (
#     assertGreaterEqual,
#     expect_warnings,
#     get_params,
#     gettestcases,
#     expect_info_dict,
#     try_rm,
#     report_warning,
# )


# import hashlib
# import io
# import json
# import socket

# import youtube_dl.YoutubeDL

# from youtube_dl.compat import (
#     compat_http_client,
#     compat_urllib_error,
#     compat_HTTPError,
# )
# from youtube_dl.utils import (
#     DownloadError,
#     ExtractorError,
#     format_bytes,
#     UnavailableVideoError,
# )
# from youtube_dl.extractor import get_info_extractor

class TestDownloadProfilePhoto():
    def __init__(self, url, channelName, options = ""):
        self.correctTests = 0
        self.totalTests = 5

        self.url = url
        self.channelName = channelName
        self.options = options
        self.dir = Path(os.getcwd())
        self.parent_dir = self.dir.parent.absolute()

        
        
        self. p_folder = os.path.join(self.parent_dir, "profile_pictures")

       
    def set_url(self, url):
        self.url = url

    def set_channelName(self, channelName):
        self.channelName = channelName
    
    def set_options(self, options):
        self.options = options

    def test_download_profile_video(self):

        if os.path.exists(self.p_folder):
            shutil.rmtree(self.p_folder)

        os.chdir(self.parent_dir)
        os.system('python3 youtube_dl ' + self.options + ' "' + self.url + '"')
        os.chdir(self.dir)
        dir = os.path.join(self.parent_dir, "profile_pictures")
        

        if os.path.isfile(os.path.join(dir, self.channelName + ".png")):
            print("Profile Download Test Passed!")
        elif os.path.isfile(os.path.join(dir, "1.png")):
            print("Profile Download Test Passed!")
        else:
            if len(self.channelName):
                print("Error: Could not find profile photo")
                exit(1)
            else:
                #If the channelName is not supplied, it should not retrieve a profile picture
                print("Test case passed!")  

if __name__ == "__main__":

    # Test if profile downloader works correctly on youtube video
    tester = TestDownloadProfilePhoto("https://www.youtube.com/watch?v=r5mx6JOn7vI", "CryptoRevolution", options = "--profile-picture True")
    tester.test_download_profile_video()
    
    #Testing to make sure no errors for non-youtube sites
    tester.set_url("https://vimeo.com/4378389")
    tester.set_channelName("")
    tester.test_download_profile_video()
    
    #Testing to make sure no errors on playlists (download profile photo currently does not work with playlists)
    tester.set_url("https://www.youtube.com/watch?v=GU0DhAlYCyI&list=PLh9R-kdGXNL4re22eMuWzQkapepohLWEu")
    tester.set_options("--profile-picture True --yes-playlist")
    tester.test_download_profile_video()







        

        


