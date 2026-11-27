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

from release_notes_generator.utils.utils import get_change_url, is_prerelease_tag, normalize_version_tag

# --- get_change_url ---


def test_get_change_url_no_repository():
    url = get_change_url(tag_name="v2.0.0")
    assert url == ""


def test_get_change_url_no_git_release(mock_repo):
    url = get_change_url(tag_name="v1.0.0", repository=mock_repo)
    assert url == "https://github.com/org/repo/commits/v1.0.0"


def test_get_change_url_with_git_release(mock_repo, mock_git_release):
    url = get_change_url(tag_name="v2.0.0", repository=mock_repo, git_release=mock_git_release)
    assert url == "https://github.com/org/repo/compare/v1.0.0...v2.0.0"


def test_get_change_url_with_prerelease_tag(mock_repo, mock_git_release):
    """A pre-release tag name appears in the compare link exactly as given."""
    url = get_change_url(tag_name="v1.1.0rc1", repository=mock_repo, git_release=mock_git_release)
    assert url == "https://github.com/org/repo/compare/v1.0.0...v1.1.0rc1"


# --- normalize_version_tag ---


@pytest.mark.parametrize(
    "tag, expected",
    [
        ("v0.9.0rc1", "v0.9.0rc1"),
        ("v0.9.0-RC1", "v0.9.0-RC1"),
        ("1.2.3a1", "v1.2.3a1"),
        ("v1.2.3b2", "v1.2.3b2"),
        ("v1.0.0-alpha.1", "v1.0.0-alpha.1"),
        ("v1.2.3-0", "v1.2.3-0"),
        ("v1.2.3-alpha.0", "v1.2.3-alpha.0"),
        ("v1.2.3-01a", "v1.2.3-01a"),
        ("v1.0.0-SNAPSHOT", "v1.0.0-SNAPSHOT"),
        ("v1.0.0-HF1", "v1.0.0-HF1"),
        ("v1.2-RC1", "v1.2.0-RC1"),
        ("v1.2rc1", "v1.2.0rc1"),
        (" v0.9.0rc1 ", "v0.9.0rc1"),
    ],
)
def test_normalize_version_tag_keeps_prerelease_suffix(tag, expected):
    """A SemVer or PEP 440 pre-release suffix stays after vMAJOR.MINOR.PATCH as given."""
    assert normalize_version_tag(tag) == expected


@pytest.mark.parametrize(
    "tag, expected",
    [
        ("v1.2", "v1.2.0"),
        ("1.2", "v1.2.0"),
        ("1.2.3", "v1.2.3"),
        ("v1.2.3", "v1.2.3"),
        (" v1.2.3 ", "v1.2.3"),
    ],
)
def test_normalize_version_tag_short_forms(tag, expected):
    """Tags without a suffix still normalize to vMAJOR.MINOR.PATCH."""
    assert normalize_version_tag(tag) == expected


@pytest.mark.parametrize("tag", ["", "   "])
def test_normalize_version_tag_empty(tag):
    """An empty or whitespace-only tag normalizes to an empty string."""
    assert normalize_version_tag(tag) == ""


@pytest.mark.parametrize(
    "tag",
    [
        "master",
        "v1",
        "v1.2.beta",
        "v1.2.3rc",
        "v1.2.3-",
        "v1.2.3+build",
        "v1.2.3-RC1+build",
        "v1.2.3 rc1",
        "v1.2.3RC1",
        "v1.2.3c1",
        "v1.2.3.rc1",
        "v1.2.3-a..b",
        "v1.2.3-01",
        "v1.2.3-alpha.01",
        "v1.2.3-RC1;rm",
        "v1.2.3rc١",
        "v١.2.3",
    ],
)
def test_normalize_version_tag_malformed(tag):
    """A malformed tag raises ValueError naming the tag and the accepted forms."""
    with pytest.raises(ValueError) as excinfo:
        normalize_version_tag(tag)
    assert str(excinfo.value) == (
        "Invalid version tag format: {!r}. Expected vMAJOR.MINOR[.PATCH] with an optional pre-release suffix, "
        "e.g. 'v0.2', 'v0.2.0', 'v0.2.0-RC1' or 'v0.2.0rc1'.".format(tag)
    )


# --- is_prerelease_tag ---


@pytest.mark.parametrize(
    "tag",
    ["v0.9.0rc1", "v0.9.0-RC1", "v1.2.3a1", "v1.2.3b2", "v1.0.0-alpha.1", "v1.0.0-HF1", "v1.2-RC1", " v1.2.3rc1 "],
)
def test_is_prerelease_tag_true(tag):
    """A valid tag with a pre-release suffix is a pre-release."""
    assert is_prerelease_tag(tag) is True


@pytest.mark.parametrize("tag", ["v1.2.3", "v1.2", "1.2.3", "", "master", "v1.2.3rc", "v1.2.3-"])
def test_is_prerelease_tag_false(tag):
    """A final tag, an empty tag, or a malformed tag is not a pre-release."""
    assert is_prerelease_tag(tag) is False
