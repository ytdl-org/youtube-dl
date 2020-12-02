from __future__ import unicode_literals

import json
import requests

from .common import InfoExtractor
from ..utils import ExtractorError

import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class OnlyFansPlaylistIE(InfoExtractor):
    IE_NAME = 'onlyfans'
    IE_DESC = 'onlyfans'
    _VALID_URL = r"https?://(?:www\.)?onlyfans.com"
        
    _SITE_URL = "https://onlyfans.com/"
    _DRIVER_PATH = "/usr/local/bin/chromedriver"

    _APP_TOKEN = "33d57ade8c02dbc5a333db99ff9ae26a"

    #log in via twitter
    _NETRC_MACHINE = 'twitter2'
    
    _USER_ID = "4090129"

    def __init__(self):
        
        self.driver_path = self._DRIVER_PATH
        options = Options()
        options.page_load_strategy = 'eager'
        options.headless = True
        self.driver = webdriver.Chrome(executable_path=self.driver_path,chrome_options=options)
        self.driver.implicitly_wait(10) # seconds
        
        #To get things working we need to use the same user agent in the requests
        self.user_agent = self.driver.execute_script("return navigator.userAgent")
        self.app_token = self._APP_TOKEN
        self.twitter_xpath ="/html/body/div[1]/div[1]/div[1]/div/div/div/form/a[1]"
        self.username_xpath = "/html/body/div[2]/div/form/fieldset[1]/div[1]/input"
        self.password_xpath = "/html/body/div[2]/div/form/fieldset[1]/div[2]/input"
        self.login_xpath = "/html/body/div[2]/div/form/fieldset[2]/input[1]"
    
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

        except Exception as e:
            print(e)
            return
                
   
    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
 
        try:

            user_account = url.split("/")[3]
            #self.driver.maximize_window()

            cookies = self.driver.get_cookies()
            s = requests.Session()
            for cookie in cookies:
                #print(cookie)
                s.cookies.set(cookie['name'], cookie['value'])
            s.headers.update({
                "Accept":"application/json, text/plain, */*",
                "User-Agent": self.user_agent,
                })
            r = s.request("GET","https://onlyfans.com/api2/v2/users/" + user_account + "?" + "app-token=" + self.app_token, timeout=60)
            #print(r.text)
            #print(s.headers)

            
            #dict_headers = {"Accept":"application/json, text/plain, */*"}
            #self.driver._client.set_header_overrides(headers=dict_headers)
            #user_account = url.split("/")[3]
            #url_getuser = "https://onlyfans.com/api2/v2/users/" + user_account + "?" + "app-token=" + self.app_token
            #self.driver.get(url_getuser)
            #wait = WebDriverWait(self.driver, 120)
            #pre = wait.until(ec.presence_of_element_located( (By.TAG_NAME, 'pre') ))
            #data_user = json.loads(pre.text)
            data_user = json.loads(r.text)
            user_id = data_user['id']
            n_videos = int(data_user['videosCount'])
            #print(n_videos)
            #input('wait')
            #self.driver.add_cookie({"name": "wallLayout", "value": "list"})
            s.cookies.set("wallLayout", "list")
            url_getvideos_base = "https://onlyfans.com/api2/v2/users/" + str(user_id) + "/posts/videos?limit=100&order=publish_date_desc&skip_users=all&skip_users_dups=1&pinned=0&app-token=" + self.app_token
            url_getvideos = url_getvideos_base
            time3 = ""
            data_videos = []
           
            s.headers["user-id"] = self._USER_ID
            s.headers["Referer"] = url + "/videos"
            s.headers["Origin"] = self._SITE_URL
            s.headers["Access-Token"] = s.cookies['sess']
            
            #print(s.headers)

            self.to_screen("Found " + str(n_videos))
            self.to_screen("Fetching video details for download")

            for i in range(0, (n_videos//100 + 1)):


                #self.driver.get(url_getvideos)
                #wait = WebDriverWait(self.driver, 120)
                #pre = wait.until(ec.presence_of_element_located( (By.TAG_NAME, 'pre') ))
                #print(i)
                #print(url_getvideos)
                #input('wait')
                #a = [s, url_getvideos, sess, self._USER_AG]
                #s = create_sign(*a)
                r = s.request("GET", url_getvideos, timeout=60)
                #data_videos.extend(json.loads(pre.text))
                #print(r.text)
                data_videos.extend(json.loads(r.text))
                time3 = data_videos[-1]["postedAtPrecise"]
                url_getvideos = url_getvideos_base + "&beforePublishTime=" + str(time3)  

            #with open(str(user_id) + "_" + user_account + ".json", "w") as outfile:
            #    json.dump(data_videos, outfile, indent=6)

            entries = []

            for post in data_videos:
                if ( post['media'][0]['type'] == 'video' ):
                    urlvideo = post['media'][0]['info']['source']['source']
                    idvideo = post['media'][0]['id']
                    datevideo = post['postedAt'].split('T')[0]
                    filesize = s.request("HEAD",urlvideo).headers['content-length']
                    width = post['media'][0]['info']['source']['width']
                    height = post['media'][0]['info']['source']['height']


                    entries.append({
                        "_type" : "video",
                        "id" :  str(idvideo),
                        "title" : datevideo + "_" + user_account,
                        "url" : urlvideo,
                        "filesize" :int(filesize),
                        "width" : width,
                        "height" : height
                    })

            

            return self.playlist_result(entries, "Onlyfans:" + user_account, "Onlyfans:" + user_account)


        except Exception as e:
            print(e)