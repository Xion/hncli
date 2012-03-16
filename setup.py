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
	     "Development Status :: 2 - Pre-Alpha",
	     "Environment :: Console",
	     "Intended Audience :: Developers",
	     "Intended Audience :: End Users/Desktop",
	     "Intended Audience :: Information Technology",
	     "Intended Audience :: System Administrators",
	     "License :: OSI Approved :: MIT License",
	     "Natural Language :: English",
	     "Operating System :: OS Independent",
	     "Programming Language :: Python",
	     "Topic :: Internet",
	     "Topic :: Internet :: WWW/HTTP",
	     "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Message Boards",
	     "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary",
	  ],

	  install_requires=[
	     'requests',
	     'beautifulsoup4',
	  ],

	  packages=find_packages(),
	  entry_points={'console_scripts': ['hncli=hncli.main:main']},
)