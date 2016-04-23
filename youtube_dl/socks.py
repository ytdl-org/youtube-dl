# This is free and unencumbered software released into the public domain.
# 
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
# 
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <http://unlicense.org/>
#
# Example:
# import socks
# import ftplib
# import socket
#
# socks.patch_socket()
#
# f = ftplib.FTP('ftp.kernel.org')
# f.login()
# print f.retrlines('LIST')
# f.quit()
# 
# s = socket.create_connection(('www.google.com', 80))
# s.sendall('HEAD / HTTP/1.0\r\n\r\n')
# print s.recv(1024)
# s.close()
from __future__ import unicode_literals
import os
import struct
import socket
import time

__author__ = 'Timo Schmid <coding@timoschmid.de>'

_orig_socket = socket.socket

try:
    from collections import namedtuple
except ImportError:
    from Collections import namedtuple

try:
    from urllib.parse import urlparse
except:
    from urlparse import urlparse

try:
    from enum import Enum
except ImportError:
    Enum = object


class ProxyError(IOError): pass
class Socks4Error(ProxyError):
    CODES = {
        0x5B: 'request rejected or failed',
        0x5C: 'request rejected becasue SOCKS server cannot connect to identd on the client',
        0x5D: 'request rejected because the client program and identd report different user-ids'
    }
    def __init__(self, code=None, msg=None):
        if code is not None and msg is None:
            msg = self.CODES.get(code)
            if msg is None:
                msg = 'unknown error'
        super(Socks4Error, self).__init__(code, msg)

class Socks5Error(Socks4Error):
    CODES = {
        0x01: 'general SOCKS server failure',
        0x02: 'connection not allowed by ruleset',
        0x03: 'Network unreachable',
        0x04: 'Host unreachable',
        0x05: 'Connection refused',
        0x06: 'TTL expired',
        0x07: 'Command not supported',
        0x08: 'Address type not supported',
        0xFE: 'unknown username or invalid password',
        0xFF: 'all offered authentication methods were rejected'
    }

class ProxyType(Enum):
    SOCKS4  = 0
    SOCKS4A = 1
    SOCKS5  = 2

Proxy = namedtuple('Proxy', ('type', 'host', 'port', 'username', 'password', 'remote_dns'))

_default_proxy = None

def setdefaultproxy(proxytype=None, addr=None, port=None, rdns=True, username=None, password=None, allow_env_override=True):
    global _default_proxy
    if allow_env_override:
        all_proxy = os.environ.get('ALL_PROXY', os.environ.get('all_proxy'))
        if all_proxy:
            all_proxy = urlparse(all_proxy)
            if all_proxy.scheme.startswith('socks'):
                if all_proxy.scheme == 'socks' or all_proxy.scheme == 'socks4':
                    proxytype = ProxyType.SOCKS4
                elif all_proxy.scheme == 'socks4a':
                    proxytype = ProxyType.SOCKS4A
                elif all_proxy.scheme == 'socks5':
                    proxytype = ProxyType.SOCKS5
                addr = all_proxy.hostname
                port = all_proxy.port
                username = all_proxy.username
                password = all_proxy.password

    if proxytype is not None:
        _default_proxy = Proxy(proxytype, addr, port, username, password, rdns)


def wrap_socket(sock):
    return socksocket(_sock=sock._sock)

def wrap_module(module):
    if hasattr(module, 'socket'):
        sock = module.socket
        if isinstance(sock, socket.socket):
            module.socket = sockssocket
        elif hasattr(socket, 'socket'):
            socket.socket = sockssocket

def patch_socket():
    import sys
    if 'socket' not in sys.modules:
        import socket
    sys.modules['socket'].socket = sockssocket


