"""Paths, files, and such."""

from collections.abc import MutableMapping
from contextlib import contextmanager
import logging
import shutil
import os
from pathlib import Path
import tempfile


class XAttr(MutableMapping):
    """Dict-like interface to extended attributes."""
    def __init__(self, path, follow_symlinks=True):
        self.path = os.fspath(path)
        self.follow_symlinks = follow_symlinks

    def _wrapper(self, f, *args):
        """General wrapper with follow_symlinks and KeyError."""
        try:
            return f(self.path, *args, follow_symlinks=self.follow_symlinks)
        except OSError as e:
            if e.errno == 61:
                raise KeyError(*args)
            raise

    # TODO: Use functools.partialmethod().
    def _list(self):
        """Read attribute names."""
        return self._wrapper(os.listxattr)

    def __getitem__(self, key):
        return self._wrapper(os.getxattr, key)

    def __setitem__(self, key, value):
        self._wrapper(os.setxattr, key, value)

    def __delitem__(self, key):
        self._wrapper(os.removexattr, key)

    def __iter__(self):
        return iter(self._list())

    def __len__(self):
        return len(self._list())

    def __contains__(self, key):
        return key in self._list()

    def __repr__(self):
        return '{0.__class__.__name__}({0.path!r})'.format(self)


@contextmanager
def temp_dir(**kwargs):
    """A temporary directory context that deletes it afterwards."""
    # TODO: Use tempfile.TemporaryDirectory() instead.
    tmpdir = tempfile.mkdtemp(**kwargs)
    try:
        yield Path(tmpdir)
    finally:
        try:
            shutil.rmtree(tmpdir)
        except FileNotFoundError:
            pass


@contextmanager
def tempfile_and_backup(path, mode, bakext='.bak', **kwargs):
    """Create a temporary file for writing, do backup, replace destination."""
    path = os.fspath(path)
    if os.path.exists(path) and not os.path.isfile(path):
        raise IOError('Not a regular file: {}'.format(path))
    with tempfile.NamedTemporaryFile(mode=mode, delete=False, **kwargs) as fp:
        try:
            yield fp
            fp.close()
            if os.path.exists(path):
                shutil.copy2(path, path + bakext)
            shutil.move(fp.name, path)
        finally:
            fp.close()
            if os.path.exists(fp.name):
                os.remove(fp.name)


def ensure_dir(path):
    """Ensure existence of the file's parent directory."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def sanitize_line(line, commenter='#'):
    """Clean up input line."""
    return line.split(commenter, 1)[0].strip()


def valid_lines(path, commenter='#'):
    """Read and yield lines that are neither empty nor comments."""
    with open(path, 'r') as fp:
        lines = (sanitize_line(x, commenter=commenter) for x in fp)
        for line in filter(None, lines):
            yield line


def copy_times(src, dst):
    """Copy atime and mtime from src to dst, following symlinks."""
    src = os.fspath(src)
    dst = os.fspath(dst)
    st = os.stat(src)
    try:
        os.utime(dst, ns=(st.st_atime_ns, st.st_mtime_ns))
    except (TypeError, AttributeError):
        os.utime(dst, (st.st_atime, st.st_mtime))  # Pre-3.3 has no nanosec.


def move(src, dst):
    """Move path."""
    # Note: pathlib cannot handle cross-device operations.
    return shutil.move(os.fspath(src), os.fspath(dst))


def rm_rf(path):
    """Recursively remove path, whatever it is, if it exists. Like rm -rf."""
    path = os.fspath(path)
    if os.path.exists(path):
        logging.info('Removing: %s', format(path))
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
