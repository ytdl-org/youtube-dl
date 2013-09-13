#!/usr/bin/python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import argparse
import ctypes
import sys
import threading
import os.path


class BuildHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True


advapi32 = ctypes.windll.advapi32

SC_MANAGER_ALL_ACCESS = 0xf003f
SC_MANAGER_CREATE_SERVICE = 0x02
SERVICE_WIN32_OWN_PROCESS = 0x10
SERVICE_AUTO_START = 0x2
SERVICE_ERROR_NORMAL = 0x1
DELETE = 0x00010000


def win_OpenSCManager():
    res = advapi32.OpenSCManagerA(None, None, SC_MANAGER_ALL_ACCESS)
    if not res:
        raise Exception('Opening service manager failed - '
                        'are you running this as administrator?')
    return res


def win_install_service(service_name, cmdline):
    manager = win_OpenSCManager()
    try:
        h = advapi32.CreateServiceA(
            manager, service_name, None,
            SC_MANAGER_CREATE_SERVICE, SERVICE_WIN32_OWN_PROCESS,
            SERVICE_AUTO_START, SERVICE_ERROR_NORMAL,
            cmdline, None, None, None, None, None)
        if not h:
            raise OSError('Service creation failed: %s' % ctypes.FormatError())

        advapi32.CloseServiceHandle(h)
    finally:
        advapi32.CloseServiceHandle(manager)


def win_uninstall_service(service_name):
    manager = win_OpenSCManager()
    try:
        h = advapi32.OpenServiceA(manager, service_name, DELETE)
        if not h:
            raise OSError('Could not find service %s: %s' % (
                service_name, ctypes.FormatError()))

        try:
            if not advapi32.DeleteService(h):
                raise OSError('Deletion failed: %s' % ctypes.FormatError())
        finally:
            advapi32.CloseServiceHandle(h)
    finally:
        advapi32.CloseServiceHandle(manager)


def install_service(bind):
    fn = os.path.normpath(__file__)
    cmdline = '"%s" "%s" -s -b "%s"' % (sys.executable, fn, bind)
    win_install_service('youtubedl_builder', cmdline)


def uninstall_service():
    win_uninstall_service('youtubedl_builder')


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--install',
                        action='store_const', dest='action', const='install',
                        help='Launch at Windows startup')
    parser.add_argument('-u', '--uninstall',
                        action='store_const', dest='action', const='uninstall',
                        help='Remove Windows service')
    parser.add_argument('-s', '--service',
                        action='store_const', dest='action', const='servce',
                        help='Run as a Windows service')
    parser.add_argument('-b', '--bind', metavar='<host:port>',
                        action='store', default='localhost:8142',
                        help='Bind to host:port (default %default)')
    options = parser.parse_args()

    if options.action == 'install':
        return install_service(options.bind)

    if options.action == 'uninstall':
        return uninstall_service()

    host, port_str = options.bind.split(':')
    port = int(port_str)

    print('Listening on %s:%d' % (host, port))
    srv = BuildHTTPServer((host, port), BuildHTTPRequestHandler)
    thr = threading.Thread(target=srv.serve_forever)
    thr.start()
    input('Press ENTER to shut down')
    srv.shutdown()
    thr.join()


def rmtree(path):
    for name in os.listdir(path):
        fname = os.path.join(path, name)
        if os.path.isdir(fname):
            rmtree(fname)
        else:
            os.chmod(fname, 0o666)
            os.remove(fname)
    os.rmdir(path)

#==============================================================================

class BuildError(Exception):
    def __init__(self, output, code=500):
        self.output = output
        self.code = code

    def __str__(self):
        return self.output


class HTTPError(BuildError):
    pass


class PythonBuilder(object):
    def __init__(self, **kwargs):
        pythonVersion = kwargs.pop('python', '2.7')
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Python\PythonCore\%s\InstallPath' % pythonVersion)
            try:
                self.pythonPath, _ = _winreg.QueryValueEx(key, '')
            finally:
                _winreg.CloseKey(key)
        except Exception:
            raise BuildError('No such Python version: %s' % pythonVersion)

        super(PythonBuilder, self).__init__(**kwargs)


