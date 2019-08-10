#!/usr/bin/env python
# -*- coding: latin1 -*-

from setuptools import setup, find_packages

setup(name="pylatexparse",
      version="2019.2",
      description="A parser and document tree for LaTeX documents",
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
      url="https://github.com/inducer/pylatexparse",
      author_email="inform@tiker.net",
      license="MIT",
      packages=find_packages())
