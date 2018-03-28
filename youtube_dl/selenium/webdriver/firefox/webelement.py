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

from selenium.webdriver.remote.webelement import WebElement as RemoteWebElement


class FirefoxWebElement(RemoteWebElement):

    @property
    def anonymous_children(self):
        """Retrieve the anonymous children of this element in an XBL
        context.  This is only available in chrome context.

        See the  `anonymous content documentation
        <https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XBL/XBL_1.0_Reference/Anonymous_Content>`_
        on MDN for more information.

        """
        return self._execute(
            "ELEMENT_GET_ANONYMOUS_CHILDREN",
            {"value": None})

    def find_anonymous_element_by_attribute(self, name, value):
        """Retrieve an anonymous descendant with a specified attribute
        value.  Typically used with an (arbitrary) anonid attribute to
        retrieve a specific anonymous child in an XBL binding.

        See the  `anonymous content documentation
        <https://developer.mozilla.org/en-US/docs/Mozilla/Tech/XBL/XBL_1.0_Reference/Anonymous_Content>`_
        on MDN for more information.

        """
        return self._execute(
            "ELEMENT_FIND_ANONYMOUS_ELEMENTS_BY_ATTRIBUTE",
            {"name": name, "value": value})["value"]
