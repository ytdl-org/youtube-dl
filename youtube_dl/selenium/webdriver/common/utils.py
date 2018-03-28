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

"""
The Utils methods.
"""
import socket
from selenium.webdriver.common.keys import Keys

try:
    basestring
except NameError:
    # Python 3
    basestring = str


def free_port():
    """
    Determines a free port using sockets.
    """
    free_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    free_socket.bind(('0.0.0.0', 0))
    free_socket.listen(5)
    port = free_socket.getsockname()[1]
    free_socket.close()
    return port


def find_connectable_ip(host, port=None):
    """Resolve a hostname to an IP, preferring IPv4 addresses.

    We prefer IPv4 so that we don't change behavior from previous IPv4-only
    implementations, and because some drivers (e.g., FirefoxDriver) do not
    support IPv6 connections.

    If the optional port number is provided, only IPs that listen on the given
    port are considered.

    :Args:
        - host - A hostname.
        - port - Optional port number.

    :Returns:
        A single IP address, as a string. If any IPv4 address is found, one is
        returned. Otherwise, if any IPv6 address is found, one is returned. If
        neither, then None is returned.

    """
    try:
        addrinfos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return None

    ip = None
    for family, _, _, _, sockaddr in addrinfos:
        connectable = True
        if port:
            connectable = is_connectable(port, sockaddr[0])

        if connectable and family == socket.AF_INET:
            return sockaddr[0]
        if connectable and not ip and family == socket.AF_INET6:
            ip = sockaddr[0]
    return ip


def join_host_port(host, port):
    """Joins a hostname and port together.

    This is a minimal implementation intended to cope with IPv6 literals. For
    example, _join_host_port('::1', 80) == '[::1]:80'.

    :Args:
        - host - A hostname.
        - port - An integer port.

    """
    if ':' in host and not host.startswith('['):
        return '[%s]:%d' % (host, port)
    return '%s:%d' % (host, port)


def is_connectable(port, host="localhost"):
    """
    Tries to connect to the server at port to see if it is running.

    :Args:
     - port - The port to connect.
    """
    socket_ = None
    try:
        socket_ = socket.create_connection((host, port), 1)
        result = True
    except socket.error:
        result = False
    finally:
        if socket_:
            socket_.close()
    return result


def is_url_connectable(port):
    """
    Tries to connect to the HTTP server at /status path
    and specified port to see if it responds successfully.

    :Args:
     - port - The port to connect.
    """
    try:
        from urllib import request as url_request
    except ImportError:
        import urllib2 as url_request

    try:
        res = url_request.urlopen("http://127.0.0.1:%s/status" % port)
        if res.getcode() == 200:
            return True
        else:
            return False
    except Exception:
        return False


def keys_to_typing(value):
    """Processes the values that will be typed in the element."""
    typing = []
    for val in value:
        if isinstance(val, Keys):
            typing.append(val)
        elif isinstance(val, int):
            val = str(val)
            for i in range(len(val)):
                typing.append(val[i])
        else:
            for i in range(len(val)):
                typing.append(val[i])
    return typing
