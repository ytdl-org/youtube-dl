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

from selenium.webdriver.common import utils
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from .service import Service
from .options import Options

DEFAULT_TIMEOUT = 30
DEFAULT_PORT = 0
DEFAULT_HOST = None
DEFAULT_LOG_LEVEL = None
DEFAULT_LOG_FILE = None


class WebDriver(RemoteWebDriver):
    """ Controls the IEServerDriver and allows you to drive Internet Explorer """

    def __init__(self, executable_path='IEDriverServer.exe', capabilities=None,
                 port=DEFAULT_PORT, timeout=DEFAULT_TIMEOUT, host=DEFAULT_HOST,
                 log_level=DEFAULT_LOG_LEVEL, log_file=DEFAULT_LOG_FILE, options=None,
                 ie_options=None):
        """
        Creates a new instance of the chrome driver.

        Starts the service and then creates new instance of chrome driver.

        :Args:
         - executable_path - path to the executable. If the default is used it assumes the executable is in the $PATH
         - capabilities: capabilities Dictionary object
         - port - port you would like the service to run, if left as 0, a free port will be found.
         - log_level - log level you would like the service to run.
         - log_file - log file you would like the service to log to.
         - options: IE Options instance, providing additional IE options
        """
        if ie_options:
            warnings.warn('use options instead of ie_options', DeprecationWarning)
            options = ie_options
        self.port = port
        if self.port == 0:
            self.port = utils.free_port()
        self.host = host
        self.log_level = log_level
        self.log_file = log_file

        if options is None:
            # desired_capabilities stays as passed in
            if capabilities is None:
                capabilities = self.create_options().to_capabilities()
        else:
            if capabilities is None:
                capabilities = options.to_capabilities()
            else:
                capabilities.update(options.to_capabilities())

        self.iedriver = Service(
            executable_path,
            port=self.port,
            host=self.host,
            log_level=self.log_level,
            log_file=self.log_file)

        self.iedriver.start()

        if capabilities is None:
            capabilities = DesiredCapabilities.INTERNETEXPLORER

        RemoteWebDriver.__init__(
            self,
            command_executor='http://localhost:%d' % self.port,
            desired_capabilities=capabilities)
        self._is_remote = False

    def quit(self):
        RemoteWebDriver.quit(self)
        self.iedriver.stop()

    def create_options(self):
        return Options()
