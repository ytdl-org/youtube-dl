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

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Options(object):
    KEY = 'webkitgtk:browserOptions'

    def __init__(self):
        self._binary_location = ''
        self._arguments = []
        self._overlay_scrollbars_enabled = True

    @property
    def binary_location(self):
        """
        Returns the location of the browser binary otherwise an empty string
        """
        return self._binary_location

    @binary_location.setter
    def binary_location(self, value):
        """
        Allows you to set the browser binary to launch

        :Args:
         - value : path to the browser binary
        """
        self._binary_location = value

    @property
    def arguments(self):
        """
        Returns a list of arguments needed for the browser
        """
        return self._arguments

    def add_argument(self, argument):
        """
        Adds an argument to the list

        :Args:
         - Sets the arguments
        """
        if argument:
            self._arguments.append(argument)
        else:
            raise ValueError("argument can not be null")

    @property
    def overlay_scrollbars_enabled(self):
        """
        Returns whether overlay scrollbars should be enabled
        """
        return self._overlay_scrollbars_enabled

    @overlay_scrollbars_enabled.setter
    def overlay_scrollbars_enabled(self, value):
        """
        Allows you to enable or disable overlay scrollbars

        :Args:
         - value : True or False
        """
        self._overlay_scrollbars_enabled = value

    def to_capabilities(self):
        """
        Creates a capabilities with all the options that have been set and
        returns a dictionary with everything
        """
        webkitgtk = DesiredCapabilities.WEBKITGTK.copy()

        browser_options = {}
        if self.binary_location:
            browser_options["binary"] = self.binary_location
        if self.arguments:
            browser_options["args"] = self.arguments
        browser_options["useOverlayScrollbars"] = self.overlay_scrollbars_enabled

        webkitgtk[Options.KEY] = browser_options

        return webkitgtk
