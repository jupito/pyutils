"""Miscellaneous utility funcionality."""

import logging
import os
import platform
import shlex
import shutil
import subprocess
import sys
import urllib
from functools import lru_cache
from itertools import chain
from pathlib import PurePath


def clamp(value, mn, mx):
    """Clamp value between minimun, maximum."""
    assert mn <= mx, (mn, mx)
    return max(min(value, mx), mn)


def int_or_float(x):
    """Return `x` as `int` if possible, or as `float` otherwise."""
    x = float(x)
    if x.is_integer():
        return int(x)
    return x


def asline(iterable, sep=' ', end='\n'):
    """Convert an iterable into a line."""
    return sep.join(str(x) for x in iterable) + end


@lru_cache(maxsize=32)
def get_prefix(n, factor=1024, prefixes=None):
    """Get magnitude prefix for number."""
    if prefixes is None:
        prefixes = ('',) + tuple('kMGTPEZY')
    if abs(n) < factor or len(prefixes) == 1:
        return n, prefixes[0]
    return get_prefix(n / factor, factor=factor, prefixes=prefixes[1:])


def fmt_size(n, unit='B'):
    """Format file size in human-readable manner (k, M, G, ...)."""
    if n is None:
        return '?{}'.format(unit)
    n, prefix = get_prefix(n)
    return '{:.0f}{}{}'.format(n, prefix, unit)


def fmt_args(cmd, *args, **kwargs):
    """Split first, then format. To easily have arguments with spaces."""
    return [x.format(**kwargs) for x in shlex.split(cmd)] + [os.fspath(x) for x
                                                             in args]


def esc_seq(n, s):
    """Escape sequence. Call sys.stdout.write() to apply."""
    return '\033]{};{}\007'.format(n, s)


def set_term_title(title):
    """Return control string for setting X terminal title."""
    return esc_seq(0, title)


def set_term_bg(color):
    """Return control string for setting X terminal background color, for
    example 'rgb:ff/ee/ee'.
    """
    return esc_seq(11, color)


def ring_bell():
    """Bell character."""
    return '\a'


def notify_send(summary, body=None, urgency=None, expire_time=None,
                app_name=None, icons=None, categories=None, hints=None,
                fgcolor=None, bgcolor=None, progress=None):
    """Send notification.

    At least dunst supports fgcolor, bgcolor, progress.
    """
    def _hint(typ, name, value):
        assert typ in ['int', 'double', 'string', 'byte'], typ
        return ['-h', '{}:{}:{}'.format(typ, name, value)]

    args = ['notify-send', summary]
    if body is not None:
        args.append(body)
    if urgency is not None:
        assert urgency in ['low', 'normal', 'critical'], urgency
        args.extend(['-u', urgency])
    if expire_time is not None:
        args.extend(['-t', str(expire_time)])
    if app_name is not None:
        args.extend(['-a', app_name])
    if icons:
        args.extend(['-i', ','.join(icons)])
    if categories:
        args.extend(['-c', ','.join(categories)])
    if hints:
        args.extend(chain.from_iterable(_hint(*x) for x in hints))
    if fgcolor is not None:
        args.extend(_hint('string', 'fgcolor', fgcolor))
    if bgcolor is not None:
        args.extend(_hint('string', 'bgcolor', bgcolor))
    if progress is not None:
        assert 0 <= progress <= 100, progress
        args.extend(_hint('int', 'value', progress))
    logging.debug('Running: %s', args)
    subprocess.check_call(args)


def truncate(s, reserved=0, columns=None, ellipsis='…', minimum_length=2):
    """Truncate string to fit limit, if possible."""
    if columns is None:
        columns = shutil.get_terminal_size().columns
    space_left = max(columns - reserved, minimum_length)
    if space_left < len(s):
        s = s[:space_left]
        if ellipsis:
            s = s[:-len(ellipsis)] + ellipsis
    return s


def camel(s):
    """Convert string to CamelCase."""
    return ''.join(x[0].upper() + x[1:].lower() for x in s.split())


def get_loglevel(name):
    """Return the numeric correspondent of a logging level name."""
    try:
        return getattr(logging, name.upper())
    except AttributeError:
        raise ValueError('Invalid log level: {}'.format(name))


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


def get_progname():
    """Get program name."""
    return PurePath(sys.argv[0]).name


def get_hostname():
    """Try to return system hostname in a portable fashion."""
    name = platform.uname().node
    if not name:
        raise OSError(None, 'Could not determine hostname')
    return name


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
        print(set_term_title(s[1:].format(**d)), end='', flush=True)

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


def peco(lines, initial=0, index=False, prg='peco'):
    """Use 'peco' to select items from list. Return selected lines, or None."""
    args = [prg, '--initial-index={}'.format(initial)]
    if index:
        lines = ('{} {}'.format(i, x) for i, x in enumerate(lines))
    d = dict(input='\n'.join(lines), stdout=subprocess.PIPE,
             universal_newlines=True)
    process = subprocess.run(args, **d)
    if process.stdout:
        # Filter tailing ''.
        output_lines = filter(None, process.stdout.split('\n'))
        if index:
            return [int(x.split(maxsplit=1)[0]) for x in output_lines]
        return output_lines
    return None
