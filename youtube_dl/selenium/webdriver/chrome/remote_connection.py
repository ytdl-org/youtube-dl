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

from selenium.webdriver.remote.remote_connection import RemoteConnection


class ChromeRemoteConnection(RemoteConnection):

    def __init__(self, remote_server_addr, keep_alive=True):
        RemoteConnection.__init__(self, remote_server_addr, keep_alive)
        self._commands["launchApp"] = ('POST', '/session/$sessionId/chromium/launch_app')
        self._commands["setNetworkConditions"] = ('POST', '/session/$sessionId/chromium/network_conditions')
        self._commands["getNetworkConditions"] = ('GET', '/session/$sessionId/chromium/network_conditions')
