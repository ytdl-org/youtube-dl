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
    """Object that manages the starting and stopping of the
    GeckoDriver."""

    def __init__(self, executable_path, port=0, service_args=None,
                 log_path="geckodriver.log", env=None):
        """Creates a new instance of the GeckoDriver remote service proxy.

        GeckoDriver provides a HTTP interface speaking the W3C WebDriver
        protocol to Marionette.

        :param executable_path: Path to the GeckoDriver binary.
        :param port: Run the remote service on a specified port.
            Defaults to 0, which binds to a random open port of the
            system's choosing.
        :param service_args: Optional list of arguments to pass to the
            GeckoDriver binary.
        :param log_path: Optional path for the GeckoDriver to log to.
            Defaults to _geckodriver.log_ in the current working directory.
        :param env: Optional dictionary of output variables to expose
            in the services' environment.

        """
        log_file = open(log_path, "a+") if log_path is not None and log_path != "" else None

        service.Service.__init__(
            self, executable_path, port=port, log_file=log_file, env=env)
        self.service_args = service_args or []

    def command_line_args(self):
        return ["--port", "%d" % self.port] + self.service_args

    def send_remote_shutdown_command(self):
        pass
