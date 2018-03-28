# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
The ApplicationCache implementaion.
"""

from selenium.webdriver.remote.command import Command


class ApplicationCache(object):

    UNCACHED = 0
    IDLE = 1
    CHECKING = 2
    DOWNLOADING = 3
    UPDATE_READY = 4
    OBSOLETE = 5

    def __init__(self, driver):
        """
        Creates a new Aplication Cache.

        :Args:
         - driver: The WebDriver instance which performs user actions.
        """
        self.driver = driver

    @property
    def status(self):
        """
        Returns a current status of application cache.
        """
        return self.driver.execute(Command.GET_APP_CACHE_STATUS)['value']
