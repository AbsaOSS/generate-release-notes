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

        core.getInput.mockImplementation((name) => {
            if (name === 'tag-name') return 'v1.0.0';
            return null;
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
                        } })
                }
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
    it('should run successfully with valid inputs', async () => {
        await run();

        // Add your assertions here
        // For example, check if core.setFailed was not called
        // expect(core.setFailed).not.toHaveBeenCalled();
    });
});