class sockssocket(socket.socket):
    def __init__(self, *args, **kwargs):
        self.__proxy = None
        if 'proxy' in kwargs:
            self.__proxy = kwargs['proxy']
            del kwargs['proxy']
        super(sockssocket, self).__init__(*args, **kwargs)

    @property
    def _proxy(self):
        if self.__proxy:
            return self.__proxy
        return _default_proxy

    @property
    def _proxy_port(self):
        if self._proxy:
            if self._proxy.port:
                return self._proxy.port
            return 1080
        return None

    def setproxy(self, proxytype=None, addr=None, port=None, rdns=True, username=None, password=None):
        if proxytype is None:
            self.__proxy = None
        else:
            self.__proxy = Proxy(proxytype, addr, port, username, password, rdns)

    def recvall(self, cnt):
        data = b''
        while len(data) < cnt:
            cur = self.recv(cnt - len(data))
            if not cur:
                raise IOError("{0} bytes missing".format(cnt-len(data)))
            data += cur
        return data

    def _setup_socks4(self, address, is_4a=False):
        destaddr, port = address

        try:
            ipaddr = socket.inet_aton(destaddr)
        except socket.error:
            if is_4a and self._proxy.remote_dns:
                ipaddr = struct.pack('!BBBB', 0, 0, 0, 0xFF)
            else:
                ipaddr = socket.inet_aton(socket.gethostbyname(destaddr))

        packet = struct.pack('!BBH', 0x4, 0x1, port) + ipaddr
        if self._proxy.username:
            username = self._proxy.username
            if hasattr(username, 'encode'):
                username = username.encode()
            packet += struct.pack('!{0}s'.format(len(username)+1), username)
        else:
            packet += b'\x00'

        if is_4a and self._proxy.remote_dns:
            if hasattr(destaddr, 'encode'):
                destaddr = destaddr.encode()
            packet += struct.pack('!{0}s'.format(len(destaddr)+1), destaddr)

        self.sendall(packet)

        packet = self.recvall(8)
        nbyte, resp_code, dstport, dsthost = struct.unpack('!BBHI', packet)

        # check valid response
        if nbyte != 0x00:
            self.close()
            raise ProxyError(0, "Invalid response from server. Expected {0:02x} got {1:02x}".format(0, nbyte))

        # access granted
        if resp_code != 0x5a:
            self.close()
            raise Socks4Error(resp_code)

    def _setup_socks5(self, address):
        destaddr, port = address

        try:
            ipaddr = socket.inet_aton(destaddr)
        except socket.error:
            if self._proxy.remote_dns:
                ipaddr = None
            else:
                ipaddr = socket.inet_aton(socket.gethostbyname(destaddr))

        auth_methods = 1
        if self._proxy.username and self._proxy.password:
            # two auth methods available
            auth_methods = 2
        packet = struct.pack('!BBB', 0x5, auth_methods, 0x00) # no auth
        if self._proxy.username and self._proxy.password:
            packet += struct.pack('!B', 0x02) # user/pass auth

        self.sendall(packet)

        packet = self.recvall(2)
        version, method = struct.unpack('!BB', packet)

        # check valid response
        if version != 0x05:
            self.close()
            raise ProxyError(0, "Invalid response from server. Expected {0:02x} got {1:02x}".format(5, version))

        # no auth methods
        if method == 0xFF:
            self.close()
            raise Socks5Error(method)

        # user/pass auth
        if method == 0x01:
            username = self._proxy.username
            if hasattr(username, 'encode'):
                username = username.encode()
            password = self._proxy.password
            if hasattr(password, 'encode'):
                password = password.encode()
            packet = struct.pack('!BB', 1, len(username)) + username
            packet += struct.pack('!B', len(password)) + password
            self.sendall(packet)

            packet = self.recvall(2)
            version, status = struct.unpack('!BB', packet)

            if version != 0x01:
                self.close()
                raise ProxyError(0, "Invalid response from server. Expected {0:02x} got {1:02x}".format(1, version))

            if status != 0x00:
                self.close()
                raise Socks5Error(1)
        elif method == 0x00: # no auth
            pass


        packet = struct.pack('!BBB', 5, 1, 0)
        if ipaddr is None:
            if hasattr(destaddr, 'encode'):
                destaddr = destaddr.encode()
            packet += struct.pack('!BB', 3, len(destaddr)) + destaddr
        else:
            packet += struct.pack('!B', 1) + ipaddr
        packet += struct.pack('!H', port)

        self.sendall(packet)

        packet = self.recvall(4)
        version, status, _, atype = struct.unpack('!BBBB', packet)

        if version != 0x05:
            self.close()
            raise ProxyError(0, "Invalid response from server. Expected {0:02x} got {1:02x}".format(5, version))

        if status != 0x00:
            self.close()
            raise Socks5Error(status)

        if atype == 0x01:
            destaddr = self.recvall(4)
        elif atype == 0x03:
            alen = struct.unpack('!B', self.recv(1))[0]
            destaddr = self.recvall(alen)
        elif atype == 0x04:
            destaddr = self.recvall(16)
        destport = struct.unpack('!H', self.recvall(2))[0]

    def _make_proxy(self, connect_func, address):
        if self._proxy.type == ProxyType.SOCKS4:
            result = connect_func(self, (self._proxy.host, self._proxy_port))
            if result != 0 and result is not None:
                return result
            self._setup_socks4(address)
        elif self._proxy.type == ProxyType.SOCKS4A:
            result = connect_func(self, (self._proxy.host, self._proxy_port))
            if result != 0 and result is not None:
                return result
            self._setup_socks4(address, is_4a=True)
        elif self._proxy.type == ProxyType.SOCKS5:
            result = connect_func(self, (self._proxy.host, self._proxy_port))
            if result != 0 and result is not None:
                return result
            self._setup_socks5(address)
        else:
            return connect_func(self, address)

    def connect(self, address):
        self._make_proxy(_orig_socket.connect, address)

    def connect_ex(self, address):
        return self._make_proxy(_orig_socket.connect_ex, address)
