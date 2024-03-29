const { Octokit } = require("@octokit/rest");
const core = require('@actions/core');
const github = require('@actions/github');
const { run } = require('./../scripts/generate-release-notes');
const fs = require('fs');
const path = require('path');
const octokitMocks = require('./mocks/octokit.mocks');
const coreMocks = require('./mocks/core.mocks');
const {mockFullPerfectData} = require("./mocks/octokit.mocks");

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
    it('should run successfully with valid inputs - required defaults only', async () => {
        console.log('Test started: should run successfully with valid inputs - required defaults only');

        // Mock core.getInput to return null for all except 'tag-name'
        core.getInput.mockImplementation((name) => {
            switch (name) {
                case 'tag-name':
                    return 'v0.1.1';
                default:
                    return null;
            }
        });
        Octokit.mockImplementation(octokitMocks.mockEmptyData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_empty_with_no_custom_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - all defined', async () => {
        console.log('Test started: should run successfully with valid inputs - all defined');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullDefaultInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockFullPerfectData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_in_default.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    /*
    Happy path tests - non default options.
    */
    it('should run successfully with valid inputs - hide warning chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - hide warning chapters');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullAndHideWarningChaptersInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockFullPerfectData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_hide_warning_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - use custom skip label', async () => {
        console.log('Test started: should run successfully with valid inputs - use custom skip label');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullAndCustomSkipLabel(name);
        });
        Octokit.mockImplementation(octokitMocks.mockFullPerfectData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_custom_skip_label.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - no chapters defined', async () => {
        console.log('Test started: should run successfully with valid inputs - no chapters defined');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullDefaultInputsNoCustomChapters(name);
        });
        Octokit.mockImplementation(octokitMocks.mockFullPerfectData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_no_custom_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - first release', async () => {
        console.log('Test started: should run successfully with valid inputs - first release');

        github.context.repo = { owner: 'owner', repo: 'repo-no-rls' };
        core.getInput.mockImplementation((name) => {
            return coreMocks.fullDefaultInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockFullPerfectData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_first_release.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - second release', async () => {
        console.log('Test started: should run successfully with valid inputs - second release no changes');

        github.context.repo = { owner: 'owner', repo: 'repo-2nd-rls' };
        core.getInput.mockImplementation((name) => {
            return coreMocks.fullDefaultInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockPerfectDataWithoutIssues);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_second_release.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - no PRs in chapter', async () => {
        console.log('Test started: should run successfully with valid inputs - no PRs in chapter');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullAndNoChaptersForPRsInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockFullPerfectData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_fully_populated_no_PRs_in_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');
        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    /*
    Happy path tests - no option related
    */
    it('should run successfully with valid inputs - no data available', async () => {
        console.log('Test started: should run successfully with valid inputs - no data available');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullDefaultInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockEmptyData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_empty_with_all_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');

        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - no data available - hide empty chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - no data available - hide empty chapters');

        // Define empty data
        core.getInput.mockImplementation((name) => {
            return coreMocks.fullAndHideEmptyChaptersInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockEmptyData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_empty_with_hidden_empty_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');

        expect(firstCallArgs[1]).toBe(expectedOutput);
    });

    it('should run successfully with valid inputs - no data available - hide warning chapters', async () => {
        console.log('Test started: should run successfully with valid inputs - no data available - hide warning chapters');

        core.getInput.mockImplementation((name) => {
            return coreMocks.fullAndHideWarningChaptersInputs(name);
        });
        Octokit.mockImplementation(octokitMocks.mockEmptyData);

        await run();

        expect(core.setFailed).not.toHaveBeenCalled();

        // Get the arguments of the first call to setOutput
        const firstCallArgs = core.setOutput.mock.calls[0];
        expect(firstCallArgs[0]).toBe('releaseNotes');

        const filePath = path.join(__dirname, 'data', 'rls_notes_empty_with_hidden_warning_chapters.md');
        let expectedOutput = fs.readFileSync(filePath, 'utf8');

        expect(firstCallArgs[1]).toBe(expectedOutput);
    });
});
