#!/usr/bin/env python3

from setuptools import setup, find_packages

long_description = """
tropohelper is a library to speed up creating resources  using tropospher
and cloudformation on AWS. Troposphere makes it much easier, but it can really
make a file for creating a stack large and repedative. Using these helper
functions keeps things much more DRY.
"""

setup(
    name='tropohelper',
    version="1.1.1",
    description='tropohelper is a collection of troposphere helpers to promote DRY.',
    long_description=long_description,
    author='Michael Gorman',
    author_email='michael@michaeljgorman.com',
    url='https://github.com/mjgorman/tropohelper',
    packages=find_packages(),
    install_requires=['troposphere>=2.2.0', 'awacs>=0.7.2'],
    test_suite='nose.collector',
    tests_require=['nose<2.0']
)
