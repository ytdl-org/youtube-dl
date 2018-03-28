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


class FirefoxRemoteConnection(RemoteConnection):
    def __init__(self, remote_server_addr, keep_alive=True):
        RemoteConnection.__init__(self, remote_server_addr, keep_alive)

        self._commands["GET_CONTEXT"] = ('GET', '/session/$sessionId/moz/context')
        self._commands["SET_CONTEXT"] = ("POST", "/session/$sessionId/moz/context")
        self._commands["ELEMENT_GET_ANONYMOUS_CHILDREN"] = \
            ("POST", "/session/$sessionId/moz/xbl/$id/anonymous_children")
        self._commands["ELEMENT_FIND_ANONYMOUS_ELEMENTS_BY_ATTRIBUTE"] = \
            ("POST", "/session/$sessionId/moz/xbl/$id/anonymous_by_attribute")
        self._commands["INSTALL_ADDON"] = \
            ("POST", "/session/$sessionId/moz/addon/install")
        self._commands["UNINSTALL_ADDON"] = \
            ("POST", "/session/$sessionId/moz/addon/uninstall")
