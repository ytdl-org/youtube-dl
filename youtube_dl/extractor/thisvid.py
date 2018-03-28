# coding: utf-8
from __future__ import unicode_literals
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..utils import (
    ExtractorError,
)
import re

from .common import InfoExtractor

# Process downloads from porn site ThisVid.com
# Requires Selenium (license Apache 2.0)

class thisvidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/videos/(?P<display_id>\w+)'
    _TEST = {
        'url': 'https://thisvid.com/videos/final-impact-3/',
        'md5': '8302bd736a1e4198ed80db4a0d0dd012',
        'info_dict': {
            'id': '490698',
            'ext': 'mp4',
            'title': 'Final impact_3',
        }
    }

    def try_find_element_attribute(self, driver, xpath, attr):
        # If attr is "_text_", get element text instead
        try:
            if attr == "_text_":
                return driver.find_element_by_xpath( xpath ).text
            else:
                return driver.find_element_by_xpath( xpath ).get_attribute( attr )
        except:
            return None

    def try_find_elements_attribute(self, driver, xpath, attr):
        # Same as try_find_element_attribute but for a list
        try:
            results = []
            objs = driver.find_elements_by_xpath( xpath )

            if attr == "_text_":
                for t in objs:
                    results.append(t.text)
            else:
                for t in objs:
                    results.append(t.get_attribute(attr))

            return results
        except:
            return None

    def _real_extract(self, url):
        dict = { 'age_limit': 18,
                'ext': 'mp4',
                 'extractor': 'ThisVid'}

        be_verbose = self._downloader.params.get('verbose', False)

        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        error_msg = ""
        driver = None
        source = ""
        wanted_driver = self._downloader.params.get('web_driver')
        w_driver = getattr(webdriver, wanted_driver.capitalize())
        if be_verbose:
            self.to_screen('Extractor started. Connecting to the selected browser (%s)' % wanted_driver)

        try:
            driver = w_driver()
            driver.get(url)
            source = driver.page_source
        except:
            error_msg = "Could not connect to the webdriver. Make sure you have installed the webdriver for '%s'" % wanted_driver
            pass

        # Check common errors
        if "SORRY, THE FILE DOES NOT EXIST YET" in source:
            # Error says 'yet' but removed files can also cause that error
            error_msg = "This file does not exist on Thisvid.com"
        elif "Sorry, this file was deleted" in source:
            error_msg = "This file has been deleted from Thisvid.com"
        elif "This video is a private video" in source:
            error_msg = "This video is private"

        if error_msg:
            if driver is not None:
                driver.quit()
            raise ExtractorError(
                'ThisVid said: %s' % error_msg,
                expected=True)

        # Click the Play button
        content = driver.find_element_by_class_name('fp-play')
        if content is not None:
            content.click()
        else:
            driver.quit()
            error_msg = "Page does not contain expected data"
            raise ExtractorError(
                'ThisVid said: %s' % error_msg,
                expected=True)

        try: # Until the true URL appears in the DOM
            element = WebDriverWait(driver, 30).until( EC.presence_of_element_located((By.CLASS_NAME, "fp-engine")))
        except:
            error_msg = "Browser timed out"
            driver.quit()
            raise ExtractorError(
                'ThisVid said: %s' % error_msg,
                expected=True)

        og_url = self.try_find_element_attribute( driver, "//meta[@property='og:video:url'][1]", "content" )
        hits = re.findall(r'/([0-9]+)/', og_url)
        video_id = hits[0]
        dict['id'] = video_id
        if be_verbose:
            self.to_screen("Found video id %s" % dict['id'])

        dict['url'] = self.try_find_element_attribute( driver, "//video[@class='fp-engine'][1]", "src" )

        video_title = self.try_find_element_attribute( driver, "//meta[@property='og:title'][1]", "content" )
        video_title = video_title[:len(video_title)-14] # Strip the last " - ThisVid.com" from the title
        dict['title'] = video_title

        # Gather other data
        try:
            elem_names = self.try_find_elements_attribute( driver, "//ul[@class='tools-left']/li/span[@class='title']", "_text_" )
            elem_values = self.try_find_elements_attribute( driver, "//ul[@class='tools-left']/li/span[@class='title-description']", "_text_" )
            hits = re.findall(r'Rating:\s([0-9]\.[0-9])', elem_names[0])
            video_rating = hits[0]

            dict['view_count'] = int( elem_values[0] )
            dict['release_date'] = elem_values[1]

            hits = re.findall(r'([0-9]+):([0-9]+)', elem_values[2])
            video_duration_in_seconds = int(hits[0][0])*60 + int(hits[0][1])
            dict['duration'] = video_duration_in_seconds

            dict['description'] = self.try_find_element_attribute(driver, "//meta[@property='og:description'][1]",
                                                                  "content")
            dict['tags'] = self.try_find_elements_attribute(driver, "//meta[@property='og:video:tag']", "content")
            dict['width'] = int(
                self.try_find_element_attribute(driver, "//meta[@property='og:video:width'][1]", "content"))
            dict['height'] = int(
                self.try_find_element_attribute(driver, "//meta[@property='og:video:height'][1]", "content"))
            dict['thumbnail'] = self.try_find_element_attribute(driver, "//meta[@property='og:image'][1]", "content")

            desc_block = driver.find_elements_by_xpath("//ul[@class='description']/li/a")

            dict['categories'] = [desc_block[0].text] # There is only one category per movie
            dict['uploader_id'] = desc_block[-1].text
            dict['uploader_url'] = desc_block[-1].get_attribute("href")

        except:
            self.to_screen("Exception while getting extra info")
            pass

        driver.quit()

        if be_verbose:
            self.to_screen("Will return the following data")
            self.to_screen( dict )

        return dict
