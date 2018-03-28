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

import logging
import time

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common import utils
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

LOGGER = logging.getLogger(__name__)
PORT = 0
HOST = None
_URL = ""


class ExtensionConnection(RemoteConnection):
    def __init__(self, host, firefox_profile, firefox_binary=None, timeout=30):
        self.profile = firefox_profile
        self.binary = firefox_binary
        HOST = host
        timeout = int(timeout)

        if self.binary is None:
            self.binary = FirefoxBinary()

        if HOST is None:
            HOST = "127.0.0.1"

        PORT = utils.free_port()
        self.profile.port = PORT
        self.profile.update_preferences()

        self.profile.add_extension()

        self.binary.launch_browser(self.profile, timeout=timeout)
        _URL = "http://%s:%d/hub" % (HOST, PORT)
        RemoteConnection.__init__(
            self, _URL, keep_alive=True)

    def quit(self, sessionId=None):
        self.execute(Command.QUIT, {'sessionId': sessionId})
        while self.is_connectable():
            LOGGER.info("waiting to quit")
            time.sleep(1)

    def connect(self):
        """Connects to the extension and retrieves the session id."""
        return self.execute(Command.NEW_SESSION,
                            {'desiredCapabilities': DesiredCapabilities.FIREFOX})

    @classmethod
    def connect_and_quit(self):
        """Connects to an running browser and quit immediately."""
        self._request('%s/extensions/firefox/quit' % _URL)

    @classmethod
    def is_connectable(self):
        """Trys to connect to the extension but do not retrieve context."""
        utils.is_connectable(self.profile.port)


class ExtensionConnectionError(Exception):
    """An internal error occurred int the extension.

    Might be caused by bad input or bugs in webdriver
    """
    pass
