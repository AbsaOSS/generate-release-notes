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

"""
This module provides utilities for GitHub Actions.
"""

import os
import sys
from typing import Optional


def get_action_input(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve the value of a specified input parameter from environment variables.

    @param name: The name of the input parameter.
    @param default: The default value to return if the environment variable is not set.

    @return: The value of the specified input parameter, or an empty string if the environment
    """
    if default is None:
        return os.getenv(f'INPUT_{name.replace("-", "_").upper()}')
    else:
        return os.getenv(f'INPUT_{name.replace("-", "_").upper()}', default=default)


def set_action_output(name: str, value: str, default_output_path: str = "default_output.txt"):
    """
    Write an action output to a file in the format expected by GitHub Actions.

    @param name: The name of the output parameter.
    @param value: The value of the output parameter.
    @param default_output_path: The default file path to which the output is written if the
    'GITHUB_OUTPUT' environment variable is not set. Defaults to "default_output.txt".
    """
    output_file = os.getenv("GITHUB_OUTPUT", default_output_path)
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"{name}<<EOF\n")
        f.write(f"{value}")
        f.write("EOF\n")


def set_action_failed(message: str) -> None:
    """
    Mark the GitHub Action as failed and exit with an error message.

    @param message: The error message to be displayed.
    @return: None
    """
    print(f"::error::{message}")
    sys.exit(1)
