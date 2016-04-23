# Public Domain SOCKS proxy protocol implementation
# Adapted from https://gist.github.com/bluec0re/cafd3764412967417fd3

from __future__ import unicode_literals

import collections
import socket

from .compat import (
    struct_pack,
    struct_unpack,
)

__author__ = 'Timo Schmid <coding@timoschmid.de>'


class ProxyError(IOError):
    pass


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


class ProxyType(object):
    SOCKS4 = 0
    SOCKS4A = 1
    SOCKS5 = 2

Proxy = collections.namedtuple('Proxy', ('type', 'host', 'port', 'username', 'password', 'remote_dns'))


class sockssocket(socket.socket):
    @property
    def _proxy(self):
        return self.__proxy

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
                raise IOError('{0} bytes missing'.format(cnt - len(data)))
            data += cur
        return data

    def _setup_socks4(self, address, is_4a=False):
        destaddr, port = address

        try:
            ipaddr = socket.inet_aton(destaddr)
        except socket.error:
            if is_4a and self._proxy.remote_dns:
                ipaddr = struct_pack('!BBBB', 0, 0, 0, 0xFF)
            else:
                ipaddr = socket.inet_aton(socket.gethostbyname(destaddr))

        packet = struct_pack('!BBH', 0x4, 0x1, port) + ipaddr
        if self._proxy.username:
            username = self._proxy.username
            if hasattr(username, 'encode'):
                username = username.encode()
            packet += struct_pack('!{0}s'.format(len(username) + 1), username)
        else:
            packet += b'\x00'

        if is_4a and self._proxy.remote_dns:
            if hasattr(destaddr, 'encode'):
                destaddr = destaddr.encode()
            packet += struct_pack('!{0}s'.format(len(destaddr) + 1), destaddr)

        self.sendall(packet)

        packet = self.recvall(8)
        nbyte, resp_code, dstport, dsthost = struct_unpack('!BBHI', packet)

        # check valid response
        if nbyte != 0x00:
            self.close()
            raise ProxyError(
                0, 'Invalid response from server. Expected {0:02x} got {1:02x}'.format(0, nbyte))

        # access granted
        if resp_code != 0x5a:
            self.close()
            raise Socks4Error(resp_code)

        return (dsthost, dstport)

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
        packet = struct_pack('!BBB', 0x5, auth_methods, 0x00)  # no auth
        if self._proxy.username and self._proxy.password:
            packet += struct_pack('!B', 0x02)  # user/pass auth

        self.sendall(packet)

        packet = self.recvall(2)
        version, method = struct_unpack('!BB', packet)

        # check valid response
        if version != 0x05:
            self.close()
            raise ProxyError(
                0, 'Invalid response from server. Expected {0:02x} got {1:02x}'.format(5, version))

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
            packet = struct_pack('!BB', 1, len(username)) + username
            packet += struct_pack('!B', len(password)) + password
            self.sendall(packet)

            packet = self.recvall(2)
            version, status = struct_unpack('!BB', packet)

            if version != 0x01:
                self.close()
                raise ProxyError(
                    0, 'Invalid response from server. Expected {0:02x} got {1:02x}'.format(1, version))

            if status != 0x00:
                self.close()
                raise Socks5Error(1)
        elif method == 0x00:  # no auth
            pass

        packet = struct_pack('!BBB', 5, 1, 0)
        if ipaddr is None:
            if hasattr(destaddr, 'encode'):
                destaddr = destaddr.encode()
            packet += struct_pack('!BB', 3, len(destaddr)) + destaddr
        else:
            packet += struct_pack('!B', 1) + ipaddr
        packet += struct_pack('!H', port)

        self.sendall(packet)

        packet = self.recvall(4)
        version, status, _, atype = struct_unpack('!BBBB', packet)

        if version != 0x05:
            self.close()
            raise ProxyError(
                0, 'Invalid response from server. Expected {0:02x} got {1:02x}'.format(5, version))

        if status != 0x00:
            self.close()
            raise Socks5Error(status)

        if atype == 0x01:
            destaddr = self.recvall(4)
        elif atype == 0x03:
            alen = struct_unpack('!B', self.recv(1))[0]
            destaddr = self.recvall(alen)
        elif atype == 0x04:
            destaddr = self.recvall(16)
        destport = struct_unpack('!H', self.recvall(2))[0]

        return (destaddr, destport)

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
        self._make_proxy(socket.socket.connect, address)

    def connect_ex(self, address):
        return self._make_proxy(socket.socket.connect_ex, address)
