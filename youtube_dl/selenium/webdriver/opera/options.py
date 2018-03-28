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

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Options(ChromeOptions):
    KEY = "operaOptions"

    def __init__(self):
        ChromeOptions.__init__(self)
        self._android_package_name = ''
        self._android_device_socket = ''
        self._android_command_line_file = ''

    @property
    def android_package_name(self):
        """
        Returns the name of the Opera package
        """
        return self._android_package_name

    @android_package_name.setter
    def android_package_name(self, value):
        """
        Allows you to set the package name

        :Args:
         - value: devtools socket name
        """
        self._android_package_name = value

    @property
    def android_device_socket(self):
        """
        Returns the name of the devtools socket
        """
        return self._android_device_socket

    @android_device_socket.setter
    def android_device_socket(self, value):
        """
        Allows you to set the devtools socket name

        :Args:
         - value: devtools socket name
        """
        self._android_device_socket = value

    @property
    def android_command_line_file(self):
        """
        Returns the path of the command line file
        """
        return self._android_command_line_file

    @android_command_line_file.setter
    def android_command_line_file(self, value):
        """
        Allows you to set where the command line file lives

        :Args:
         - value: command line file path
        """
        self._android_command_line_file = value

    def to_capabilities(self):
        """
            Creates a capabilities with all the options that have been set and

            returns a dictionary with everything
        """
        capabilities = ChromeOptions.to_capabilities(self)
        capabilities.update(DesiredCapabilities.OPERA)
        opera_options = capabilities[self.KEY]

        if self.android_package_name:
            opera_options["androidPackage"] = self.android_package_name
        if self.android_device_socket:
            opera_options["androidDeviceSocket"] = self.android_device_socket
        if self.android_command_line_file:
            opera_options["androidCommandLineFile"] = \
                self.android_command_line_file
        return capabilities


class AndroidOptions(Options):

    def __init__(self):
        Options.__init__(self)
        self.android_package_name = 'com.opera.browser'
