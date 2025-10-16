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
This module contains the CustomChapters class which is responsible for representing the custom chapters in the release
notes.
"""
import logging
from typing import Any, Iterable

from release_notes_generator.action_inputs import ActionInputs
from release_notes_generator.chapters.base_chapters import BaseChapters
from release_notes_generator.model.chapter import Chapter
from release_notes_generator.model.record.commit_record import CommitRecord
from release_notes_generator.model.record.record import Record

logger = logging.getLogger(__name__)


def _normalize_labels(raw: Any) -> list[str]:  # helper for multi-label
    """Normalize a raw labels definition into an ordered, de-duplicated list.

    Parameters:
        - str: may contain newlines and/or commas
        - list[str]: already a sequence of labels (will still be trimmed & deduped)

    Returns:
        Ordered list preserving first occurrence order; excludes empty tokens.
        Invalid (non str/list) returns empty list to be handled by caller.
    """
    if isinstance(raw, list):
        working: Iterable[Any] = raw
    elif isinstance(raw, str):
        # newline first then comma per spec
        parts: list[str] = []
        for line in raw.splitlines():
            for token in line.split(","):
                parts.append(token)
        working = parts
    else:
        return []

    cleaned: list[str] = []
    seen: set[str] = set()
    for item in working:
        if not isinstance(item, str):  # skip non-string items silently
            continue
        token = item.strip()
        if not token:  # skip empty after trimming
            continue
        if token in seen:  # de-duplicate preserving first occurrence
            continue
        seen.add(token)
        cleaned.append(token)
    return cleaned


class CustomChapters(BaseChapters):
    """
    A class used to represent the custom chapters in the release notes.
    """

    def populate(self, records: dict[str, Record]) -> None:
        """
        Populates the custom chapters with records.

        Parameters:
            @param records: A dictionary of records keyed by 'owner/repo#number' and values are Record objects.

        Returns:
            None
        """
        for record_id, record in records.items():  # iterate all records
            if not record.contains_change_increment():
                continue
            if record.skip:  # check if the record should be skipped - by user defined skip labels
                continue
            if isinstance(record, CommitRecord):  # commits have no labels
                continue

            record_labels = getattr(record, "labels", [])
            if not record_labels:
                continue

            for ch in self.chapters.values():
                # Quick intersection check
                if any(lbl in ch.labels for lbl in record_labels):
                    if record_id not in ch.rows:
                        ch.add_row(record_id, record.to_chapter_row(True))
                        # Track for backward compatibility (not used for gating anymore)
                        if record_id not in self.populated_record_numbers_list:
                            self.populated_record_numbers_list.append(record_id)

    def from_yaml_array(self, chapters: list[dict[str, Any]]) -> "CustomChapters":  # type: ignore[override]
        """
        Populate the custom chapters from a list of dict objects.

        Supports legacy single 'label' as well as new multi 'labels'. When both are present, 'labels' takes precedence.
        Unknown keys trigger a warning (once per chapter definition).
        Empty / invalid label definitions are skipped with a warning.

        Parameters:
            @param chapters: A list of dictionaries representing the chapters.

        Returns:
            The CustomChapters instance for chaining.
        """
        allowed_keys = {"title", "label", "labels"}
        for chapter in chapters:
            if not isinstance(chapter, dict):
                logger.warning("Skipping chapter definition with invalid type %s: %s", type(chapter), chapter)
                continue
            if "title" not in chapter:
                logger.warning("Skipping chapter without title key: %s", chapter)
                continue
            title = chapter["title"]

            has_labels = "labels" in chapter
            has_label = "label" in chapter

            # Warn on unknown keys
            unknown = set(chapter.keys()) - allowed_keys
            if unknown:
                logger.warning("Chapter '%s' has unknown keys ignored: %s", title, ", ".join(sorted(unknown)))

            raw_labels: Any = None
            if has_labels and has_label:
                logger.warning("Chapter '%s' both 'label' and 'labels' provided; using 'labels' (precedence)", title)
                raw_labels = chapter.get("labels")
            elif has_labels:
                raw_labels = chapter.get("labels")
            elif has_label:
                # Wrap legacy single label in a list to append below
                raw_labels = [chapter.get("label")]
            else:
                logger.warning("Chapter '%s' has no 'label' or 'labels' key; skipping", title)
                continue

            # Type validation & normalization
            if not isinstance(raw_labels, (str, list)):
                logger.warning(
                    "Chapter '%s' invalid labels type (%s); expected string or list; skipping", title, type(raw_labels)
                )
                continue

            normalized = _normalize_labels(raw_labels)
            if not normalized:
                logger.warning("Chapter '%s' labels definition empty after normalization; skipping", title)
                continue

            if ActionInputs.get_verbose():
                logger.debug("Chapter '%s' normalized labels: %s", title, normalized)

            if title not in self.chapters:
                self.chapters[title] = Chapter(title, normalized)
            else:
                # Merge while preserving order & avoiding duplicates
                existing = self.chapters[title].labels
                for lbl in normalized:
                    if lbl not in existing:
                        existing.append(lbl)

        return self
