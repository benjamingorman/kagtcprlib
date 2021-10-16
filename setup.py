#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
      name='kagtcprlib',
      version='0.2.1',
      description="TCPR library for King Arthur's Gold",
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      author='Benjamin Gorman',
      author_email='8076bgorman@gmail.com',
      url='https://github.com/benjamingorman/kagtcprlib',
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            "Operating System :: OS Independent",
      ],
      install_requires=["toml", "xmltodict", "simple-websocket-server"],
      packages=find_packages(exclude=("tests",)),
      include_package_data=True,
      package_dir={'kagtcprlib': 'kagtcprlib'},
      package_data={'': ['web/**/*',]},
)
