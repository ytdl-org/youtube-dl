# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
    int_or_none,
    sanitize_filename,
    std_headers
)

import hashlib


import shutil
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import time
import httpx


class NetDNAIE(InfoExtractor):
    IE_NAME = "netdna"
    _VALID_URL = r'https?://(www\.)?netdna-storage\.com/f/(?P<id>[^/]+)/.*'
    _DICT_BYTES = {'KB': 1024, 'MB': 1024*1024, 'GB' : 1024*1024*1024}

    def _real_extract(self, url):
        
        # options = Options()
        # options.add_argument(f"user-agent={std_headers['User-Agent']}")
        # #options.add_argument("headless=True")
        # options.add_argument("user-data-dir=/Users/antoniotorres/Library/Application Support/Google/Chrome")
        
        # driver = webdriver.Chrome(executable_path=shutil.which('chromedriver'),options=options)
        opts = Options()
        opts.headless = True
        profile = "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/oo5x1t4e.selenium"
        driver = Firefox(options=opts, firefox_profile=profile)
                        
        #videoid = self._search_regex(self._VALID_URL, url, 'videoid',default=None, fatal=False, group='id')
        
        self.report_extraction(url)
        
        try:
        
            driver.get(url)

            wait = WebDriverWait(driver, 30)

            try:
                el1 = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "DOWNLOAD")))
                    
            except Exception as e:
                pass
            el11 = driver.find_element_by_xpath("/html/body/section[1]/div[1]/header/h1")
            el12 = driver.find_element_by_xpath("/html/body/section/div[1]/header/p/strong")
            title = el11.text.split('.')[0].replace("-", "_")
            ext = el11.text.split('.')[1].lower()
            est_size = el12.text.split(' ')
            
            self.to_screen(f"[redirect] {el1.get_attribute('href')}")
            driver.get(el1.get_attribute('href'))
            time.sleep(1)
            try:
                el2 = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "CONTINUE")))
            except Exception as e:
                pass

            self.to_screen(f"[redirect] {el2.get_attribute('href')}")
            driver.get(el2.get_attribute('href'))
            time.sleep(5)
            try:
                el3 = wait.until(ec.element_to_be_clickable((By.ID,"btn-main")))
            except Exception as e:
                pass
            el3.click()
            time.sleep(5)
            try:
                el4 = wait.until(ec.element_to_be_clickable((By.ID, "btn-main")))
            except Exception as e:
                pass

            el4.click()
            time.sleep(1)
            try:
                el5 = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "DOWNLOAD")))
            except Exception as e:
                pass

            self.to_screen(f"[redirect] {driver.current_url}")
            video_url = el5.get_attribute('href')
            
            #videoid = re.findall(r'download/([^\/]+)/', video_url)[0]
            
            #vid = driver.find_element_by_xpath("/html/head/meta[4]").get_attribute('content')
            
            str_id = f"{title}{est_size[0]}"
            videoid = int(hashlib.sha256(str_id.encode('utf-8')).hexdigest(),16) % 10**8
        
        except Exception as e:
            pass
        
        driver.close()
        driver.quit()
        
        try:
            
            res = httpx.head(video_url, headers={'User-Agent': std_headers['User-Agent']})
            if res.status_code >= 400:
                filesize = None
            else:
                filesize = int(res.headers.get('content-length', None))
        except Exception as e:
            filesize = None
        
        if not filesize:
            filesize = float(est_size[0])*self._DICT_BYTES[est_size[1]]
            self.to_screen(est_size)
            self.to_screen(self._DICT_BYTES[est_size[1]])
            self.to_screen(filesize)

        format_video = {
            'format_id' : "http-mp4",
            'url' : video_url,
            'filesize' : filesize,
            'ext' : ext
        }
        
        return {
            'id': str(videoid),
            'title': sanitize_filename(title,restricted=True),
            'formats': [format_video],
            'ext': ext
        }