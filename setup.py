#!/usr/bin/env python
# -*- coding: latin1 -*-

from setuptools import setup, find_packages

setup(name="pylatexparse",
      version="2019.1",
      description="Extensions for pycparser",
      long_description=open("README.rst", "r").read(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Other Audience',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Programming Language :: Python :: 3',
          'Topic :: Utilities',
          ],

      author="Andreas Kloeckner",
      url="http://pypi.python.org/pypi/pylatexparse",
      author_email="inform@tiker.net",
      license="MIT",
      packages=find_packages())
