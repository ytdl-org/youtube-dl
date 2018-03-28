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
    """
    Object that manages the starting and stopping of the IEDriver
    """

    def __init__(self, executable_path, port=0, host=None, log_level=None, log_file=None):
        """
        Creates a new instance of the Service

        :Args:
         - executable_path : Path to the IEDriver
         - port : Port the service is running on
         - host : IP address the service port is bound
         - log_level : Level of logging of service, may be "FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE".
           Default is "FATAL".
         - log_file : Target of logging of service, may be "stdout", "stderr" or file path.
           Default is "stdout"."""
        self.service_args = []
        if host is not None:
            self.service_args.append("--host=%s" % host)
        if log_level is not None:
            self.service_args.append("--log-level=%s" % log_level)
        if log_file is not None:
            self.service_args.append("--log-file=%s" % log_file)

        service.Service.__init__(self, executable_path, port=port,
                                 start_error_message="Please download from http://selenium-release.storage.googleapis.com/index.html and read up at https://github.com/SeleniumHQ/selenium/wiki/InternetExplorerDriver")

    def command_line_args(self):
        return ["--port=%d" % self.port] + self.service_args
