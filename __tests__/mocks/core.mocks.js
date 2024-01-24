const fullDefaultInputs = (name) => {
    switch (name) {
        case 'tag-name':
            return 'v0.1.0';
        case 'chapters':
            return JSON.stringify([
                {"title": "Breaking Changes 💥", "label": "breaking-change"},
                {"title": "New Features 🎉", "label": "enhancement"},
                {"title": "New Features 🎉", "label": "feature"},
                {"title": "Bugfixes 🛠", "label": "bug"}
            ]);
        case 'warnings':
            return 'true';
        case 'published-at':
            return 'false';
        case 'skip-release-notes-label':
            return null;
        case 'print-empty-chapters':
            return 'true';
        default:
            return null;
    }
};

module.exports = {
    fullDefaultInputs,
};