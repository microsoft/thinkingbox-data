# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from setuptools import find_packages, setup

setup(
    name="sandbox_servers",
    version="0.1.0",
    packages=find_packages(include=["sandbox_servers", "sandbox_servers.*"]),
)
