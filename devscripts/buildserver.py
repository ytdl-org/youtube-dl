#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import getopt, threading, sys, urlparse, _winreg, os, subprocess, shutil, tempfile


class BuildHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True


def usage():
    print 'Usage: %s [options]'
    print 'Options:'
    print
    print '  -h, --help               Display this help'
    print '  -i, --install            Launch at session startup'
    print '  -u, --uninstall          Do not launch at session startup'
    print '  -b, --bind <host[:port]> Bind to host:port (default localhost:8142)'
    sys.exit(0)


def main(argv):
    opts, args = getopt.getopt(argv, 'hb:iu', ['help', 'bind=', 'install', 'uninstall'])
    host = 'localhost'
    port = 8142

    for opt, val in opts:
        if opt in ['-h', '--help']:
            usage()
        elif opt in ['-b', '--bind']:
            try:
                host, port = val.split(':')
            except ValueError:
                host = val
            else:
                port = int(port)
        elif opt in ['-i', '--install']:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, _winreg.KEY_WRITE)
            try:
                _winreg.SetValueEx(key, 'Youtube-dl builder', 0, _winreg.REG_SZ,
                                   '"%s" "%s" -b %s:%d' % (sys.executable, os.path.normpath(os.path.abspath(sys.argv[0])),
                                                           host, port))
            finally:
                _winreg.CloseKey(key)
            print 'Installed.'
            sys.exit(0)
        elif opt in ['-u', '--uninstall']:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, _winreg.KEY_WRITE)
            try:
                _winreg.DeleteValue(key, 'Youtube-dl builder')
            finally:
                _winreg.CloseKey(key)
            print 'Uninstalled.'
            sys.exit(0)

    print 'Listening on %s:%d' % (host, port)
    srv = BuildHTTPServer((host, port), BuildHTTPRequestHandler)
    thr = threading.Thread(target=srv.serve_forever)
    thr.start()
    raw_input('Hit <ENTER> to stop...\n')
    srv.shutdown()
    thr.join()


def rmtree(path):
    for name in os.listdir(path):
        fname = os.path.join(path, name)
        if os.path.isdir(fname):
            rmtree(fname)
        else:
            os.chmod(fname, 0666)
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
            print 'WARNING deleting "%s": %s' % (self.basePath, e)

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
