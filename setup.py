#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
      name='kagtcprlib',
      version='0.2.1',
      description="TCPR library for King Arthur's Gold",
      long_description=open("README.md").read(),
      author='Benjamin Gorman',
      author_email='8076bgorman@gmail.com',
      url='https://github.com/benjamingorman/kagtcprlib',
      classifiers=[
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
      ],
      packages=find_packages(exclude=("tests",)),
      include_package_data=True,
      package_dir={'kagtcprlib': 'kagtcprlib'},
      package_data={'': ['web/**/*',]},
)
