#!/bin/bash

# Set environment variables based on the action inputs
export INPUT_TAG_NAME="v0.1.0"
export INPUT_CHAPTERS='[
  {
    "orgName": "absa-group",
    "repoName": "living-doc-example-project",
    "queryLabels": ["feature", "enhancement"]
  }
]'
export INPUT_WARNINGS="false"
export INPUT_PUBLISHED_AT="true"
export INPUT_SKIP_RELEASE_NOTES_LABEL="ignore-in-release"
export INPUT_PRINT_EMPTY_CHAPTERS="true"
export INPUT_CHAPTERS_TO_PR_WITHOUT_ISSUE="true"
export INPUT_VERBOSE="true"

# Run the Python script
python3 ./src/generate-release-notes.py
