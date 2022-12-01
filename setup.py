# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import os.path

readme = ''
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.rst')
if os.path.exists(readme_path):
    with open(readme_path, 'rb') as stream:
        readme = stream.read().decode('utf8')

setup(
    long_description=readme,
    name='birdfeeder-coinalpha',
    version='1.3.0',
    description='Helper library for CoinAlpha projects',
    python_requires='==3.*,>=3.8.0',
    project_urls={"repository": "https://github.com/coinalpha/birdfeeder"},
    author='Vladimir Kamarzin',
    author_email='vvk@vvk.pp.ru',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={"console_scripts": ["build_image = birdfeeder.build_image:app"]},
    packages=['birdfeeder', 'birdfeeder.aws', 'birdfeeder.enum', 'birdfeeder.pydantic', 'birdfeeder.sqlalchemy'],
    package_dir={"": "."},
    package_data={},
    install_requires=[
        'aioconsole>=0.1.16',
        'aiohttp==3.*,>=3.2.0',
        'aiorun==2020.*,>=2020.0.0',
        'boto3==1.*,>=1.0.0',
        'cachetools==4.*,>=4.0.0',
        'environs==9.*,>=9.0.0',
        'kafka-python==2.*,>=2.0.0',
        'pandas==1.*,>=1.1.0',
        'pydantic==1.*,>=1.9.0',
        'python-json-logger==2.*,>=2.0.0',
        'ruamel.yaml==0.*,>=0.16.0',
        'typer>=0.3',
    ],
    extras_require={
        "dev": [
            "docker==4.*,>=4.0.0",
            "mysqlclient==2.*,>=2.0.0",
            "poetry2conda==0.*,>=0.3.0",
            "pre-commit==2.*,>=2.2.0",
            "pymysql==1.*,>=1.0.2",
            "pytest==6.*,>=6.0.0",
            "pytest-aiohttp",
            "pytest-asyncio==0.*,>=0.14.0",
            "pytest-cov==2.*,>=2.7.0",
            "pytest-mock==3.*,>=3.1.0",
            "redis==3.*,>=3.5.0",
            "sqlalchemy==1.*,>=1.4.0",
            "sqlalchemy-utils==0.*,>=0.37.0",
        ]
    },
)
