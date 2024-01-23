jest.mock('@actions/core');
jest.mock('@actions/github');
jest.mock('@octokit/rest');

const core = require('@actions/core');
const github = require('@actions/github');
const { Octokit } = require("@octokit/rest");
const { run } = require("../scripts/generate-release-notes");

jest.mock("@actions/github", () => ({
    context: {
        repo: {
            owner: 'mock-owner',
            repo: 'mock-repo',
        },
    },
}));

jest.mock("@octokit/rest", () => ({
    Octokit: jest.fn().mockImplementation(() => ({
        rest: {
            repos: {
                getLatestRelease: jest.fn().mockResolvedValue({
                    data: {
                        tag_name: 'v1.0.0',
                        published_at: '2023-12-12T09:58:30.000Z',
                        created_at: '2023-12-12T09:56:30.000Z',
                    },
                }),
            },
            issues: {
                listForRepo: jest.fn().mockResolvedValue({
                    data: [
                        {
                            id: 1,
                            title: 'Issue 1',
                            state: 'closed',
                            labels: [{ name: 'bug' }],
                        },
                        {
                            id: 2,
                            title: 'Issue 2',
                            state: 'open',
                            labels: [{ name: 'enhancement' }],
                        },
                    ],
                }),
                listEventsForTimeline: jest.fn().mockResolvedValue({ data: [] }),
                get: jest.fn().mockResolvedValue({ data: {} }),
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
                listCommits: jest.fn().mockResolvedValue({ data: [] }),
                get: jest.fn().mockResolvedValue({ data: {} }),
            },
        },
    })),
}));

describe('Release Notes Scrapper Action Test', () => {
    beforeEach(() => {
        // Reset environment variables and mocks before each test
        delete process.env.GITHUB_TOKEN;
        delete process.env.GITHUB_REPOSITORY;
        jest.resetAllMocks();
        jest.clearAllMocks();

        // Mock core.getInput as needed
        core.getInput.mockImplementation((name) => {
            if (name === 'tag-name') return 'v1.0.0';
            // Add other inputs as required
            return null;
        });

        core.setFailed = jest.fn();
    });

    /*
        Check if the action fails if the required environment variables are missing.
     */

    it('should fail if GITHUB_TOKEN is missing', async () => {
        process.env['GITHUB_REPOSITORY'] = 'mock-owner/mock-repo';

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GitHub token is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if GITHUB_REPOSITORY is missing', async () => {
        process.env['GITHUB_TOKEN'] = 'some-token';

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GITHUB_REPOSITORY environment variable is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if GITHUB_REPOSITORY is not in the correct format', async () => {
        process.env['GITHUB_TOKEN'] = 'some-token';
        process.env['GITHUB_REPOSITORY'] = 'mock-repo'; // Incorrect format, missing owner

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GITHUB_REPOSITORY environment variable is not in the correct format 'owner/repo'.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if tag-name input is missing', async () => {
        process.env['GITHUB_TOKEN'] = 'some-token';
        process.env['GITHUB_REPOSITORY'] = 'mock-owner/mock-repo';

        // Mock core.getInput to return null for 'tag-name'
        core.getInput.mockImplementation((name) => {
            if (name === 'tag-name') return null;
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
    it('should pass with default values', async () => {
        // Set necessary environment variables
        process.env['GITHUB_TOKEN'] = 'some-token';
        process.env['GITHUB_REPOSITORY'] = 'mock-owner/mock-repo';

        // Mock core.getInput to return default values
        core.getInput.mockImplementation((name) => {
            if (name === 'tag-name') return 'v1.0.0';
            if (name === 'chapters') return "[]";
            if (name === 'warnings') return 'true';
            if (name === 'published-at') return 'false';
            if (name === 'skip-release-notes-label') return 'skip-release-notes';
            if (name === 'print-empty-chapters') return 'true';
            return null;
        });

        // Call the run function
        await run();

        // Verify that core.setFailed was not called
        expect(core.setFailed).not.toHaveBeenCalled();

        // Verify that core.getInput was called with the correct arguments
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
        expect(core.getInput).toHaveBeenCalledWith('chapters');
        expect(core.getInput).toHaveBeenCalledWith('warnings');
        expect(core.getInput).toHaveBeenCalledWith('published-at');
        expect(core.getInput).toHaveBeenCalledWith('skip-release-notes-label');
        expect(core.getInput).toHaveBeenCalledWith('print-empty-chapters');

        // Verify that the mocked Octokit instance functions were called with the correct arguments
        // Add necessary expects here
        // TODO add expects for successful run
    });

    /*
        TBD: Add more tests as needed.
     */
});