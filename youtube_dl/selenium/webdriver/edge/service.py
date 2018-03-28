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

from selenium.webdriver.common import service


class Service(service.Service):

    def __init__(self, executable_path, port=0, verbose=False, log_path=None):
        """
        Creates a new instance of the EdgeDriver service.

        EdgeDriver provides an interface for Microsoft WebDriver to use
        with Microsoft Edge.

        :param executable_path: Path to the Microsoft WebDriver binary.
        :param port: Run the remote service on a specified port.
            Defaults to 0, which binds to a random open port of the
            system's choosing.
        :verbose: Whether to make the webdriver more verbose (passes the
            --verbose option to the binary). Defaults to False.
        :param log_path: Optional path for the webdriver binary to log to.
            Defaults to None which disables logging.

        """

        self.service_args = []
        if verbose:
            self.service_args.append("--verbose")

        params = {
            "executable": executable_path,
            "port": port,
            "start_error_message": "Please download from http://go.microsoft.com/fwlink/?LinkId=619687"
        }

        if log_path:
            params["log_file"] = open(log_path, "a+")

        service.Service.__init__(self, **params)

    def command_line_args(self):
        return ["--port=%d" % self.port] + self.service_args
