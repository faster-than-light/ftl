#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='bugcatcher',
    version='0.1.8',
    author='Faster Than Light',
    author_email='devops@fasterthanlight.dev',
    maintainer='Faster Than Light',
    maintainer_email='devops@fasterthanlight.dev',
    license='GNU GPL v2.0',
    url='https://github.com/faster-than-light/bugcatcher',
    description='Faster Than Light Command Line Test Client',
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=['bugcatcher'],
    packages=['bugcatcher'],
    install_requires=[
        'gitpython',
        'requests',
        'colorama',
        'pytest>=3.5.0'
    ],
    python_requires='>=3.4',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    ],
    entry_points={
        'pytest11': [
            'ftl = bugcatcher.ftl:main',
        ],
        'console_scripts': [
            'ftl = bugcatcher.ftl:main',
        ],
    },
)
