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

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchFrameException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoAlertPresentException

"""
 * Canned "Expected Conditions" which are generally useful within webdriver
 * tests.
"""


class title_is(object):
    """An expectation for checking the title of a page.
    title is the expected title, which must be an exact match
    returns True if the title matches, false otherwise."""
    def __init__(self, title):
        self.title = title

    def __call__(self, driver):
        return self.title == driver.title


class title_contains(object):
    """ An expectation for checking that the title contains a case-sensitive
    substring. title is the fragment of title expected
    returns True when the title matches, False otherwise
    """
    def __init__(self, title):
        self.title = title

    def __call__(self, driver):
        return self.title in driver.title


class presence_of_element_located(object):
    """ An expectation for checking that an element is present on the DOM
    of a page. This does not necessarily mean that the element is visible.
    locator - used to find the element
    returns the WebElement once it is located
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        return _find_element(driver, self.locator)


class url_contains(object):
    """ An expectation for checking that the current url contains a
    case-sensitive substring.
    url is the fragment of url expected,
    returns True when the title matches, False otherwise
    """
    def __init__(self, url):
        self.url = url

    def __call__(self, driver):
        return self.url in driver.current_url


class url_matches(object):
    """An expectation for checking the current url.
    pattern is the expected pattern, which must be an exact match
    returns True if the title matches, false otherwise."""
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, driver):
        import re
        match = re.search(self.pattern, driver.current_url)

        return match is not None


class url_to_be(object):
    """An expectation for checking the current url.
    url is the expected url, which must be an exact match
    returns True if the title matches, false otherwise."""
    def __init__(self, url):
        self.url = url

    def __call__(self, driver):
        return self.url == driver.current_url


class url_changes(object):
    """An expectation for checking the current url.
    url is the expected url, which must not be an exact match
    returns True if the url is different, false otherwise."""
    def __init__(self, url):
        self.url = url

    def __call__(self, driver):
        return self.url != driver.current_url


class visibility_of_element_located(object):
    """ An expectation for checking that an element is present on the DOM of a
    page and visible. Visibility means that the element is not only displayed
    but also has a height and width that is greater than 0.
    locator - used to find the element
    returns the WebElement once it is located and visible
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            return _element_if_visible(_find_element(driver, self.locator))
        except StaleElementReferenceException:
            return False


class visibility_of(object):
    """ An expectation for checking that an element, known to be present on the
    DOM of a page, is visible. Visibility means that the element is not only
    displayed but also has a height and width that is greater than 0.
    element is the WebElement
    returns the (same) WebElement once it is visible
    """
    def __init__(self, element):
        self.element = element

    def __call__(self, ignored):
        return _element_if_visible(self.element)


def _element_if_visible(element, visibility=True):
    return element if element.is_displayed() == visibility else False


class presence_of_all_elements_located(object):
    """ An expectation for checking that there is at least one element present
    on a web page.
    locator is used to find the element
    returns the list of WebElements once they are located
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        return _find_elements(driver, self.locator)


class visibility_of_any_elements_located(object):
    """ An expectation for checking that there is at least one element visible
    on a web page.
    locator is used to find the element
    returns the list of WebElements once they are located
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        return [element for element in _find_elements(driver, self.locator) if _element_if_visible(element)]


