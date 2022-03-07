#!/usr/bin/env python
# coding: utf-8
#
# Licensed under MIT
#
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    install_requires=['flask>=2.0.1','requests'],
    version='1.0.10',
    long_description=long_description,
    long_description_content_type="text/markdown",
    description="APP性能测试 - Simple test in SoloX",
    packages=setuptools.find_namespace_packages(include=["solox", "solox.*"], ),
    include_package_data=True
)