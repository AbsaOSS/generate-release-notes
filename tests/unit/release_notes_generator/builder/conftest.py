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
import pytest


@pytest.fixture(autouse=True)
def _disable_stats_chapters(mocker):
    """Disable stats chapters for all existing builder tests to avoid output changes."""
    mocker.patch(
        "release_notes_generator.builder.builder.ActionInputs.get_show_stats_chapters",
        return_value=False,
    )
