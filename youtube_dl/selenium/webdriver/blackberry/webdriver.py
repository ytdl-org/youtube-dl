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

import os
import platform
import subprocess

try:
    import http.client as http_client
except ImportError:
    import httplib as http_client

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

LOAD_TIMEOUT = 5


class WebDriver(RemoteWebDriver):
    """
    Controls the BlackBerry Browser and allows you to drive it.

    :Args:
     - device_password - password for the BlackBerry device or emulator you are
       trying to drive
     - bb_tools_dir path to the blackberry-deploy executable. If the default
       is used it assumes it is in the $PATH
     - hostip - the ip for the device you are trying to drive. Falls back to
       169.254.0.1 which is the default ip used
     - port - the port being used for WebDriver on device. defaults to 1338
     - desired_capabilities: Dictionary object with non-browser specific
       capabilities only, such as "proxy" or "loggingPref".

    Note: To get blackberry-deploy you will need to install the BlackBerry
          WebWorks SDK - the default install will put it in the $PATH for you.
          Download at https://developer.blackberry.com/html5/downloads/
    """
    def __init__(self, device_password, bb_tools_dir=None,
                 hostip='169.254.0.1', port=1338, desired_capabilities={}):
        remote_addr = 'http://{}:{}'.format(hostip, port)

        filename = 'blackberry-deploy'
        if platform.system() == "Windows":
            filename += '.bat'

        if bb_tools_dir is not None:
            if os.path.isdir(bb_tools_dir):
                bb_deploy_location = os.path.join(bb_tools_dir, filename)
                if not os.path.isfile(bb_deploy_location):
                    raise WebDriverException('Invalid blackberry-deploy location: {}'.format(bb_deploy_location))
            else:
                raise WebDriverException('Invalid blackberry tools location, must be a directory: {}'.format(bb_tools_dir))
        else:
            bb_deploy_location = filename

        """
        Now launch the BlackBerry browser before allowing anything else to run.
        """
        try:
            launch_args = [bb_deploy_location,
                           '-launchApp',
                           str(hostip),
                           '-package-name', 'sys.browser',
                           '-package-id', 'gYABgJYFHAzbeFMPCCpYWBtHAm0',
                           '-password', str(device_password)]

            with open(os.devnull, 'w') as fp:
                p = subprocess.Popen(launch_args, stdout=fp)

            returncode = p.wait()

            if returncode == 0:
                # wait for the BlackBerry10 browser to load.
                is_running_args = [bb_deploy_location,
                                   '-isAppRunning',
                                   str(hostip),
                                   '-package-name', 'sys.browser',
                                   '-package-id', 'gYABgJYFHAzbeFMPCCpYWBtHAm0',
                                   '-password', str(device_password)]

                WebDriverWait(None, LOAD_TIMEOUT)\
                    .until(lambda x: subprocess.check_output(is_running_args)
                           .find('result::true'),
                           message='waiting for BlackBerry10 browser to load')

                RemoteWebDriver.__init__(self,
                                         command_executor=remote_addr,
                                         desired_capabilities=desired_capabilities)
            else:
                raise WebDriverException('blackberry-deploy failed to launch browser')
        except Exception as e:
            raise WebDriverException('Something went wrong launching blackberry-deploy', stacktrace=getattr(e, 'stacktrace', None))

    def quit(self):
        """
        Closes the browser and shuts down the
        """
        try:
            RemoteWebDriver.quit(self)
        except http_client.BadStatusLine:
            pass
