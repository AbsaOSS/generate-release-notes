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
from release_notes_generator.model.record.hierarchy_issue_record import HierarchyIssueRecord
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

    def _find_catch_open_hierarchy_chapter(self) -> Chapter | None:
        """Return the first chapter with catch_open_hierarchy enabled, or None."""
        for ch in self.chapters.values():
            if ch.catch_open_hierarchy:
                return ch
        return None

    def _add_record_to_chapter(self, record_id: str, record: Record, chapter: Chapter) -> None:
        """Add a record to a chapter if not already present, tracking duplicity and verbose logging."""
        if record_id not in chapter.rows:
            if not chapter.hidden:
                record.add_to_chapter_presence(chapter.title)
            chapter.add_row(record_id, record.to_chapter_row(not chapter.hidden))
            if record_id not in self.populated_record_numbers_list:
                self.populated_record_numbers_list.append(record_id)
            if chapter.hidden and ActionInputs.get_verbose():
                logger.debug(
                    "Record %s assigned to hidden chapter '%s' (not counted for duplicity)",
                    record_id,
                    chapter.title,
                )

    def _try_route_to_coh_chapter(
        self, record_id: str, record: Record, record_labels: list[str], coh_chapter: Chapter
    ) -> bool:
        """Try to route an open HierarchyIssueRecord to the COH chapter.

        Returns:
            True if the record was routed to the COH chapter, False if the label filter excluded it.
        """
        if not coh_chapter.labels or any(lbl in coh_chapter.labels for lbl in record_labels):
            self._add_record_to_chapter(record_id, record, coh_chapter)
            return True
        return False

    def populate(self, records: dict[str, Record]) -> None:
        """
        Populates the custom chapters with records.

        Parameters:
            @param records: A dictionary of records keyed by 'owner/repo#number' and values are Record objects.

        Returns:
            None
        """
        hierarchy_enabled = ActionInputs.get_hierarchy()
        coh_chapter = self._find_catch_open_hierarchy_chapter()

        if coh_chapter and not hierarchy_enabled:
            logger.warning("catch-open-hierarchy has no effect when hierarchy is disabled")

        for record_id, record in records.items():  # iterate all records
            if not record.contains_change_increment():
                continue
            if record.skip:  # check if the record should be skipped - by user defined skip labels
                continue
            if isinstance(record, CommitRecord):  # commits have no labels
                continue

            record_labels = getattr(record, "labels", [])

            # Conditional Custom Chapter gate: intercept open hierarchy parents before label routing.
            # Note: precedes the record_labels early-exit so label-less HierarchyIssueRecord
            # is still routed to a no-filter COH chapter.
            if (
                hierarchy_enabled
                and coh_chapter is not None
                and isinstance(record, HierarchyIssueRecord)
                and record.is_open
            ):
                if self._try_route_to_coh_chapter(record_id, record, record_labels, coh_chapter):
                    continue

            if not record_labels:
                continue

            for ch in self.chapters.values():
                if ch.catch_open_hierarchy:
                    continue  # COH chapter is only populated via the hierarchy-state gate
                if any(lbl in ch.labels for lbl in record_labels):
                    self._add_record_to_chapter(record_id, record, ch)

    def _sorted_chapters(self) -> list[Chapter]:
        """Return chapters sorted by explicit order then first-seen position.

        Chapters with explicit order are rendered first (ascending).
        Chapters without order follow, preserving dict insertion order.
        """
        indexed: list[tuple[int, Chapter]] = list(enumerate(self.chapters.values()))
        with_order: list[tuple[int, int, Chapter]] = [
            (ch.order, pos, ch) for pos, ch in indexed if ch.order is not None
        ]
        without_order = [ch for _, ch in indexed if ch.order is None]
        with_order.sort(key=lambda t: (t[0], t[1]))
        return [ch for _, _, ch in with_order] + without_order

    def to_string(self) -> str:
        """
        Converts the custom chapters to a string, excluding hidden chapters.

        Returns:
            str: The chapters as a string with hidden chapters filtered out.
        """
        result = ""
        for chapter in self._sorted_chapters():
            # Skip hidden chapters from output
            if chapter.hidden:
                record_count = len(chapter.rows)
                if ActionInputs.get_verbose():
                    logger.debug("Skipping hidden chapter: %s (%d records tracked)", chapter.title, record_count)
                continue

            chapter_string = chapter.to_string(
                sort_ascending=self.sort_ascending, print_empty_chapters=self.print_empty_chapters
            )
            if chapter_string:
                result += chapter_string + "\n\n"

        # Note: strip is required to remove leading newline chars when empty chapters are not printed option
        return result.strip()

    def from_yaml_array(self, chapters: list[dict[str, Any]]) -> "CustomChapters":  # type: ignore[override]
        """
        Populate the custom chapters from a list of dict objects.

        Supports legacy single 'label' as well as new multi 'labels'. When both are present, 'labels' takes precedence.
        Supports 'catch-open-hierarchy: true' to mark a chapter as a Conditional Custom Chapter that intercepts open
        HierarchyIssueRecord parents before label-based routing. A catch-open-hierarchy chapter does not require a
        labels definition; if labels are provided they act as an optional filter.
        Unknown keys trigger a warning (once per chapter definition).
        Empty / invalid label definitions are skipped with a warning.

        Parameters:
            @param chapters: A list of dictionaries representing the chapters.

        Returns:
            The CustomChapters instance for chaining.
        """
        allowed_keys = {"title", "label", "labels", "hidden", "order", "catch-open-hierarchy"}
        coh_chapter_title: str | None = None  # track first catch-open-hierarchy chapter
        for chapter in chapters:
            if not isinstance(chapter, dict):
                logger.warning("Skipping chapter definition with invalid type %s: %s", type(chapter), chapter)
                continue
            if "title" not in chapter:
                logger.warning("Skipping chapter without title key: %s", chapter)
                continue
            title = chapter["title"]

            hidden = self._parse_bool_flag(title, chapter.get("hidden", False), "hidden")
            catch_open_hierarchy = self._parse_bool_flag(
                title, chapter.get("catch-open-hierarchy", False), "catch-open-hierarchy"
            )

            # Enforce single catch-open-hierarchy chapter constraint.
            # Same-title repeats are treated as a merge and allowed through.
            if catch_open_hierarchy:
                if coh_chapter_title is not None and coh_chapter_title != title:
                    logger.warning(
                        "Chapter '%s' has catch-open-hierarchy: true but '%s' already uses it; ignoring duplicate",
                        title,
                        coh_chapter_title,
                    )
                    catch_open_hierarchy = False
                elif coh_chapter_title is None:
                    coh_chapter_title = title
                # else: same title repeating COH — silent merge pass-through

            unknown = set(chapter.keys()) - allowed_keys
            if unknown:
                logger.warning("Chapter '%s' has unknown keys ignored: %s", title, ", ".join(sorted(unknown)))

            normalized = self._parse_labels_definition(title, chapter, catch_open_hierarchy)
            if normalized is None:
                if coh_chapter_title == title:  # release the reservation: chapter won't be created
                    coh_chapter_title = None
                continue

            parsed_order = self._parse_order_flag(title, chapter.get("order"))
            self._register_chapter(
                title,
                normalized,
                hidden=hidden,
                catch_open_hierarchy=catch_open_hierarchy,
                parsed_order=parsed_order,
            )

        return self

    @staticmethod
    def _parse_bool_flag(title: str, raw: Any, key: str) -> bool:
        """Parse and validate a boolean flag from a chapter config entry.

        Parameters:
            title: Chapter title (for warning messages).
            raw: Raw value from YAML.
            key: Config key name (for warning messages).

        Returns:
            Parsed boolean; defaults to False on invalid input.
        """
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, str):
            if raw.lower() == "true":
                return True
            if raw.lower() == "false":
                return False
            logger.warning("Chapter '%s' has invalid '%s' value: %s. Defaulting to false.", title, key, raw)
            return False
        logger.warning("Chapter '%s' has invalid '%s' value type: %s. Defaulting to false.", title, key, type(raw))
        return False

    @staticmethod
    def _parse_order_flag(title: str, raw_order: Any) -> int | None:
        """Parse and validate the 'order' flag from a chapter config entry.

        Parameters:
            title: Chapter title (for warning messages).
            raw_order: Raw value from YAML.

        Returns:
            Parsed integer order, or None if absent or invalid.
        """
        if raw_order is None:
            return None
        if isinstance(raw_order, bool):
            logger.warning(
                "Chapter '%s' has invalid 'order' value type: %s. Ignoring custom ordering input.",
                title,
                type(raw_order),
            )
            return None
        if isinstance(raw_order, int):
            return raw_order
        if isinstance(raw_order, str):
            try:
                return int(raw_order.strip())
            except ValueError:
                logger.warning(
                    "Chapter '%s' has invalid 'order' value: %s. Must be an integer."
                    " Ignoring custom ordering input.",
                    title,
                    raw_order,
                )
                return None
        logger.warning(
            "Chapter '%s' has invalid 'order' value type: %s. Ignoring custom ordering input.",
            title,
            type(raw_order),
        )
        return None

    @staticmethod
    def _parse_labels_definition(title: str, chapter: dict[str, Any], catch_open_hierarchy: bool) -> list[str] | None:
        """Parse and validate the labels definition for a chapter config entry.

        Parameters:
            title: Chapter title (for warning messages).
            chapter: Raw chapter dict from YAML.
            catch_open_hierarchy: Whether this chapter is a Conditional Custom Chapter.

        Returns:
            Normalised label list (may be empty for COH chapters with no labels), or None if the
            chapter should be skipped entirely.
        """
        has_labels = "labels" in chapter
        has_label = "label" in chapter

        raw_labels: Any = None
        if has_labels and has_label:
            logger.warning("Chapter '%s' both 'label' and 'labels' provided; using 'labels' (precedence)", title)
            raw_labels = chapter.get("labels")
        elif has_labels:
            raw_labels = chapter.get("labels")
        elif has_label:
            raw_labels = [chapter.get("label")]
        elif catch_open_hierarchy:
            return []  # COH chapters don't require labels
        else:
            logger.warning("Chapter '%s' has no 'label' or 'labels' key; skipping", title)
            return None

        if raw_labels is None:
            if catch_open_hierarchy:
                return []  # COH chapter with explicit null labels — treat as no-label filter
            logger.warning("Chapter '%s' has null labels value; skipping", title)
            return None

        if not isinstance(raw_labels, (str, list)):
            logger.warning(
                "Chapter '%s' invalid labels type (%s); expected string or list; skipping", title, type(raw_labels)
            )
            return None

        normalized = _normalize_labels(raw_labels)
        if not normalized:
            logger.warning("Chapter '%s' labels definition empty after normalization; skipping", title)
            return None

        if ActionInputs.get_verbose():
            logger.debug("Chapter '%s' normalized labels: %s", title, normalized)
        return normalized

    def _register_chapter(
        self,
        title: str,
        normalized: list[str],
        *,
        hidden: bool,
        catch_open_hierarchy: bool,
        parsed_order: int | None,
    ) -> None:
        """Register a new chapter or merge labels into an existing one.

        Parameters:
            title: Chapter title.
            normalized: Normalised label list.
            hidden: Whether the chapter is hidden.
            catch_open_hierarchy: Whether the chapter is a Conditional Custom Chapter.
            parsed_order: Explicit render order, or None.
        """
        if title not in self.chapters:
            self.chapters[title] = Chapter(title, normalized)
            self.chapters[title].hidden = hidden
            self.chapters[title].order = parsed_order
            self.chapters[title].catch_open_hierarchy = catch_open_hierarchy
            if hidden:
                logger.info(
                    "Chapter '%s' marked as hidden, will not appear in output (but records will be tracked)", title
                )
        else:
            # Merge while preserving order & avoiding duplicates
            existing = self.chapters[title].labels
            for lbl in normalized:
                if lbl not in existing:
                    existing.append(lbl)
            self.chapters[title].hidden = hidden
            if catch_open_hierarchy:
                self.chapters[title].catch_open_hierarchy = True
            if hidden:
                logger.info(
                    "Chapter '%s' marked as hidden, will not appear in output (but records will be tracked)", title
                )
            # Handle order merging: keep first explicit value, warn on conflict
            existing_order = self.chapters[title].order
            if parsed_order is not None:
                if existing_order is None:
                    self.chapters[title].order = parsed_order
                elif existing_order != parsed_order:
                    logger.warning(
                        "Chapter '%s' has conflicting order values: %d vs %d. Keeping first value %d.",
                        title,
                        existing_order,
                        parsed_order,
                        existing_order,
                    )
