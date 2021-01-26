from __future__ import unicode_literals

import json
import requests

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    std_headers,
    

)

import selenium
import re

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from pathlib import Path

from rclone import RClone

class OnlyFansBaseIE(InfoExtractor):

    _SITE_URL = "https://onlyfans.com/"
    _DRIVER_PATH = "/usr/local/bin/chromedriver"
    _COOKIES_PATH = Path(Path.home(), "testing/cookies.json")

    _APP_TOKEN = "33d57ade8c02dbc5a333db99ff9ae26a"

    #log in via twitter
    _NETRC_MACHINE = 'twitter2'
    
    _USER_ID = "4090129"

       
    def __init__(self):
        
        self.app_token = self._APP_TOKEN
        self.session = requests.Session()
        
        self.twitter_xpath ="/html/body/div[1]/div[1]/div[1]/div/div/div/form/a[1]"
        self.username_xpath = "/html/body/div[2]/div/form/fieldset[1]/div[1]/input"
        self.password_xpath = "/html/body/div[2]/div/form/fieldset[1]/div[2]/input"
        self.login_xpath = "/html/body/div[2]/div/form/fieldset[2]/input[1]"

        self.cookies = []
        self.driver = ""
        self.user_agent = ""
        
        try:
            with open(self._COOKIES_PATH, "r") as f:
                    self.cookies = json.load(f)
                    #print(self.cookies)
            self.user_agent = self.cookies[-1]['value']
            std_headers['User-Agent'] = self.user_agent
                    

        except Exception as e:
            print("Cookies file not found. Lets log in")        
        
        if not self.cookies:
            options = Options()
            options.page_load_strategy = 'eager'
            options.headless = True
            self.driver = webdriver.Chrome(executable_path=self._DRIVER_PATH,chrome_options=options)
            self.driver.implicitly_wait(10) # seconds
            self.user_agent = self.driver.execute_script("return navigator.userAgent")
        
           
    def _copy_cookies_gdrive(self):

        rc = RClone()
        res = rc.copy(self._COOKIES_PATH, "gdrive:Temp")
      
    
    def _login(self):

        username, password = self._get_login_info()
    
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        self.report_login()

        try:
            self.driver.get(self._SITE_URL)
            #self.driver.wait_for_request('onlyfans.com', timeout=3600)
            wait = WebDriverWait(self.driver, 120)
            twitter_element = wait.until(ec.visibility_of_element_located(
                (By.XPATH, self.twitter_xpath) ))
            #twitter_element = self.driver.find_element_by_xpath(self.twitter_xpath)
            twitter_element.click()
            wait = WebDriverWait(self.driver, 120)
            #self.driver.wait_for_request('api.twitter.com', timeout=3600)
            #username_element = self.driver.find_element_by_xpath(self.username_xpath)
            username_element = wait.until(ec.visibility_of_element_located(
                (By.XPATH, self.username_xpath) ))
            username_element.send_keys(username)
            password_element = self.driver.find_element_by_xpath(self.password_xpath)
            password_element.send_keys(password)
            login_element = self.driver.find_element_by_xpath(self.login_xpath)
            login_element.click()
            WebDriverWait(self.driver, 120).until(ec.staleness_of(login_element))

            self.cookies = self.driver.get_cookies()
            self.cookies.append({"name": "user-agent", "value" : self.user_agent}) 
            json.dump(self.cookies, open(self._COOKIES_PATH, "w"))
            self._copy_cookies_gdrive()

        except Exception as e:
            print(e)

        return

    def _extract_from_json(self, data_post, acc=None):

        info_dict = []
        
        if data_post['media'][0]['type'] == 'video':
        
            if acc:
                account = acc
            else:
                account = data_post['author']['username']
            
            datevideo = data_post['postedAt'].split("T")[0]
            videoid = str(data_post['id'])


            formats = []
            
            try:

                filesize = None
                try:
                    filesize = int(self.session.request("HEAD", data_post['media'][0]['info']['source']['source']).headers['content-length'])
                except Exception as e:
                    pass
                formats.append({
                    'format_id': "http-mp4",
                    'url': data_post['media'][0]['info']['source']['source'],
                    'width': data_post['media'][0]['info']['source']['width'],
                    'height': data_post['media'][0]['info']['source']['height'],
                    'filesize': filesize,
                    'format_note' : "source original"
                })
            except Exception as e:
                    print(e)
                    print("No source video format")

            try:
                    
                if data_post['media'][0]['videoSources']['720']:
                    filesize = None
                    try:
                        filesize = int(self.session.request("HEAD",data_post['media'][0]['videoSources']['720']).headers['content-length'])
                    except Exception as e:
                        pass
                    formats.append({
                        'format_id': "http-mp4",
                        'url': data_post['media'][0]['videoSources']['720'],
                        'width': data_post['media'][0]['info']['source']['width'],
                        'height': data_post['media'][0]['info']['source']['height'],
                        'format_note' : "source 720",
                        'filesize': filesize,
                    })

            except Exception as e:
                    print(e)
                    print("No info for 720p format")

            try:
                if data_post['media'][0]['videoSources']['240']:
                    filesize = None
                    try:
                        filesize = int(self.session.request("HEAD",data_post['media'][0]['videoSources']['240']).headers['content-length'])
                    except Exception as e:
                        pass
                    formats.append({
                        'format_id': "http-mp4",
                        'url': data_post['media'][0]['videoSources']['240'],
                        'format_note' : "source 240",
                        'filesize': filesize,
                    })

            except Exception as e:
                print(e)
                print("No info for 240p format")
            
           # self._check_formats(formats, videoid)
            if formats:
                self._sort_formats(formats)
            
                info_dict = {
                    "id" :  str(videoid),
                    "title" : datevideo + "_" + account,
                    "formats" : formats
                }

        return info_dict

