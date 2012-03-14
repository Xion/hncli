#!/usr/bin/env python
'''
hncli (Hacker News command line client)
Setup script
'''
from setuptools import setup, find_packages


setup(name="hncli",
	  version="0.1",
	  description="Command line client for Hacker News",
	  author='Karol Kuczmarski "Xion"',
	  author_email="karol.kuczmarski@gmail.com",
	  url="http://github.com/Xion/hncli",
	  license="MIT",

	  classifiers=[
	  ],

	  install_requires=[
	     'requests',
	     'BeautifulSoup',
	  ],

	  packages=find_packages(),
	  entry_points={'console_scripts': ['hncli=hncli.main:main']},
)