class visibility_of_all_elements_located(object):
    """ An expectation for checking that all elements are present on the DOM of a
    page and visible. Visibility means that the elements are not only displayed
    but also has a height and width that is greater than 0.
    locator - used to find the elements
    returns the list of WebElements once they are located and visible
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            elements = _find_elements(driver, self.locator)
            for element in elements:
                if _element_if_visible(element, visibility=False):
                    return False
            return elements
        except StaleElementReferenceException:
            return False


class text_to_be_present_in_element(object):
    """ An expectation for checking if the given text is present in the
    specified element.
    locator, text
    """
    def __init__(self, locator, text_):
        self.locator = locator
        self.text = text_

    def __call__(self, driver):
        try:
            element_text = _find_element(driver, self.locator).text
            return self.text in element_text
        except StaleElementReferenceException:
            return False


class text_to_be_present_in_element_value(object):
    """
    An expectation for checking if the given text is present in the element's
    locator, text
    """
    def __init__(self, locator, text_):
        self.locator = locator
        self.text = text_

    def __call__(self, driver):
        try:
            element_text = _find_element(driver,
                                         self.locator).get_attribute("value")
            if element_text:
                return self.text in element_text
            else:
                return False
        except StaleElementReferenceException:
                return False


class frame_to_be_available_and_switch_to_it(object):
    """ An expectation for checking whether the given frame is available to
    switch to.  If the frame is available it switches the given driver to the
    specified frame.
    """
    def __init__(self, locator):
        self.frame_locator = locator

    def __call__(self, driver):
        try:
            if isinstance(self.frame_locator, tuple):
                driver.switch_to.frame(_find_element(driver,
                                                     self.frame_locator))
            else:
                driver.switch_to.frame(self.frame_locator)
            return True
        except NoSuchFrameException:
            return False


class invisibility_of_element_located(object):
    """ An Expectation for checking that an element is either invisible or not
    present on the DOM.

    locator used to find the element
    """
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            return _element_if_visible(_find_element(driver, self.locator), False)
        except (NoSuchElementException, StaleElementReferenceException):
            # In the case of NoSuchElement, returns true because the element is
            # not present in DOM. The try block checks if the element is present
            # but is invisible.
            # In the case of StaleElementReference, returns true because stale
            # element reference implies that element is no longer visible.
            return True


class element_to_be_clickable(object):
    """ An Expectation for checking an element is visible and enabled such that
    you can click it."""
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = visibility_of_element_located(self.locator)(driver)
        if element and element.is_enabled():
            return element
        else:
            return False


class staleness_of(object):
    """ Wait until an element is no longer attached to the DOM.
    element is the element to wait for.
    returns False if the element is still attached to the DOM, true otherwise.
    """
    def __init__(self, element):
        self.element = element

    def __call__(self, ignored):
        try:
            # Calling any method forces a staleness check
            self.element.is_enabled()
            return False
        except StaleElementReferenceException:
            return True


class element_to_be_selected(object):
    """ An expectation for checking the selection is selected.
    element is WebElement object
    """
    def __init__(self, element):
        self.element = element

    def __call__(self, ignored):
        return self.element.is_selected()


class element_located_to_be_selected(object):
    """An expectation for the element to be located is selected.
    locator is a tuple of (by, path)"""
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        return _find_element(driver, self.locator).is_selected()


class element_selection_state_to_be(object):
    """ An expectation for checking if the given element is selected.
    element is WebElement object
    is_selected is a Boolean."
    """
    def __init__(self, element, is_selected):
        self.element = element
        self.is_selected = is_selected

    def __call__(self, ignored):
        return self.element.is_selected() == self.is_selected


class element_located_selection_state_to_be(object):
    """ An expectation to locate an element and check if the selection state
    specified is in that state.
    locator is a tuple of (by, path)
    is_selected is a boolean
    """
    def __init__(self, locator, is_selected):
        self.locator = locator
        self.is_selected = is_selected

    def __call__(self, driver):
        try:
            element = _find_element(driver, self.locator)
            return element.is_selected() == self.is_selected
        except StaleElementReferenceException:
            return False


class number_of_windows_to_be(object):
    """ An expectation for the number of windows to be a certain value."""

    def __init__(self, num_windows):
        self.num_windows = num_windows

    def __call__(self, driver):
        return len(driver.window_handles) == self.num_windows


class new_window_is_opened(object):
    """ An expectation that a new window will be opened and have the number of
    windows handles increase"""

    def __init__(self, current_handles):
        self.current_handles = current_handles

    def __call__(self, driver):
        return len(driver.window_handles) > len(self.current_handles)


class alert_is_present(object):
    """ Expect an alert to be present."""
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            alert = driver.switch_to.alert
            return alert
        except NoAlertPresentException:
            return False


def _find_element(driver, by):
    """Looks up an element. Logs and re-raises ``WebDriverException``
    if thrown."""
    try:
        return driver.find_element(*by)
    except NoSuchElementException as e:
        raise e
    except WebDriverException as e:
        raise e


def _find_elements(driver, by):
    try:
        return driver.find_elements(*by)
    except WebDriverException as e:
        raise e
