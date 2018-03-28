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

import json
import logging
import os
import tempfile
import zipfile

from selenium.common.exceptions import NoSuchElementException

LOGGER = logging.getLogger(__name__)


def format_json(json_struct):
    return json.dumps(json_struct, indent=4)


def dump_json(json_struct):
    return json.dumps(json_struct)


def load_json(s):
    return json.loads(s)


def handle_find_element_exception(e):
    if ("Unable to find" in e.response["value"]["message"] or "Unable to locate" in e.response["value"]["message"]):
        raise NoSuchElementException("Unable to locate element:")
    else:
        raise e


def return_value_if_exists(resp):
    if resp and "value" in resp:
        return resp["value"]


def get_root_parent(elem):
    parent = elem.parent
    while True:
        try:
            parent.parent
            parent = parent.parent
        except AttributeError:
            return parent


def unzip_to_temp_dir(zip_file_name):
    """Unzip zipfile to a temporary directory.

    The directory of the unzipped files is returned if success,
    otherwise None is returned. """
    if not zip_file_name or not os.path.exists(zip_file_name):
        return None

    zf = zipfile.ZipFile(zip_file_name)

    if zf.testzip() is not None:
        return None

    # Unzip the files into a temporary directory
    LOGGER.info("Extracting zipped file: %s" % zip_file_name)
    tempdir = tempfile.mkdtemp()

    try:
        # Create directories that don't exist
        for zip_name in zf.namelist():
            # We have no knowledge on the os where the zipped file was
            # created, so we restrict to zip files with paths without
            # charactor "\" and "/".
            name = (zip_name.replace("\\", os.path.sep).
                    replace("/", os.path.sep))
            dest = os.path.join(tempdir, name)
            if (name.endswith(os.path.sep) and not os.path.exists(dest)):
                os.mkdir(dest)
                LOGGER.debug("Directory %s created." % dest)

        # Copy files
        for zip_name in zf.namelist():
            # We have no knowledge on the os where the zipped file was
            # created, so we restrict to zip files with paths without
            # charactor "\" and "/".
            name = (zip_name.replace("\\", os.path.sep).
                    replace("/", os.path.sep))
            dest = os.path.join(tempdir, name)
            if not (name.endswith(os.path.sep)):
                LOGGER.debug("Copying file %s......" % dest)
                outfile = open(dest, 'wb')
                outfile.write(zf.read(zip_name))
                outfile.close()
                LOGGER.debug("File %s copied." % dest)

        LOGGER.info("Unzipped file can be found at %s" % tempdir)
        return tempdir

    except IOError as err:
        LOGGER.error("Error in extracting webdriver.xpi: %s" % err)
        return None
