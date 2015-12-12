import errno
import glob
import os
import shutil
import subprocess
import sys


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def rename_file(old_path, new_path):
    if sys.platform == 'win32':
        try:
            os.unlink(new_path)
        except OSError:
            pass
    os.rename(old_path, new_path)


class I18N_Utils(object):
    GETTEXT_DOMAIN = 'youtube_dl'

    def get_po_root(self):
        return 'po/'

    def get_pot_filename(self):
        return os.path.join(self.get_po_root(), '%s.pot' % self.GETTEXT_DOMAIN)

    @staticmethod
    def _run_subprocess(cmds):
        print(' '.join(cmds))
        subprocess.check_call(cmds)

    def merge_messages(self, old_file, new_file):
        self._run_subprocess(['msgmerge', '-N', old_file, '-o', new_file, self.get_pot_filename()])

    def update_gmo_internal(self, lang, po_file):
        locale_dir = 'share/locale/%s/LC_MESSAGES' % lang
        mkdir_p(locale_dir)
        self._run_subprocess([
            'msgfmt', '-o',
            os.path.join(locale_dir, 'youtube_dl.mo'),
            po_file])

    def update_po_internal(self, lang, po_file):
        old_po_file = po_file + '.old'
        rename_file(po_file, old_po_file)
        self.merge_messages(old_po_file, po_file)

    def for_all_po(self, callback):
        for f in os.listdir(self.get_po_root()):
            name, ext = os.path.splitext(f)
            if ext != '.po':
                continue

            callback(name, os.path.join(self.get_po_root(), f))

    def update_gmo(self):
        self.for_all_po(self.update_gmo_internal)

    def update_po(self):
        self.for_all_po(self.update_po_internal)

    def update_pot(self):
        pot_file = self.get_pot_filename()
        old_pot_file = self.get_pot_filename() + '.old'
        shutil.copy2(pot_file, old_pot_file)
        cmds = [
            'xgettext', '-d', self.GETTEXT_DOMAIN, '-j', '-k', '-ktr', '--from-code=utf-8', '-F', '-o',
            pot_file]
        cmds.extend(glob.glob('youtube_dl/*.py') + glob.glob('youtube_dl/*/*.py'))
        self._run_subprocess(cmds)
        self.merge_messages(old_pot_file, pot_file)


def main(argv):
    instance = I18N_Utils()
    if argv[1] == 'update-po':
        instance.update_po()
    elif argv[1] == 'update-gmo':
        instance.update_gmo()
    elif argv[1] == 'update-pot':
        instance.update_pot()

if __name__ == '__main__':
    main(sys.argv)
