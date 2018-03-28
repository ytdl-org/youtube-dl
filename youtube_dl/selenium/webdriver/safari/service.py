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

import os
from selenium.webdriver.common import service, utils
from subprocess import PIPE


class Service(service.Service):
    """
    Object that manages the starting and stopping of the SafariDriver
    """

    def __init__(self, executable_path, port=0, quiet=False):
        """
        Creates a new instance of the Service

        :Args:
         - executable_path : Path to the SafariDriver
         - port : Port the service is running on """

        if not os.path.exists(executable_path):
            raise Exception("SafariDriver requires Safari 10 on OSX El Capitan or greater")

        if port == 0:
            port = utils.free_port()

        self.quiet = quiet
        log = PIPE
        if quiet:
            log = open(os.devnull, 'w')
        service.Service.__init__(self, executable_path, port, log)

    def command_line_args(self):
        return ["-p", "%s" % self.port]

    @property
    def service_url(self):
        """
        Gets the url of the SafariDriver Service
        """
        return "http://localhost:%d" % self.port
