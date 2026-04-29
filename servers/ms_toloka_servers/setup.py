# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from setuptools import find_packages, setup

setup(
    name="ms_toloka_servers",
    version="0.1.0",
    packages=find_packages(include=["ms_toloka_servers", "ms_toloka_servers.*"]),
)
