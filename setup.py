#!/usr/bin/env python

from setuptools import setup, find_packages

setup(

    name='graypy',
    version='0.2.3',
    description="Python logging handler that sends messages in GELF (Graylog Extended Log Format).",
    long_description=open('README.rst').read(),
    keywords='logging gelf graylog2 graylog udp',
    author='Sever Banesiu',
    author_email='banesiu.sever@gmail.com',
    url='https://github.com/severb/graypy',
    license='BSD License',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,

)
