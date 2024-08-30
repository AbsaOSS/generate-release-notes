#
# Copyright 2024 ABSA Group Limited
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
This module contains a method to set up logging in the project.
"""

import logging
import os
import sys


def setup_logging() -> None:
    """
    Set up the logging configuration in the project

    @return: None
    """
    # Load logging configuration from the environment variables
    is_verbose_logging: bool = os.getenv("INPUT_VERBOSE", "false").lower() == "true"
    is_debug_mode = os.getenv("RUNNER_DEBUG", "0") == "1"
    level = logging.DEBUG if is_verbose_logging or is_debug_mode else logging.INFO

    # Set up the logging configuration
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    sys.stdout.flush()

    logging.info("Setting up logging configuration")

    if is_debug_mode:
        logging.debug("Debug mode enabled by CI runner")
    if is_verbose_logging:
        logging.debug("Verbose logging enabled")
