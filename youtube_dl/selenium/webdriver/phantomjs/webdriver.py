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

import warnings

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from .service import Service


class WebDriver(RemoteWebDriver):
    """
    Wrapper to communicate with PhantomJS through Ghostdriver.

    You will need to follow all the directions here:
    https://github.com/detro/ghostdriver
    """

    def __init__(self, executable_path="phantomjs",
                 port=0, desired_capabilities=DesiredCapabilities.PHANTOMJS,
                 service_args=None, service_log_path=None):
        """
        Creates a new instance of the PhantomJS / Ghostdriver.

        Starts the service and then creates new instance of the driver.

        :Args:
         - executable_path - path to the executable. If the default is used it assumes the executable is in the $PATH
         - port - port you would like the service to run, if left as 0, a free port will be found.
         - desired_capabilities: Dictionary object with non-browser specific
           capabilities only, such as "proxy" or "loggingPref".
         - service_args : A List of command line arguments to pass to PhantomJS
         - service_log_path: Path for phantomjs service to log to.
        """
        warnings.warn('Selenium support for PhantomJS has been deprecated, please use headless '
                      'versions of Chrome or Firefox instead')
        self.service = Service(
            executable_path,
            port=port,
            service_args=service_args,
            log_path=service_log_path)
        self.service.start()

        try:
            RemoteWebDriver.__init__(
                self,
                command_executor=self.service.service_url,
                desired_capabilities=desired_capabilities)
        except Exception:
            self.quit()
            raise

        self._is_remote = False

    def quit(self):
        """
        Closes the browser and shuts down the PhantomJS executable
        that is started when starting the PhantomJS
        """
        try:
            RemoteWebDriver.quit(self)
        except Exception:
            # We don't care about the message because something probably has gone wrong
            pass
        finally:
            self.service.stop()
