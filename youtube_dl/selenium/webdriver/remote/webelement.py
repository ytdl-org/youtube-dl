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
import hashlib
import os
import pkgutil
import warnings
import zipfile

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.utils import keys_to_typing
from .command import Command

# Python 3 imports
try:
    str = basestring
except NameError:
    pass

try:
    from StringIO import StringIO as IOStream
except ImportError:  # 3+
    from io import BytesIO as IOStream

# not relying on __package__ here as it can be `None` in some situations (see #4558)
_pkg = '.'.join(__name__.split('.')[:-1])
getAttribute_js = pkgutil.get_data(_pkg, 'getAttribute.js').decode('utf8')
isDisplayed_js = pkgutil.get_data(_pkg, 'isDisplayed.js').decode('utf8')


class WebElement(object):
    """Represents a DOM element.

    Generally, all interesting operations that interact with a document will be
    performed through this interface.

    All method calls will do a freshness check to ensure that the element
    reference is still valid.  This essentially determines whether or not the
    element is still attached to the DOM.  If this test fails, then an
    ``StaleElementReferenceException`` is thrown, and all future calls to this
    instance will fail."""

    def __init__(self, parent, id_, w3c=False):
        self._parent = parent
        self._id = id_
        self._w3c = w3c

    def __repr__(self):
        return '<{0.__module__}.{0.__name__} (session="{1}", element="{2}")>'.format(
            type(self), self._parent.session_id, self._id)

    @property
    def tag_name(self):
        """This element's ``tagName`` property."""
        return self._execute(Command.GET_ELEMENT_TAG_NAME)['value']

    @property
    def text(self):
        """The text of the element."""
        return self._execute(Command.GET_ELEMENT_TEXT)['value']

    def click(self):
        """Clicks the element."""
        self._execute(Command.CLICK_ELEMENT)

    def submit(self):
        """Submits a form."""
        if self._w3c:
            form = self.find_element(By.XPATH, "./ancestor-or-self::form")
            self._parent.execute_script(
                "var e = arguments[0].ownerDocument.createEvent('Event');"
                "e.initEvent('submit', true, true);"
                "if (arguments[0].dispatchEvent(e)) { arguments[0].submit() }", form)
        else:
            self._execute(Command.SUBMIT_ELEMENT)

    def clear(self):
        """Clears the text if it's a text entry element."""
        self._execute(Command.CLEAR_ELEMENT)

    def get_property(self, name):
        """
        Gets the given property of the element.

        :Args:
            - name - Name of the property to retrieve.

        Example::

            text_length = target_element.get_property("text_length")
        """
        try:
            return self._execute(Command.GET_ELEMENT_PROPERTY, {"name": name})["value"]
        except WebDriverException:
            # if we hit an end point that doesnt understand getElementProperty lets fake it
            return self.parent.execute_script('return arguments[0][arguments[1]]', self, name)

    def get_attribute(self, name):
        """Gets the given attribute or property of the element.

        This method will first try to return the value of a property with the
        given name. If a property with that name doesn't exist, it returns the
        value of the attribute with the same name. If there's no attribute with
        that name, ``None`` is returned.

        Values which are considered truthy, that is equals "true" or "false",
        are returned as booleans.  All other non-``None`` values are returned
        as strings.  For attributes or properties which do not exist, ``None``
        is returned.

        :Args:
            - name - Name of the attribute/property to retrieve.

        Example::

            # Check if the "active" CSS class is applied to an element.
            is_active = "active" in target_element.get_attribute("class")

        """

        attributeValue = ''
        if self._w3c:
            attributeValue = self.parent.execute_script(
                "return (%s).apply(null, arguments);" % getAttribute_js,
                self, name)
        else:
            resp = self._execute(Command.GET_ELEMENT_ATTRIBUTE, {'name': name})
            attributeValue = resp.get('value')
            if attributeValue is not None:
                if name != 'value' and attributeValue.lower() in ('true', 'false'):
                    attributeValue = attributeValue.lower()
        return attributeValue

    def is_selected(self):
        """Returns whether the element is selected.

        Can be used to check if a checkbox or radio button is selected.
        """
        return self._execute(Command.IS_ELEMENT_SELECTED)['value']

    def is_enabled(self):
        """Returns whether the element is enabled."""
        return self._execute(Command.IS_ELEMENT_ENABLED)['value']

    def find_element_by_id(self, id_):
        """Finds element within this element's children by ID.

        :Args:
         - id\_ - ID of child element to locate.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            foo_element = element.find_element_by_id('foo')
        """
        return self.find_element(by=By.ID, value=id_)

    def find_elements_by_id(self, id_):
        """Finds a list of elements within this element's children by ID.
        Will return a list of webelements if found, or an empty list if not.

        :Args:
         - id\_ - Id of child element to find.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = element.find_elements_by_id('foo')
        """
        return self.find_elements(by=By.ID, value=id_)

    def find_element_by_name(self, name):
        """Finds element within this element's children by name.

        :Args:
         - name - name property of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_name('foo')
        """
        return self.find_element(by=By.NAME, value=name)

    def find_elements_by_name(self, name):
        """Finds a list of elements within this element's children by name.

        :Args:
         - name - name property to search for.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = element.find_elements_by_name('foo')
        """
        return self.find_elements(by=By.NAME, value=name)

    def find_element_by_link_text(self, link_text):
        """Finds element within this element's children by visible link text.

        :Args:
         - link_text - Link text string to search for.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_link_text('Sign In')
        """
        return self.find_element(by=By.LINK_TEXT, value=link_text)

    def find_elements_by_link_text(self, link_text):
        """Finds a list of elements within this element's children by visible link text.

        :Args:
         - link_text - Link text string to search for.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = element.find_elements_by_link_text('Sign In')
        """
        return self.find_elements(by=By.LINK_TEXT, value=link_text)

    def find_element_by_partial_link_text(self, link_text):
        """Finds element within this element's children by partially visible link text.

        :Args:
         - link_text: The text of the element to partially match on.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_partial_link_text('Sign')
        """
        return self.find_element(by=By.PARTIAL_LINK_TEXT, value=link_text)

    def find_elements_by_partial_link_text(self, link_text):
        """Finds a list of elements within this element's children by link text.

        :Args:
         - link_text: The text of the element to partial match on.

        :Returns:
         - list of webelement - a list with elements if any was found.  an
           empty list if not

        :Usage:
            elements = element.find_elements_by_partial_link_text('Sign')
        """
        return self.find_elements(by=By.PARTIAL_LINK_TEXT, value=link_text)

    def find_element_by_tag_name(self, name):
        """Finds element within this element's children by tag name.

        :Args:
         - name - name of html tag (eg: h1, a, span)

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_tag_name('h1')
        """
        return self.find_element(by=By.TAG_NAME, value=name)

    def find_elements_by_tag_name(self, name):
        """Finds a list of elements within this element's children by tag name.

        :Args:
         - name - name of html tag (eg: h1, a, span)

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = element.find_elements_by_tag_name('h1')
        """
        return self.find_elements(by=By.TAG_NAME, value=name)

    def find_element_by_xpath(self, xpath):
        """Finds element by xpath.

        :Args:
         - xpath - xpath of element to locate.  "//input[@class='myelement']"

        Note: The base path will be relative to this element's location.

        This will select the first link under this element.

        ::

            myelement.find_element_by_xpath(".//a")

        However, this will select the first link on the page.

        ::

            myelement.find_element_by_xpath("//a")

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_xpath('//div/td[1]')
        """
        return self.find_element(by=By.XPATH, value=xpath)

    def find_elements_by_xpath(self, xpath):
        """Finds elements within the element by xpath.

        :Args:
         - xpath - xpath locator string.

        Note: The base path will be relative to this element's location.

        This will select all links under this element.

        ::

            myelement.find_elements_by_xpath(".//a")

        However, this will select all links in the page itself.

        ::

            myelement.find_elements_by_xpath("//a")

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = element.find_elements_by_xpath("//div[contains(@class, 'foo')]")

        """
        return self.find_elements(by=By.XPATH, value=xpath)

    def find_element_by_class_name(self, name):
        """Finds element within this element's children by class name.

        :Args:
         - name: The class name of the element to find.

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_class_name('foo')
        """
        return self.find_element(by=By.CLASS_NAME, value=name)

    def find_elements_by_class_name(self, name):
        """Finds a list of elements within this element's children by class name.

        :Args:
         - name: The class name of the elements to find.

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = element.find_elements_by_class_name('foo')
        """
        return self.find_elements(by=By.CLASS_NAME, value=name)

    def find_element_by_css_selector(self, css_selector):
        """Finds element within this element's children by CSS selector.

        :Args:
         - css_selector - CSS selector string, ex: 'a.nav#home'

        :Returns:
         - WebElement - the element if it was found

        :Raises:
         - NoSuchElementException - if the element wasn't found

        :Usage:
            element = element.find_element_by_css_selector('#foo')
        """
        return self.find_element(by=By.CSS_SELECTOR, value=css_selector)

    def find_elements_by_css_selector(self, css_selector):
        """Finds a list of elements within this element's children by CSS selector.

        :Args:
         - css_selector - CSS selector string, ex: 'a.nav#home'

        :Returns:
         - list of WebElement - a list with elements if any was found.  An
           empty list if not

        :Usage:
            elements = element.find_elements_by_css_selector('.foo')
        """
        return self.find_elements(by=By.CSS_SELECTOR, value=css_selector)

    def send_keys(self, *value):
        """Simulates typing into the element.

        :Args:
            - value - A string for typing, or setting form fields.  For setting
              file inputs, this could be a local file path.

        Use this to send simple key events or to fill out form fields::

            form_textfield = driver.find_element_by_name('username')
            form_textfield.send_keys("admin")

        This can also be used to set file inputs.

        ::

            file_input = driver.find_element_by_name('profilePic')
            file_input.send_keys("path/to/profilepic.gif")
            # Generally it's better to wrap the file path in one of the methods
            # in os.path to return the actual path to support cross OS testing.
            # file_input.send_keys(os.path.abspath("path/to/profilepic.gif"))

        """
        # transfer file to another machine only if remote driver is used
        # the same behaviour as for java binding
        if self.parent._is_remote:
            local_file = self.parent.file_detector.is_local_file(*value)
            if local_file is not None:
                value = self._upload(local_file)

        self._execute(Command.SEND_KEYS_TO_ELEMENT,
                      {'text': "".join(keys_to_typing(value)),
                       'value': keys_to_typing(value)})

    # RenderedWebElement Items
    def is_displayed(self):
        """Whether the element is visible to a user."""
        # Only go into this conditional for browsers that don't use the atom themselves
        if self._w3c and self.parent.capabilities['browserName'] == 'safari':
            return self.parent.execute_script(
                "return (%s).apply(null, arguments);" % isDisplayed_js,
                self)
        else:
            return self._execute(Command.IS_ELEMENT_DISPLAYED)['value']

    @property
    def location_once_scrolled_into_view(self):
        """THIS PROPERTY MAY CHANGE WITHOUT WARNING. Use this to discover
        where on the screen an element is so that we can click it. This method
        should cause the element to be scrolled into view.

        Returns the top lefthand corner location on the screen, or ``None`` if
        the element is not visible.

        """
        if self._w3c:
            old_loc = self._execute(Command.W3C_EXECUTE_SCRIPT, {
                'script': "arguments[0].scrollIntoView(true); return arguments[0].getBoundingClientRect()",
                'args': [self]})['value']
            return {"x": round(old_loc['x']),
                    "y": round(old_loc['y'])}
        else:
            return self._execute(Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW)['value']

    @property
    def size(self):
        """The size of the element."""
        size = {}
        if self._w3c:
            size = self._execute(Command.GET_ELEMENT_RECT)['value']
        else:
            size = self._execute(Command.GET_ELEMENT_SIZE)['value']
        new_size = {"height": size["height"],
                    "width": size["width"]}
        return new_size

    def value_of_css_property(self, property_name):
        """The value of a CSS property."""
        return self._execute(Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY, {
            'propertyName': property_name})['value']

    @property
    def location(self):
        """The location of the element in the renderable canvas."""
        if self._w3c:
            old_loc = self._execute(Command.GET_ELEMENT_RECT)['value']
        else:
            old_loc = self._execute(Command.GET_ELEMENT_LOCATION)['value']
        new_loc = {"x": round(old_loc['x']),
                   "y": round(old_loc['y'])}
        return new_loc

    @property
    def rect(self):
        """A dictionary with the size and location of the element."""
        return self._execute(Command.GET_ELEMENT_RECT)['value']

    @property
    def screenshot_as_base64(self):
        """
        Gets the screenshot of the current element as a base64 encoded string.

        :Usage:
            img_b64 = element.screenshot_as_base64
        """
        return self._execute(Command.ELEMENT_SCREENSHOT)['value']

    @property
    def screenshot_as_png(self):
        """
        Gets the screenshot of the current element as a binary data.

        :Usage:
            element_png = element.screenshot_as_png
        """
        return base64.b64decode(self.screenshot_as_base64.encode('ascii'))

    def screenshot(self, filename):
        """
        Saves a screenshot of the current element to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            element.screenshot('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)
        png = self.screenshot_as_png
        try:
            with open(filename, 'wb') as f:
                f.write(png)
        except IOError:
            return False
        finally:
            del png
        return True

    @property
    def parent(self):
        """Internal reference to the WebDriver instance this element was found from."""
        return self._parent

    @property
    def id(self):
        """Internal ID used by selenium.

        This is mainly for internal use. Simple use cases such as checking if 2
        webelements refer to the same element, can be done using ``==``::

            if element1 == element2:
                print("These 2 are equal")

        """
        return self._id

    def __eq__(self, element):
        return hasattr(element, 'id') and self._id == element.id

    def __ne__(self, element):
        return not self.__eq__(element)

    # Private Methods
    def _execute(self, command, params=None):
        """Executes a command against the underlying HTML element.

        Args:
          command: The name of the command to _execute as a string.
          params: A dictionary of named parameters to send with the command.

        Returns:
          The command's JSON response loaded into a dictionary object.
        """
        if not params:
            params = {}
        params['id'] = self._id
        return self._parent.execute(command, params)

    def find_element(self, by=By.ID, value=None):
        """
        'Private' method used by the find_element_by_* methods.

        :Usage:
            Use the corresponding find_element_by_* instead of this.

        :rtype: WebElement
        """
        if self._w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        return self._execute(Command.FIND_CHILD_ELEMENT,
                             {"using": by, "value": value})['value']

    def find_elements(self, by=By.ID, value=None):
        """
        'Private' method used by the find_elements_by_* methods.

        :Usage:
            Use the corresponding find_elements_by_* instead of this.

        :rtype: list of WebElement
        """
        if self._w3c:
            if by == By.ID:
                by = By.CSS_SELECTOR
                value = '[id="%s"]' % value
            elif by == By.TAG_NAME:
                by = By.CSS_SELECTOR
            elif by == By.CLASS_NAME:
                by = By.CSS_SELECTOR
                value = ".%s" % value
            elif by == By.NAME:
                by = By.CSS_SELECTOR
                value = '[name="%s"]' % value

        return self._execute(Command.FIND_CHILD_ELEMENTS,
                             {"using": by, "value": value})['value']

    def __hash__(self):
        return int(hashlib.md5(self._id.encode('utf-8')).hexdigest(), 16)

    def _upload(self, filename):
        fp = IOStream()
        zipped = zipfile.ZipFile(fp, 'w', zipfile.ZIP_DEFLATED)
        zipped.write(filename, os.path.split(filename)[1])
        zipped.close()
        content = base64.encodestring(fp.getvalue())
        if not isinstance(content, str):
            content = content.decode('utf-8')
        try:
            return self._execute(Command.UPLOAD_FILE, {'file': content})['value']
        except WebDriverException as e:
            if "Unrecognized command: POST" in e.__str__():
                return filename
            elif "Command not found: POST " in e.__str__():
                return filename
            elif '{"status":405,"value":["GET","HEAD","DELETE"]}' in e.__str__():
                return filename
            else:
                raise e
