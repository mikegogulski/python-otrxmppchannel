# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='OTRXMPPChannel',
    author='Mike Gogulski',
    author_email='mike@gogulski.com',
    maintainer='Mike Gogulski',
    maintainer_email='mike@gogulski.com',
    url='https://github.com/mikegogulski/python-otrxmppchannel',
    version='1.0.0',
    packages=['otrxmppchannel', ],
    install_requires=[
        'python-potr',
        'xmpppy', ],
    license='Unlicense',
    description='An OTR-XMPP communications channel',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications :: Chat',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
