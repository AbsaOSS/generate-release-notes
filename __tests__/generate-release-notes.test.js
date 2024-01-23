const { Octokit } = require("@octokit/rest");
const core = require('@actions/core');
const github = require('@actions/github');
const { run } = require('./../scripts/generate-release-notes');

jest.mock('@octokit/rest');
jest.mock('@actions/core');
jest.mock('@actions/github');

describe('run', () => {
    beforeEach(() => {
        // Reset environment variables and mocks before each test
        process.env.GITHUB_TOKEN = 'fake-token';
        process.env.GITHUB_REPOSITORY = 'owner/repo';

        jest.resetAllMocks();

        // Mock the inputs - keep the action default values
        core.getInput.mockImplementation((name) => {
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
        });

        github.context.repo = { owner: 'owner', repo: 'repo' };

        // Reset Octokit mock
        Octokit.mockImplementation(() => ({
            rest: {
                repos: {
                    getLatestRelease: jest.fn().mockResolvedValue({ data: {
                            tag_name: 'v1.0.0',
                            published_at: '2023-12-12T09:58:30.000Z',
                            created_at: '2023-12-12T09:56:30.000Z',
                        } }),
                },
                issues: {
                    listForRepo: jest.fn().mockResolvedValue({
                        data: [
                            {
                                number: 1,
                                title: 'Issue 1',
                                state: 'closed',
                                labels: [{ name: 'bug' }],
                                assignees: [],
                            },
                            {
                                number: 2,
                                title: 'Issue 2',
                                state: 'open',
                                labels: [{ name: 'enhancement' }],
                                assignees: [
                                    {
                                        login: "someone"
                                    },
                                ],
                            },
                        ],
                    }),
                    listEventsForTimeline: jest.fn().mockResolvedValue({
                        data: [
                            {
                                id: 1,
                                event: 'labeled',
                                label: { name: 'bug' },
                                source: {
                                    issue: {
                                        pull_request: "link"
                                    },
                                },
                            },
                            {
                                id: 2,
                                event: 'cross-referenced',
                                source: {
                                    issue: {
                                        pull_request: "link"
                                    },
                                },
                            },
                        ],
                    }),
                    listComments: jest.fn().mockResolvedValue({
                        data: [
                            {
                                id: 101,
                                user: { login: 'user1' },
                                body: 'This is the first comment.',
                                created_at: '2023-01-01T10:00:00Z',
                                updated_at: '2023-01-01T10:00:00Z'
                            },
                            {
                                id: 102,
                                user: { login: 'user2' },
                                body: 'Release notes:\\n- note about change',
                                created_at: '2023-01-02T11:00:00Z',
                                updated_at: '2023-01-02T11:00:00Z'
                            },
                        ],
                    }),
                },
                pulls: {
                    list: jest.fn().mockResolvedValue({
                        data: [
                            {
                                id: 1,
                                title: 'Pull Request 1',
                                state: 'closed',
                                labels: [{ name: 'bug' }],
                            },
                            {
                                id: 2,
                                title: 'Pull Request 2',
                                state: 'open',
                                labels: [{ name: 'enhancement' }],
                            },
                        ],
                    }),
                    listCommits: jest.fn().mockResolvedValue({
                        data: [
                            {
                                commit: {
                                    author: {
                                        name: 'John Doe',
                                        email: 'john.doe@example.com',
                                    },
                                    message: 'Initial commit'
                                },
                                author: {
                                    login: 'johnDoe',
                                },
                                url: 'https://api.github.com/repos/owner/repo/commits/abc123'
                            },
                            {
                                commit: {
                                    author: {
                                        name: 'Jane Smith',
                                        email: 'jane.smith@example.com',
                                    },
                                    message: 'Add new feature'
                                },
                                author: {
                                    login: 'johnDoe',
                                },
                                url: 'https://api.github.com/repos/owner/repo/commits/def456'
                            },
                        ],
                    }),
                    get: jest.fn().mockResolvedValue({
                        data: [
                            {
                                body: 'This is a detailed description of the pull request.',
                            },
                        ],
                    }),
                },
            }
        }));
    });

    /*
        Check if the action fails if the required environment variables are missing.
     */
    it('should fail if GITHUB_TOKEN is missing', async () => {
        delete process.env.GITHUB_TOKEN;

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GitHub token is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if GITHUB_REPOSITORY is missing', async () => {
        delete process.env.GITHUB_REPOSITORY;

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GITHUB_REPOSITORY environment variable is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if GITHUB_REPOSITORY is not in the correct format', async () => {
        process.env.GITHUB_REPOSITORY = 'owner-repo';

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GITHUB_REPOSITORY environment variable is not in the correct format 'owner/repo'.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if tag-name input is missing', async () => {
        // Mock core.getInput to return null for 'tag-name' - here return null only as 'tag-name' is the only required
        core.getInput.mockImplementation((name) => {
            return null;
        });

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("Tag name is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    /*
    Happy path tests - default values.
    */
    it('should run successfully with valid inputs - required defaults only', async () => {
        // Mock core.getInput to return null for all except 'tag-name'
        core.getInput.mockImplementation((name) => {
            switch (name) {
                case 'tag-name':
                    return 'v0.1.0';
                default:
                    return null;
            }
        });

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        // TODO - finish when full data set will be designed
        // expect(firstCallArgs[1]).toBe('expected_output_value');
    });

    it('should run successfully with valid inputs - all defined', async () => {
        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        // TODO - finish when full data set will be designed
        // expect(firstCallArgs[1]).toBe('expected_output_value');
    });

    /*
    Happy path tests - non default options.
    */
    it('should run successfully with valid inputs - hide warning chapters', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - use published at', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - use custom skip label', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - do not print empty chapters', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - no chapters defined', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - empty chapter', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - previous release already exists', async () => {
        // TODO
    });

    /*
    Happy path tests - no option related
    */
    it('should run successfully with valid inputs - no data available', async () => {
        // TODO
    });

    it('should run successfully with valid inputs - co author with public mail', async () => {
        // TODO
    });


    it('should run successfully with valid inputs - co author with non public mail', async () => {
        // TODO
    });
});
