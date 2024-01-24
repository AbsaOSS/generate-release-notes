const { Octokit } = require("@octokit/rest");
const core = require('@actions/core');
const github = require('@actions/github');
const { run } = require('./../scripts/generate-release-notes');
const fs = require('fs');
const path = require('path');
const { mockEmptyData, mockFullPerfectData } = require('./mocks/octokit.mocks');
const { fullDefaultInputs } = require('./mocks/core.mocks');

jest.mock('@octokit/rest');
jest.mock('@actions/core');
jest.mock('@actions/github');

describe('run', () => {
    beforeEach(() => {
        // Reset environment variables and mocks before each test
        process.env.GITHUB_TOKEN = 'fake-token';
        process.env.GITHUB_REPOSITORY = 'owner/repo';

        jest.resetAllMocks();

        github.context.repo = { owner: 'owner', repo: 'repo' };
    });

    /*
        Check if the action fails if the required environment variables are missing.
     */
    it('should fail if GITHUB_TOKEN is missing', async () => {
        console.log('Test started: should fail if GITHUB_TOKEN is missing');
        delete process.env.GITHUB_TOKEN;

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GitHub token is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if GITHUB_REPOSITORY is missing', async () => {
        console.log('Test started: should fail if GITHUB_REPOSITORY is missing');
        delete process.env.GITHUB_REPOSITORY;

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GITHUB_REPOSITORY environment variable is missing.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if GITHUB_REPOSITORY is not in the correct format', async () => {
        console.log('Test started: should fail if GITHUB_REPOSITORY is not in the correct format');
        process.env.GITHUB_REPOSITORY = 'owner-repo';

        await run();

        // Check if core.setFailed was called with the expected message
        expect(core.setFailed).toHaveBeenCalledWith("GITHUB_REPOSITORY environment variable is not in the correct format 'owner/repo'.");

        // Check if core.getInput was called exactly once
        expect(core.getInput).toHaveBeenCalledTimes(1);
        expect(core.getInput).toHaveBeenCalledWith('tag-name');
    });

    it('should fail if tag-name input is missing', async () => {
        console.log('Test started: should fail if tag-name input is missing');

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
    xit('should run successfully with valid inputs - required defaults only', async () => {
        console.log('Test started: should run successfully with valid inputs - required defaults only');

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
        console.log('Test started: should run successfully with valid inputs - all defined');

        core.getInput.mockImplementation((name) => {
            return fullDefaultInputs(name);
        });
        Octokit.mockImplementation(mockFullPerfectData);

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
    xit('should run successfully with valid inputs - hide warning chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - hide warning chapters');

        // TODO
    });

    xit('should run successfully with valid inputs - use published at', async () => {
        console.log('Test started: should run successfully with valid inputs - use published at');

        // TODO
    });

    xit('should run successfully with valid inputs - use custom skip label', async () => {
        console.log('Test started: should run successfully with valid inputs - use custom skip label');

        // TODO
    });

    xit('should run successfully with valid inputs - do not print empty chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - do not print empty chapters');

        // TODO
    });

    xit('should run successfully with valid inputs - no chapters defined', async () => {
        console.log('Test started: should run successfully with valid inputs - no chapters defined');

        // TODO
    });

    xit('should run successfully with valid inputs - empty chapter', async () => {
        console.log('Test started: should run successfully with valid inputs - empty chapter');

        // TODO
    });

    xit('should run successfully with valid inputs - previous release already exists', async () => {
        console.log('Test started: should run successfully with valid inputs - previous release already exists');

        // TODO
    });

    /*
    Happy path tests - no option related
    */
    it('should run successfully with valid inputs - no data available', async () => {
        console.log('Test started: should run successfully with valid inputs - no data available');

        // Define empty data
        core.getInput.mockImplementation((name) => {
            return fullDefaultInputs(name);
        });
        Octokit.mockImplementation(mockEmptyData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_empty_with_all_chapters.txt');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');

        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    xit('should run successfully with valid inputs - no data available - hide empty chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - no data available - hide empty chapters');

        // TODO next
    });

    xit('should run successfully with valid inputs - no data available - hide warning chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - no data available - hide warning chapters');

        // TODO next
    });

    xit('should run successfully with valid inputs - co author with public mail', async () => {
        console.log('Test started: should run successfully with valid inputs - co author with public mail');

        // TODO
    });

    xit('should run successfully with valid inputs - co author with non public mail', async () => {
        console.log('Test started: should run successfully with valid inputs - co author with non public mail');

        // TODO
    });
});