class GITInfoBuilder(object):
    def __init__(self, **kwargs):
        try:
            self.user, self.repoName = kwargs['path'][:2]
            self.rev = kwargs.pop('rev')
        except ValueError:
            raise BuildError('Invalid path')
        except KeyError as e:
            raise BuildError('Missing mandatory parameter "%s"' % e.args[0])

        path = os.path.join(os.environ['APPDATA'], 'Build archive', self.repoName, self.user)
        if not os.path.exists(path):
            os.makedirs(path)
        self.basePath = tempfile.mkdtemp(dir=path)
        self.buildPath = os.path.join(self.basePath, 'build')

        super(GITInfoBuilder, self).__init__(**kwargs)


class GITBuilder(GITInfoBuilder):
    def build(self):
        try:
            subprocess.check_output(['git', 'clone', 'git://github.com/%s/%s.git' % (self.user, self.repoName), self.buildPath])
            subprocess.check_output(['git', 'checkout', self.rev], cwd=self.buildPath)
        except subprocess.CalledProcessError as e:
            raise BuildError(e.output)

        super(GITBuilder, self).build()


class YoutubeDLBuilder(object):
    authorizedUsers = ['fraca7', 'phihag', 'rg3', 'FiloSottile']

    def __init__(self, **kwargs):
        if self.repoName != 'youtube-dl':
            raise BuildError('Invalid repository "%s"' % self.repoName)
        if self.user not in self.authorizedUsers:
            raise HTTPError('Unauthorized user "%s"' % self.user, 401)

        super(YoutubeDLBuilder, self).__init__(**kwargs)

    def build(self):
        try:
            subprocess.check_output([os.path.join(self.pythonPath, 'python.exe'), 'setup.py', 'py2exe'],
                                    cwd=self.buildPath)
        except subprocess.CalledProcessError as e:
            raise BuildError(e.output)

        super(YoutubeDLBuilder, self).build()


class DownloadBuilder(object):
    def __init__(self, **kwargs):
        self.handler = kwargs.pop('handler')
        self.srcPath = os.path.join(self.buildPath, *tuple(kwargs['path'][2:]))
        self.srcPath = os.path.abspath(os.path.normpath(self.srcPath))
        if not self.srcPath.startswith(self.buildPath):
            raise HTTPError(self.srcPath, 401)

        super(DownloadBuilder, self).__init__(**kwargs)

    def build(self):
        if not os.path.exists(self.srcPath):
            raise HTTPError('No such file', 404)
        if os.path.isdir(self.srcPath):
            raise HTTPError('Is a directory: %s' % self.srcPath, 401)

        self.handler.send_response(200)
        self.handler.send_header('Content-Type', 'application/octet-stream')
        self.handler.send_header('Content-Disposition', 'attachment; filename=%s' % os.path.split(self.srcPath)[-1])
        self.handler.send_header('Content-Length', str(os.stat(self.srcPath).st_size))
        self.handler.end_headers()

        with open(self.srcPath, 'rb') as src:
            shutil.copyfileobj(src, self.handler.wfile)

        super(DownloadBuilder, self).build()


class CleanupTempDir(object):
    def build(self):
        try:
            rmtree(self.basePath)
        except Exception as e:
            print('WARNING deleting "%s": %s' % (self.basePath, e))

        super(CleanupTempDir, self).build()


class Null(object):
    def __init__(self, **kwargs):
        pass

    def start(self):
        pass

    def close(self):
        pass

    def build(self):
        pass


class Builder(PythonBuilder, GITBuilder, YoutubeDLBuilder, DownloadBuilder, CleanupTempDir, Null):
    pass


class BuildHTTPRequestHandler(BaseHTTPRequestHandler):
    actionDict = { 'build': Builder, 'download': Builder } # They're the same, no more caching.

    def do_GET(self):
        path = urlparse.urlparse(self.path)
        paramDict = dict([(key, value[0]) for key, value in urlparse.parse_qs(path.query).items()])
        action, _, path = path.path.strip('/').partition('/')
        if path:
            path = path.split('/')
            if action in self.actionDict:
                try:
                    builder = self.actionDict[action](path=path, handler=self, **paramDict)
                    builder.start()
                    try:
                        builder.build()
                    finally:
                        builder.close()
                except BuildError as e:
                    self.send_response(e.code)
                    msg = unicode(e).encode('UTF-8')
                    self.send_header('Content-Type', 'text/plain; charset=UTF-8')
                    self.send_header('Content-Length', len(msg))
                    self.end_headers()
                    self.wfile.write(msg)
                except HTTPError as e:
                    self.send_response(e.code, str(e))
            else:
                self.send_response(500, 'Unknown build method "%s"' % action)
        else:
            self.send_response(500, 'Malformed URL')

#==============================================================================

if __name__ == '__main__':
    main(sys.argv[1:])
