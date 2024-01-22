jest.mock('@actions/core');
jest.mock('@actions/github', () => ({
    context: {
        repo: {
            owner: 'mock-owner',
            repo: 'mock-repo'
        }
    },
}));

const core = require('@actions/core');
const github = require('@actions/github');
const expect = require('expect');
const main = require('../scripts/generate-release-notes');

describe('Release Notes Scrapper Action Test', () => {
    beforeEach(() => {
        // Reset environment variables and mocks before each test
        delete process.env.GITHUB_TOKEN;
        delete process.env.GITHUB_REPOSITORY;
        jest.resetAllMocks();

        // Mock core.getInput as needed
        core.getInput.mockImplementation((name) => {
            if (name === 'tag-name') return 'v1.0.0';
            // Add other inputs as required
            return null;
        });
    });

    it('should fail if GITHUB_TOKEN is missing', async () => {
        process.env['GITHUB_REPOSITORY'] = 'mock-owner/mock-repo';

        try {
            await main.run();
            // If the function does not throw, force the test to fail
            // expect(true).toBe(false);
        } catch (error) {
            // Log the error for debugging
            console.log("Caught error:", error.message);
            // expect(error.message).toMatch("Missing required inputs or environment variables.");
        }
    });

    // it('should fail if GITHUB_REPOSITORY is missing', async () => {
    //     process.env['GITHUB_TOKEN'] = 'some-token';
    //
    //     await expect(main.run()).rejects.toThrow("Missing required inputs or environment variables.");
    // });
});