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

import base64
import os

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Options(object):
    KEY = "goog:chromeOptions"

    def __init__(self):
        self._binary_location = ''
        self._arguments = []
        self._extension_files = []
        self._extensions = []
        self._experimental_options = {}
        self._debugger_address = None

    @property
    def binary_location(self):
        """
        Returns the location of the binary otherwise an empty string
        """
        return self._binary_location

    @binary_location.setter
    def binary_location(self, value):
        """
        Allows you to set where the chromium binary lives

        :Args:
         - value: path to the Chromium binary
        """
        self._binary_location = value

    @property
    def debugger_address(self):
        """
        Returns the address of the remote devtools instance
        """
        return self._debugger_address

    @debugger_address.setter
    def debugger_address(self, value):
        """
        Allows you to set the address of the remote devtools instance
        that the ChromeDriver instance will try to connect to during an
        active wait.

        :Args:
         - value: address of remote devtools instance if any (hostname[:port])
        """
        self._debugger_address = value

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
    def extensions(self):
        """
        Returns a list of encoded extensions that will be loaded into chrome

        """
        encoded_extensions = []
        for ext in self._extension_files:
            file_ = open(ext, 'rb')
            # Should not use base64.encodestring() which inserts newlines every
            # 76 characters (per RFC 1521).  Chromedriver has to remove those
            # unnecessary newlines before decoding, causing performance hit.
            encoded_extensions.append(base64.b64encode(file_.read()).decode('UTF-8'))

            file_.close()
        return encoded_extensions + self._extensions

    def add_extension(self, extension):
        """
        Adds the path to the extension to a list that will be used to extract it
        to the ChromeDriver

        :Args:
         - extension: path to the \*.crx file
        """
        if extension:
            extension_to_add = os.path.abspath(os.path.expanduser(extension))
            if os.path.exists(extension_to_add):
                self._extension_files.append(extension_to_add)
            else:
                raise IOError("Path to the extension doesn't exist")
        else:
            raise ValueError("argument can not be null")

    def add_encoded_extension(self, extension):
        """
        Adds Base64 encoded string with extension data to a list that will be used to extract it
        to the ChromeDriver

        :Args:
         - extension: Base64 encoded string with extension data
        """
        if extension:
            self._extensions.append(extension)
        else:
            raise ValueError("argument can not be null")

    @property
    def experimental_options(self):
        """
        Returns a dictionary of experimental options for chrome.
        """
        return self._experimental_options

    def add_experimental_option(self, name, value):
        """
        Adds an experimental option which is passed to chrome.

        Args:
          name: The experimental option name.
          value: The option value.
        """
        self._experimental_options[name] = value

    @property
    def headless(self):
        """
        Returns whether or not the headless argument is set
        """
        return '--headless' in self._arguments

    def set_headless(self, headless=True):
        """
        Sets the headless argument

        Args:
          headless: boolean value indicating to set the headless option
        """
        args = {'--headless', '--disable-gpu'}
        if headless:
            self._arguments.extend(args)
        else:
            self._arguments = list(set(self._arguments) - args)

    def to_capabilities(self):
        """
            Creates a capabilities with all the options that have been set and

            returns a dictionary with everything
        """
        chrome = DesiredCapabilities.CHROME.copy()

        chrome_options = self.experimental_options.copy()
        chrome_options["extensions"] = self.extensions
        if self.binary_location:
            chrome_options["binary"] = self.binary_location
        chrome_options["args"] = self.arguments
        if self.debugger_address:
            chrome_options["debuggerAddress"] = self.debugger_address

        chrome[self.KEY] = chrome_options

        return chrome
