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

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from .service import Service


class WebDriver(RemoteWebDriver):
    """
    Controls the WebKitGTKDriver and allows you to drive the browser.
    """

    def __init__(self, executable_path="WebKitWebDriver", port=0, options=None,
                 desired_capabilities=DesiredCapabilities.WEBKITGTK,
                 service_log_path=None):
        """
        Creates a new instance of the WebKitGTK driver.

        Starts the service and then creates new instance of WebKitGTK Driver.

        :Args:
         - executable_path : path to the executable. If the default is used it assumes the executable is in the $PATH.
         - port : port you would like the service to run, if left as 0, a free port will be found.
         - options : an instance of WebKitGTKOptions
         - desired_capabilities : Dictionary object with desired capabilities
         - service_log_path : Path to write service stdout and stderr output.
        """
        if options is not None:
            capabilities = options.to_capabilities()
            capabilities.update(desired_capabilities)
            desired_capabilities = capabilities

        self.service = Service(executable_path, port=port, log_path=service_log_path)
        self.service.start()

        RemoteWebDriver.__init__(
            self,
            command_executor=self.service.service_url,
            desired_capabilities=desired_capabilities)
        self._is_remote = False

    def quit(self):
        """
        Closes the browser and shuts down the WebKitGTKDriver executable
        that is started when starting the WebKitGTKDriver
        """
        try:
            RemoteWebDriver.quit(self)
        except http_client.BadStatusLine:
            pass
        finally:
            self.service.stop()
