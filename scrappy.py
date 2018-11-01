#!/usr/bin/python3

"""Scrape web."""

import logging
from functools import lru_cache
from http import HTTPStatus
from urllib.request import urlopen
# import urllib3
# import requests

from bs4 import BeautifulSoup
import click

# PARSER = 'html.parser'
PARSER = 'lxml'
# PARSER = 'lxml-xml'
# PARSER = 'html5lib'


class Scrappy():
    """Scraper utility."""
    def __init__(self, url, parser=PARSER):
        self._url = url
        self._response = urlopen(url)
        self._soup = BeautifulSoup(self._response, parser)

    @property
    def url(self):
        return self._url

    @property
    def real_url(self):
        return self._response.geturl()

    @property
    @lru_cache(maxsize=None)
    def code(self):
        """Get HTTP status code, or None on unknown code."""
        try:
            # pylint: disable=no-value-for-parameter
            return HTTPStatus(self._response.getcode())
        except ValueError:
            return None

    @property
    @lru_cache(maxsize=None)
    def info(self):
        """Get connection response info."""
        return self._response.info().items()

    @property
    @lru_cache(maxsize=None)
    def title(self):
        """Get document title."""
        title = self._soup.title
        if title is None:
            return None
        return title.string.strip()

    def links(self):
        """Get links."""
        # tags = self._soup.find_all()
        tags = self._soup.find_all('link')
        for tag in tags:
            d = tag.attrs
            href = d.pop('href', '-')
            yield href, d


@click.command()
@click.argument('url')
@click.option('-v', '--verbose', count=True, help='Increase verbosity')
@click.option('-r', '--response', is_flag=True, help='Show response info')
@click.option('-l', '--links', is_flag=True, help='Show links')
def cli(url, verbose, response, links):
    """CLI program."""
    echo = click.echo
    try:
        scr = Scrappy(url)
    except AttributeError as e:
        logging.exception((e, url))
        raise

    if scr.code:
        echo((scr.code.value, scr.code.name))
    if verbose:
        echo(scr.url)
    echo(scr.real_url)
    if response:
        for i, (k, v) in enumerate(scr.info):
            # echo('{:4}: {}: {}'.format(i, k, v))
            echo(f'{i:4}: {k}: {v}')

    echo('Title: {}'.format(scr.title))
    if links:
        echo('Links: -')
        for i, (href, d) in enumerate(scr.links()):
            # echo('{:4}: {}: {}'.format(i, href, d))
            echo(f'{i:4}: {href}: {d}')
