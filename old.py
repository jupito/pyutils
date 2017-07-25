"""Old stuff."""

import logging
import os


def walker(top, types='f'):
    """Yield all paths in subdirectories of root path. Kind of like find."""
    top = os.fspath(top)
    if os.path.isdir(top):
        it = os.walk(top, onerror=logging.error, followlinks=True)
        for dirpath, dirnames, filenames in it:
            if 'f' in types:
                for p in filenames:
                    yield os.path.join(dirpath, p)
            if 'd' in types:
                for p in dirnames:
                    yield os.path.join(dirpath, p)
    elif 'f' in types:
        yield top