class OnlyFansResetIE(OnlyFansBaseIE):
    IE_NAME = 'onlyfans:reset'
    IE_DESC = 'onlyfans:reset'
    _VALID_URL = r"onlyfans:reset"

    def _real_initialize(self):

        self.cookies = []
        options = Options()
        options.page_load_strategy = 'eager'
        options.headless = True
        self.driver = webdriver.Chrome(executable_path=self._DRIVER_PATH,chrome_options=options)
        self.driver.implicitly_wait(10) # seconds
        self.user_agent = self.driver.execute_script("return navigator.userAgent")
        self._login()
    

class OnlyFansPostIE(OnlyFansBaseIE):
    IE_NAME = 'onlyfans:post'
    IE_DESC = 'onlyfans:post'
    #_VALID_URL = r"https?://(?:www\.)?onlyfans.com/post/(?P<post>\d{8})"
    #_VALID_URL = r"(onlyfans:post:(?P<post>.*?):(?P<account>.*?))|(https?://(?:www\.)?onlyfans.com/(?P<post>.*?)/(?P<account>.*?))"
    _VALID_URL =  r"(?:(onlyfans:post:(?P<post>.*?):(?P<account>[\da-zA-Z]+))|(https?://(?:www\.)?onlyfans.com/(?P<post2>[\d]+)/(?P<account2>[\da-zA-Z]+)))"

    def _real_initialize(self):
        if not self.cookies:  
            self._login()

    def _real_extract(self, url):
 
        try:

            for cookie in self.cookies:
                #print(cookie)
                #cookie_obj = requests.cookies.create_cookie(domain="onlyfans.com", name=cookie['name'], value=cookie['value'])
               if not "user-agent" in cookie['name']:
                   self.session.cookies.set(cookie['name'], cookie['value'])
            self.session.headers.update({
                "Accept":"application/json, text/plain, */*",
                "User-Agent": self.user_agent,
                })

            post = re.search(self._VALID_URL, url).group("post")
            if not post:
                post = re.search(self._VALID_URL, url).group("post2")
            account = re.search(self._VALID_URL, url).group("account")
            if not account:
                account = re.search(self._VALID_URL, url).group("account2")

            #print("post:" + post + ":" + "account:" + account)
            #input("")

            self.session.headers["user-id"] = self._USER_ID
            self.session.headers["Referer"] = self._SITE_URL + post + "/" + account
            self.session.headers["Origin"] = self._SITE_URL
            self.session.headers["Access-Token"] = self.session.cookies['sess']

            #print(self.session.headers)
            #print(self.session.cookies)

            r = self.session.request("GET","https://onlyfans.com/api2/v2/posts/" + post + \
                "?skip_users_dups=1&app-token=" + self.app_token, timeout=60)

            #print(r.text)

            data_post = json.loads(r.text)
            #print(data_post)
            
            return self._extract_from_json(data_post)

        except Exception as e:
            print(e)

