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

from selenium.webdriver.remote.command import Command
from . import interaction
from .key_actions import KeyActions
from .key_input import KeyInput
from .pointer_actions import PointerActions
from .pointer_input import PointerInput


class ActionBuilder(object):
    def __init__(self, driver, mouse=None, keyboard=None):
        if mouse is None:
            mouse = PointerInput(interaction.POINTER, "mouse")
        if keyboard is None:
            keyboard = KeyInput(interaction.KEY)
        self.devices = [mouse, keyboard]
        self._key_action = KeyActions(keyboard)
        self._pointer_action = PointerActions(mouse)
        self.driver = driver

    def get_device_with(self, name):
        try:
            idx = self.devices.index(name)
            return self.devices[idx]
        except:
            pass

    @property
    def pointer_inputs(self):
        return [device for device in self.devices if device.type == interaction.POINTER]

    @property
    def key_inputs(self):
        return [device for device in self.devices if device.type == interaction.KEY]

    @property
    def key_action(self):
        return self._key_action

    @property
    def pointer_action(self):
        return self._pointer_action

    def add_key_input(self, name):
        new_input = KeyInput(name)
        self._add_input(new_input)
        return new_input

    def add_pointer_input(self, type_, name):
        new_input = PointerInput(type_, name)
        self._add_input(new_input)
        return new_input

    def perform(self):
        enc = {"actions": []}
        for device in self.devices:
            encoded = device.encode()
            if encoded['actions']:
                enc["actions"].append(encoded)
        self.driver.execute(Command.W3C_ACTIONS, enc)

    def clear_actions(self):
        self.driver.execute(Command.W3C_CLEAR_ACTIONS)

    def _add_input(self, input):
        self.devices.append(input)
