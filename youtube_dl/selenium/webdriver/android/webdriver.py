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

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class WebDriver(RemoteWebDriver):
    """
    Simple RemoteWebDriver wrapper to start connect to Selendroid's WebView app

    For more info on getting started with Selendroid
    http://selendroid.io/mobileWeb.html
    """

    def __init__(self, host="localhost", port=4444, desired_capabilities=DesiredCapabilities.ANDROID):
        """
        Creates a new instance of Selendroid using the WebView app

        :Args:
         - host - location of where selendroid is running
         - port - port that selendroid is running on
         - desired_capabilities: Dictionary object with capabilities
        """
        RemoteWebDriver.__init__(
            self,
            command_executor="http://%s:%d/wd/hub" % (host, port),
            desired_capabilities=desired_capabilities)
