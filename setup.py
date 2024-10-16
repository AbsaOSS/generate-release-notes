#
# Copyright 2023 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os

from setuptools import setup

# add pylint exception for R1732
# pylint: disable=consider-using-with
setup(
    name="release_notes_generator",
    version="0.1.0",
    description="A tool to generate release notes for GitHub projects.",
    long_description=open("README.md", "r", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Miroslav Pojer",
    author_email="miroslav.pojer@absa.africa",
    url="https://github.com/AbsaOSS/generate-release-notes",
    packages=["release_notes_generator", "tests"],
    install_requires=[
        "PyGithub",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "generate-release-notes=main:run",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: Apache 2.0 License",
        "Programming Language :: Python :: 3.11",
    ],
)
