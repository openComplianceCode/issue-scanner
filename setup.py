#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import distutils.cmd
import os
import subprocess
import sys

from setuptools import setup, find_packages
import setuptools.command.build_py


sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))


__author__ = "Yixiong Chen"
__email__ = "chenyxbear@gmail.com"


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
  """
  Utility function to read the README file.
  :param fname: Path to file to read
  :rtype: String
  Returns file content
  """
  return open(os.path.join(os.path.dirname(__file__), fname)).read()


requirements = [
  'scancode-toolkit>=30.1.0',
  'beautifulsoup4==4.11.1',
  'grimoirelab_toolkit==0.1.12',
  'isort==5.10.1',
  'jsonpath==0.82',
  'perceval==0.17.17',
  'perceval_weblate==0.1.2',
  'PyMySQL==0.9.3',
  'pyrpm==0.4',
  'PyYAML==6.0'
  'requests==2.26.0',
  'scipy==1.7.1',
  'setuptools==58.1.0',
  'SQLAlchemy==1.3.24',
  'tornado==6.1',
  'tqdm==4.62.3',
  'urllib3==1.25.8'
  'python-rpm-spec==0.11'
]


metadata = dict(
  name = "scraw",
  version = "0.0.1",
  author = "Yixiong Chen",
  author_email = "chenyxbear@gmail.com",
  description = ("An license scanner."),
  license = "",
  python_requires = ">=3.5",
  install_requires = requirements,
)

setup(**metadata)