class OnlyFansPlaylistIE(OnlyFansBaseIE):
    IE_NAME = 'onlyfans:playlist'
    IE_DESC = 'onlyfans:playlist'
    #_VALID_URL = r"https?://(?:www\.)?onlyfans.com/account/(?P<account>[^/]+)"
    _VALID_URL = r"(?:(onlyfans:account:(?P<account>[^:]+)(?:(:(?P<mode>(?:date|favs|tips)))?))|(https?://(?:www\.)?onlyfans.com/(?P<account2>\w+)(?:(/(?P<mode2>(?:date|favs|tips)))?)$))"
    _MODE_DICT = {"favs" : "favorites_count_desc", "tips" : "tips_summ_desc", "date" : "publish_date_desc", "latest10" : "publish_date_desc"}
           
   
    def _real_initialize(self):
        if len(self.cookies) == 0:
            self._login()

    def _real_extract(self, url):
 
        try:

            account = re.search(self._VALID_URL, url).group("account")
            if not account:
                account = re.search(self._VALID_URL, url).group("account2")
            #self.driver.maximize_window()
            #print("Acc: " + account)
            #cookies = self.driver.get_cookies()
            #json.dump(cookies, open("cookies.json", "w"))
            mode = re.search(self._VALID_URL, url).group("mode")
            if not mode:
                mode = re.search(self._VALID_URL, url).group("mode2")
                if not mode:
                    mode = "latest10"
           #print(f"mode: {mode}")
            for cookie in self.cookies:
                #print(cookie)
                if not "user-agent" in cookie['name']:
                   self.session.cookies.set(cookie['name'], cookie['value'])
            self.session.headers.update({
                "Accept":"application/json, text/plain, */*",
                "User-Agent": self.user_agent,
                })
            r = self.session.request("GET","https://onlyfans.com/api2/v2/users/" + account + "?" + "app-token=" + self.app_token, timeout=60)

            data_user = json.loads(r.text)
            user_id = data_user['id']
            n_videos = int(data_user['videosCount'])
            
            self.session.cookies.set("wallLayout", "list")

            self.session.headers["user-id"] = self._USER_ID
            self.session.headers["Referer"] = self._SITE_URL + "/" + account + "/videos"
            self.session.headers["Origin"] = self._SITE_URL
            self.session.headers["Access-Token"] = self.session.cookies['sess']
            
            data_videos = [] 
            
            if mode=="date":


                url_getvideos_base = "https://onlyfans.com/api2/v2/users/" + str(user_id) + "/posts/videos?limit=100&order=" + self._MODE_DICT.get("date") + "&skip_users=all&skip_users_dups=1&pinned=0&app-token=" + self.app_token
                url_getvideos = url_getvideos_base
                time3 = ""                          

                
                #print(self.session.headers)

                self.to_screen("Found " + str(n_videos))
                self.to_screen("Fetching video details for download")

                for i in range(0, (n_videos//100 + 1)):

                   #print(url_getvideos)
                    r = self.session.request("GET", url_getvideos, timeout=60)
                   #print(r)
                    if r:
                        data_videos.extend(json.loads(r.text))
                        time3 = data_videos[-1]["postedAtPrecise"]
                        url_getvideos = url_getvideos_base + "&beforePublishTime=" + str(time3)  
                    else:
                        raise ExtractorError("No videos")
                        break
                #with open(str(user_id) + "_" + account + ".json", "w") as outfile:
                #     json.dump(data_videos, outfile, indent=6)

            elif mode=="favs" or mode=="tips" or mode=="latest10":

                

                url_getvideos = "https://onlyfans.com/api2/v2/users/" + str(user_id) + "/posts/videos?limit=10&order=" + self._MODE_DICT.get(mode) + "&skip_users=all&skip_users_dups=1&pinned=0&app-token=" + self.app_token
               #print(url_getvideos)
                r = self.session.request("GET", url_getvideos, timeout=60)
               #print(r)
                if r:
                    data_videos.extend(json.loads(r.text))
                else:
                    raise ExtractorError("No videos")
                    



            entries = []

            for post in data_videos:
                info = self._extract_from_json(post, account)
                if info:
                    entries.append(info)



            return self.playlist_result(entries, "Onlyfans:" + account, "Onlyfans:" + account)


        except Exception as e:
            print(e)