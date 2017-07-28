"""Argument parsing."""

import argparse
import shlex
from pathlib import Path


class DefaultValueHelpFormatter(argparse.HelpFormatter):
    """A formatter that appends possible default value to argument helptext."""
    def _expand_help(self, action):
        s = super()._expand_help(action)
        default = getattr(action, 'default', None)
        if default is None or default in [False, argparse.SUPPRESS]:
            return s
        return '{} (default: {})'.format(s, repr(default))


class FileArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser that is better for reading arguments from files.

    Set `fromfile_prefix_chars` to `@` by default; better
    `convert_arg_line_to_args()`; added `parse_from_files()`; added `add` as a
    shortcut to `add_argument`.
    """
    add = argparse.ArgumentParser.add_argument

    def __init__(self, fromfile_prefix_chars='@', **kwargs):
        super().__init__(fromfile_prefix_chars=fromfile_prefix_chars, **kwargs)

    def convert_arg_line_to_args(self, arg_line):
        """Fancier file reading."""
        return shlex.split(arg_line, comments=True)

    def parse_from_files(self, paths):
        """Parse known arguments from files."""
        prefix = self.fromfile_prefix_chars[0]
        args = ['{}{}'.format(prefix, x) for x in paths]
        return self.parse_known_args(args)

    # raise_on_error = True
    # def error(self, message):
    #     if self.raise_on_error:
    #         raise ValueError(message)
    #     super().error(message)


def get_basic_parser(formatter_class=DefaultValueHelpFormatter, **kwargs):
    """Get an argument parser with standard arguments ready."""
    p = FileArgumentParser(formatter_class=formatter_class, **kwargs)
    p.add('-v', '--verbose', action='count', default=0,
          help='increase verbosity')
    p.add('--logfile', type=Path, help='log file')
    p.add('--loglevel', default='WARNING', help='log level name')
    return p
