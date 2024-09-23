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

from release_notes_generator.utils.utils import get_change_url, detect_row_format_invalid_keywords


# get_change_url


def test_get_change_url_no_repository():
    url = get_change_url(tag_name="v2.0.0")
    assert url == ""


def test_get_change_url_no_git_release(mock_repo):
    url = get_change_url(tag_name="v1.0.0", repository=mock_repo)
    assert url == "https://github.com/org/repo/commits/v1.0.0"


def test_get_change_url_with_git_release(mock_repo, mock_git_release):
    url = get_change_url(tag_name="v2.0.0", repository=mock_repo, git_release=mock_git_release)
    assert url == "https://github.com/org/repo/compare/v1.0.0...v2.0.0"


# detect_row_format_invalid_keywords


def test_valid_row_format():
    """Test when all keywords in the row format are valid."""
    row_format = "{number} - {title} in {pull-requests}"
    errors = detect_row_format_invalid_keywords(row_format)
    assert not errors, "Expected no errors for valid keywords"


def test_multiple_invalid_keywords():
    """Test when there are multiple invalid keywords in the row format."""
    row_format = "{number} - {link} - {Title} and {Pull-requests}"
    errors = detect_row_format_invalid_keywords(row_format)
    assert len(errors) == 1
    assert "Invalid Issue row format keyword(s) found: link, Title, Pull-requests" in errors[0]
