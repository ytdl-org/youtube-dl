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


KEY = "key"
POINTER = "pointer"
NONE = "none"
SOURCE_TYPES = set([KEY, POINTER, NONE])


class Interaction(object):

    PAUSE = "pause"

    def __init__(self, source):
        self.source = source


class Pause(Interaction):

    def __init__(self, source, duration=0):
        super(Interaction, self).__init__()
        self.source = source
        self.duration = duration

    def encode(self):
        output = {"type": self.PAUSE}
        output["duration"] = self.duration * 1000
        return output
