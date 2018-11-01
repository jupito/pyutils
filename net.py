"""Network utility funcionality."""

import logging
import os
import shlex
import shutil
import urllib
from pathlib import PurePath

from pyutils.misc import fmt_size, truncate


def url_suffix(url):
    """URL filename suffix."""
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)  # See also unquote_plus().
    suffix = PurePath(path).suffix
    if not suffix:
        # Well, maybe the filename is in the query part.
        path = urllib.parse.unquote(parsed.query)
        suffix = PurePath(path).suffix
    return suffix


def download(url, dst_path, tmp_path=None, progress=True):
    """Download file, showing optional progress meter."""
    # TODO: Use newer py3 libs.
    # TODO: Use notifications: notify-send -h int:value:42 "Working ..."
    def report(cnt, blksize, total):
        """Reporter callback."""
        d = dict(d=truncate(os.fspath(dst_path), reserved=15))
        if total == 0:
            s = 'Download seems to be empty: %s'
            logging.warning(s, shlex.quote(dst_path))
            total = -1
        if total == -1:
            s = '\r{d}: {p} '
            d.update(p=fmt_size(cnt * blksize))
        else:
            s = '\r{d}: {t} {p:.0%} '
            d.update(t=fmt_size(total), p=min(cnt * blksize / total, 1))
        print(s.format(**d), end='', flush=True)
        # print(set_term_title(s[1:].format(**d)), end='', flush=True)

    d = {}
    if tmp_path is not None:
        d['filename'] = tmp_path
    if progress:
        d['reporthook'] = report
    try:
        filename, headers = urllib.request.urlretrieve(url, **d)
    except urllib.error.ContentTooShortError as e:
        # Didn't get all that was advertised.
        logging.error('%s: %s', e, url)
        return None
    except urllib.error.HTTPError as e:
        # Perhaps a problem with authentication, or a 404.
        logging.error('%s: %s', e, url)
        return None
    except urllib.error.URLError as e:
        logging.exception('%s: %s', e, url)
        # raise
        return None
    except UnicodeEncodeError as e:
        # Whatever this is... swith to py3 libs.
        logging.exception('%s: %s', e, url)
        return None
    else:
        shutil.move(filename, dst_path)
        if progress:
            print('OK')
    finally:
        urllib.request.urlcleanup()
    return headers
