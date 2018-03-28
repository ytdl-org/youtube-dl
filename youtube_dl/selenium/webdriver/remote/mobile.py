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

from .command import Command


class Mobile(object):

    class ConnectionType(object):

        def __init__(self, mask):
            self.mask = mask

        @property
        def airplane_mode(self):
            return self.mask % 2 == 1

        @property
        def wifi(self):
            return (self.mask / 2) % 2 == 1

        @property
        def data(self):
            return (self.mask / 4) > 0

    ALL_NETWORK = ConnectionType(6)
    WIFI_NETWORK = ConnectionType(2)
    DATA_NETWORK = ConnectionType(4)
    AIRPLANE_MODE = ConnectionType(1)

    def __init__(self, driver):
        self._driver = driver

    @property
    def network_connection(self):
        return self.ConnectionType(self._driver.execute(Command.GET_NETWORK_CONNECTION)['value'])

    def set_network_connection(self, network):
        """
        Set the network connection for the remote device.

        Example of setting airplane mode::

            driver.mobile.set_network_connection(driver.mobile.AIRPLANE_MODE)
        """
        mode = network.mask if isinstance(network, self.ConnectionType) else network
        return self.ConnectionType(self._driver.execute(
            Command.SET_NETWORK_CONNECTION, {
                'name': 'network_connection',
                'parameters': {'type': mode}})['value'])

    @property
    def context(self):
        """
        returns the current context (Native or WebView).
        """
        return self._driver.execute(Command.CURRENT_CONTEXT_HANDLE)

    @property
    def contexts(self):
        """
        returns a list of available contexts
        """
        return self._driver.execute(Command.CONTEXT_HANDLES)

    @context.setter
    def context(self, new_context):
        """
        sets the current context
        """
        self._driver.execute(Command.SWITCH_TO_CONTEXT, {"name": new_context})
