# Generate Release Notes Action

TODO - update the file content after implementation


This GitHub Action automatically generates release notes for a given release tag, categorizing contributions into user-defined chapters based on labels.

## Usage

To use the action, add the following step to your workflow:

```yaml
- name: Generate Release Notes
  uses: AbsaOSS/generate-release-notes@v1-notes
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    tag_name: ${{ steps.set_tag.outputs.tag }}
    release_name: v${{ steps.set_tag.outputs.tag }}
    chapters: '[
      {"title": "Breaking Changes 💥", "label": "breaking-change"},
      {"title": "New Features 🎉", "label": "enhancement"},
      {"title": "New Features 🎉", "label": "feature"},
      {"title": "Bugfixes 🛠", "label": "bugfix"}
    ]'


To build
npm install
npm run build

commit action.yml and dist/index.js