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


import shutil
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By


class GayBeegIE(InfoExtractor):
    IE_NAME = "gaybeeg"
    _VALID_URL = r'https?://(www\.)?gaybeeg\.info/?.*'
    
                
    def _real_extract(self, url):
        
        # options = Options()
        # options.add_argument(f"user-agent={std_headers['User-Agent']}")
        # options.add_argument("headless=True")
        # options.add_argument("user-data-dir=/Users/antoniotorres/Library/Application Support/Google/Chrome")
        # driver = webdriver.Chrome(executable_path=shutil.which('chromedriver'),options=options)
        opts = Options()
        opts.headless = True
        profile = "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/oo5x1t4e.selenium"
        driver = Firefox(options=opts, firefox_profile=profile)
        
        
        try:
        
            driver.get(url)
            
            wait = WebDriverWait(driver, 30)
            
                
            el_list = wait.until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))
                    

            entries = [self.url_result(el.get_attribute('href'), "NetDNA") for el in el_list if "dna-storage" in el.get_attribute('outerHTML')]
            
        except Exception as e:
            pass        
        
        driver.close()
        driver.quit()

        return {
            '_type': 'playlist',
            'id': "gaybeeg",
            'title': "gaybeeg",
            'entries': entries,
        }               


