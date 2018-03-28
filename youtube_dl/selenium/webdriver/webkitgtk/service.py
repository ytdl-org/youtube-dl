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
    Object that manages the starting and stopping of the WebKitGTKDriver
    """

    def __init__(self, executable_path, port=0, log_path=None):
        """
        Creates a new instance of the Service

        :Args:
         - executable_path : Path to the WebKitGTKDriver
         - port : Port the service is running on
         - log_path : Path for the WebKitGTKDriver service to log to
        """
        log_file = open(log_path, "wb") if log_path is not None and log_path != "" else None
        service.Service.__init__(self, executable_path, port, log_file)

    def command_line_args(self):
        return ["-p", "%d" % self.port]

    def send_remote_shutdown_command(self):
        pass
