# http://click.pocoo.org/5/setuptools/

from setuptools import find_packages, setup

setup(
    name='pyutils-jupito',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        scrappy=pyutils-jupito.scripts.scrappy:cli
    ''',
)
