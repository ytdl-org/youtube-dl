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
from .service import Service ##


class WebDriver(RemoteWebDriver):
    """
    Controls the SafariDriver and allows you to drive the browser.

    """

    def __init__(self, port=0, executable_path="/usr/bin/safaridriver", reuse_service=False,
                 desired_capabilities=DesiredCapabilities.SAFARI, quiet=False):
        """

        Creates a new Safari driver instance and launches or finds a running safaridriver service.

        :Args:
         - port - The port on which the safaridriver service should listen for new connections. If zero, a free port will be found.
         - quiet - If True, the driver's stdout and stderr is suppressed.
         - executable_path - Path to a custom safaridriver executable to be used. If absent, /usr/bin/safaridriver is used.
         - desired_capabilities: Dictionary object with desired capabilities (Can be used to provide various Safari switches).
         - reuse_service - If True, do not spawn a safaridriver instance; instead, connect to an already-running service that was launched externally.
        """

        self._reuse_service = reuse_service
        self.service = Service(executable_path, port=port, quiet=False)  ##

        if not reuse_service:
            self.service.start()

        RemoteWebDriver.__init__(
            self,
            command_executor=self.service.service_url,
            desired_capabilities=desired_capabilities)
        self._is_remote = False

    def quit(self):
        """
        Closes the browser and shuts down the SafariDriver executable
        that is started when starting the SafariDriver
        """
        try:
            RemoteWebDriver.quit(self)
        except http_client.BadStatusLine:
            pass
        finally:
            if not self._reuse_service:
                self.service.stop()
